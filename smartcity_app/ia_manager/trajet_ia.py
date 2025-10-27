"""
Intelligence Artificielle pour la Planification de Trajets - SmartCity
Module : 🤖 IA Trajets Intelligents avec Cohérence Géographique
"""

import json
import math
import random
from datetime import datetime, timedelta
from django.utils import timezone
from typing import List, Dict, Tuple, Optional
from ..gestion_trajets.models import (
    DemandeTrajetIntelligent, 
    TrajetRecommande, 
    TypeVehiculeIntelligent,
    AlerteTransportTempsReel,
    PreferenceUtilisateurIA
)

# Import du gestionnaire de cohérence géographique
from .geo_coherence import geo_coherence_manager

class MoteurRecommandationTrajet:
    """
    Moteur d'IA pour la recommandation intelligente de trajets
    """
    
    def __init__(self):
        self.facteurs_poids = {
            'rapidite': {'duree': 0.8, 'circulation': 0.6, 'retard': 0.7},
            'economique': {'cout': 0.9, 'cout_carburant': 0.8, 'cout_parking': 0.7},
            'ecologique': {'empreinte_carbone': 0.9, 'transport_public': 0.7},
            'confort': {'confort_vehicule': 0.8, 'nb_correspondances': 0.6, 'marche': 0.5},
            'moins_circulation': {'circulation': 0.9, 'routes_secondaires': 0.7}
        }
        
        self.poids_vehicules = {
            'public': {'cout': 0.2, 'ecologie': 0.8, 'confort': 0.6},
            'prive': {'cout': 0.8, 'ecologie': 0.3, 'confort': 0.9},
            'partage': {'cout': 0.4, 'ecologie': 0.7, 'confort': 0.7},
            'actif': {'cout': 0.1, 'ecologie': 0.9, 'confort': 0.4}
        }
    
    def analyser_demande(self, demande: DemandeTrajetIntelligent) -> Dict:
        """
        Analyse une demande de trajet et génère des recommandations intelligentes
        """
        try:
            # 1. Analyser le contexte
            contexte = self._analyser_contexte(demande)
            
            # 2. Récupérer les préférences utilisateur
            preferences = self._obtenir_preferences_utilisateur(demande.utilisateur)
            
            # 3. Analyser les conditions en temps réel
            conditions_temps_reel = self._analyser_conditions_temps_reel(demande)
            
            # 4. Générer les options de trajet
            options_trajet = self._generer_options_trajet(demande, contexte, conditions_temps_reel)
            
            # 5. Calculer les scores et classer
            trajets_scores = self._calculer_scores_trajets(options_trajet, demande, preferences)
            
            # 6. Sélectionner les meilleurs trajets
            trajets_recommandes = self._selectionner_meilleurs_trajets(trajets_scores)
            
            # 7. Enrichir avec des informations temps réel
            trajets_enrichis = self._enrichir_trajets_temps_reel(trajets_recommandes, conditions_temps_reel)
            
            return {
                'statut': 'success',
                'trajets_recommandes': trajets_enrichis,
                'contexte': contexte,
                'conditions_temps_reel': conditions_temps_reel,
                'nb_options_analysees': len(options_trajet),
                'timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            return {
                'statut': 'error',
                'erreur': str(e),
                'timestamp': timezone.now().isoformat()
            }
    
    def _analyser_contexte(self, demande: DemandeTrajetIntelligent) -> Dict:
        """Analyse le contexte de la demande"""
        maintenant = timezone.now()
        heure_depart = demande.heure_depart_souhaitee or maintenant
        
        # Analyser l'heure
        heure = heure_depart.hour
        jour_semaine = heure_depart.weekday()  # 0=lundi, 6=dimanche
        
        contexte = {
            'periode_journee': self._determiner_periode_journee(heure),
            'type_jour': 'semaine' if jour_semaine < 5 else 'weekend',
            'heure_pointe': self._est_heure_pointe(heure, jour_semaine),
            'saison': self._determiner_saison(maintenant),
            'meteo_prevue': self._obtenir_meteo(heure_depart),
            'evenements_ville': self._obtenir_evenements(heure_depart)
        }
        
        return contexte
    
    def _analyser_conditions_temps_reel(self, demande: DemandeTrajetIntelligent) -> Dict:
        """Analyse les conditions de circulation et transport en temps réel"""
        
        # Simuler les données temps réel (en production, cela viendrait d'APIs réelles)
        niveau_circulation = random.choice(['faible', 'moyen', 'fort'])
        
        alertes_actives = list(AlerteTransportTempsReel.objects.filter(
            active=True,
            date_debut__lte=timezone.now(),
        ).values('type_alerte', 'titre', 'description', 'severite'))
        
        conditions = {
            'circulation_generale': niveau_circulation,
            'indice_circulation': random.randint(3, 8),  # 1-10
            'alertes_transport': alertes_actives,
            'retards_moyens': {
                'bus': random.randint(0, 10),
                'metro': random.randint(0, 5),
                'tram': random.randint(0, 7)
            },
            'disponibilite_vehicules': {
                'velo_partage': random.randint(60, 95),  # % disponibilité
                'voiture_partage': random.randint(40, 80),
                'trottinette': random.randint(50, 90)
            },
            'conditions_meteo': {
                'temperature': random.randint(5, 25),
                'precipitation': random.choice(['none', 'light', 'moderate']),
                'vent': random.randint(0, 20)
            }
        }
        
        return conditions
    
    def _generer_options_trajet(self, demande: DemandeTrajetIntelligent, contexte: Dict, conditions: Dict) -> List[Dict]:
        """Génère toutes les options de trajet possibles avec cohérence géographique"""
        options = []
        
        # **NOUVEAUTÉ** : Calculer la distance réelle entre départ et arrivée
        depart_coords = (demande.lieu_depart_lat, demande.lieu_depart_lng) if demande.lieu_depart_lat and demande.lieu_depart_lng else None
        arrivee_coords = (demande.lieu_arrivee_lat, demande.lieu_arrivee_lng) if demande.lieu_arrivee_lat and demande.lieu_arrivee_lng else None
        
        # Si pas de coordonnées, essayer de les déduire des noms de lieux
        if not depart_coords and demande.lieu_depart:
            depart_coords = geo_coherence_manager.obtenir_coordonnees_ville(demande.lieu_depart)
        
        if not arrivee_coords and demande.lieu_arrivee:
            arrivee_coords = geo_coherence_manager.obtenir_coordonnees_ville(demande.lieu_arrivee)
        
        # Calculer la distance réelle
        distance_reelle = None
        if depart_coords and arrivee_coords:
            distance_reelle = geo_coherence_manager.calculer_distance_reelle(depart_coords, arrivee_coords)
        
        # Si pas de distance réelle, utiliser une estimation (fallback)
        if distance_reelle is None:
            distance_reelle = random.uniform(5, 25)  # km (estimation par défaut)
        
        # **NOUVEAUTÉ** : Obtenir les informations de zone
        zone_info = geo_coherence_manager.obtenir_info_zone(distance_reelle)
        
        # Récupérer les véhicules disponibles
        vehicules_disponibles = TypeVehiculeIntelligent.objects.filter(disponible=True)
        
        if demande.vehicules_preferes.exists():
            vehicules_prioritaires = demande.vehicules_preferes.all()
        else:
            vehicules_prioritaires = vehicules_disponibles
        
        # Générer des options pour chaque type de véhicule
        options_brutes = []
        for vehicule in vehicules_prioritaires:
            option = self._calculer_trajet_vehicule(
                demande, vehicule, contexte, conditions, distance_reelle
            )
            if option:
                options_brutes.append(option)
        
        # **NOUVEAUTÉ** : Filtrer avec cohérence géographique
        if depart_coords and arrivee_coords:
            options_coherentes = geo_coherence_manager.filtrer_vehicules_coherents(
                options_brutes,
                distance_reelle,
                depart_coords,
                arrivee_coords
            )
            
            # Ajouter des informations contextuelles
            for option in options_coherentes:
                option['zone_geographique'] = zone_info['nom']
                option['distance_reelle_km'] = distance_reelle
        else:
            # Fallback si pas de coordonnées : garder tous mais signaler
            options_coherentes = options_brutes
            for option in options_coherentes:
                option['coherence_geo'] = {
                    'est_adapte': True,
                    'raison': 'Coordonnées non disponibles - vérification impossible',
                    'zone': 'inconnue',
                    'explication': '⚠️ Recommandation sans vérification géographique'
                }
                option['zone_geographique'] = 'Non déterminée'
                option['distance_reelle_km'] = distance_reelle
        
        # Générer des options combinées (multimodal) uniquement si pertinent
        if distance_reelle and 5 < distance_reelle < 30:  # Multimodal pertinent pour 5-30km
            options_multimodales = self._generer_trajets_multimodaux(demande, contexte, conditions, distance_reelle)
            options_coherentes.extend(options_multimodales)
        
        return options_coherentes
    
    def _calculer_trajet_vehicule(self, demande: DemandeTrajetIntelligent, vehicule: TypeVehiculeIntelligent, 
                                 contexte: Dict, conditions: Dict, distance_reelle: Optional[float] = None) -> Optional[Dict]:
        """Calcule un trajet pour un véhicule spécifique"""
        
        # Utiliser la distance fournie ou la calculer
        if distance_reelle is not None:
            distance = distance_reelle
        else:
            # Calculer la distance (simulation - en production utiliserait une API de routing)
            distance = self._calculer_distance(
                demande.lieu_depart_lat, demande.lieu_depart_lng,
                demande.lieu_arrivee_lat, demande.lieu_arrivee_lng
            )
            
            if distance is None:
                distance = random.uniform(5, 25)  # km
        
        # Calculer les métriques selon le type de véhicule
        if vehicule.categorie == 'public':
            duree, cout, confort = self._calculer_metriques_transport_public(
                distance, vehicule, contexte, conditions
            )
        elif vehicule.categorie == 'prive':
            duree, cout, confort = self._calculer_metriques_transport_prive(
                distance, vehicule, contexte, conditions
            )
        elif vehicule.categorie == 'partage':
            duree, cout, confort = self._calculer_metriques_transport_partage(
                distance, vehicule, contexte, conditions
            )
        else:  # actif
            duree, cout, confort = self._calculer_metriques_transport_actif(
                distance, vehicule, contexte, conditions
            )
        
        # Calculer l'empreinte carbone
        empreinte_carbone = distance * vehicule.empreinte_carbone
        
        # Analyser la circulation spécifique
        facteur_circulation = self._calculer_facteur_circulation(vehicule, conditions)
        duree *= facteur_circulation
        
        return {
            'vehicule_id': vehicule.id,
            'vehicule_nom': vehicule.nom,
            'vehicule_type': vehicule.categorie,
            'distance_km': round(distance, 2),
            'duree_minutes': int(duree),
            'cout_euros': round(cout, 2),
            'empreinte_carbone_g': round(empreinte_carbone, 1),
            'score_confort': confort,
            'facteur_circulation': facteur_circulation,
            'etapes': self._generer_etapes_trajet(demande, vehicule, distance),
            'fiabilite': self._calculer_fiabilite(vehicule, conditions),
            'horaires_temps_reel': self._obtenir_horaires_temps_reel(vehicule)
        }
    
    def _calculer_metriques_transport_public(self, distance: float, vehicule: TypeVehiculeIntelligent, 
                                           contexte: Dict, conditions: Dict) -> Tuple[float, float, int]:
        """Calcule durée, coût, confort pour transport public"""
        
        # Durée de base + temps d'attente + correspondances
        duree_base = (distance / vehicule.vitesse_moyenne) * 60  # minutes
        temps_attente = vehicule.frequence_passage / 2 if vehicule.frequence_passage else 8
        temps_correspondances = random.randint(5, 15) if distance > 10 else 0
        duree_totale = duree_base + temps_attente + temps_correspondances
        
        # Coût fixe pour transport public
        cout = 1.5 if distance < 10 else 2.5
        
        # Confort dépend de l'affluence
        confort_base = 7
        if contexte.get('heure_pointe', False):
            confort_base -= 2
        
        return duree_totale, cout, max(1, confort_base)
    
    def _calculer_metriques_transport_prive(self, distance: float, vehicule: TypeVehiculeIntelligent,
                                          contexte: Dict, conditions: Dict) -> Tuple[float, float, int]:
        """Calcule durée, coût, confort pour transport privé"""
        
        duree = (distance / vehicule.vitesse_moyenne) * 60
        
        # Coût carburant + parking
        cout_carburant = distance * vehicule.cout_par_km
        cout_parking = 2.0 if distance > 5 else 0
        cout_total = cout_carburant + cout_parking
        
        confort = 9  # Très confortable
        
        return duree, cout_total, confort
    
    def _calculer_metriques_transport_partage(self, distance: float, vehicule: TypeVehiculeIntelligent,
                                            contexte: Dict, conditions: Dict) -> Tuple[float, float, int]:
        """Calcule durée, coût, confort pour transport partagé"""
        
        duree = (distance / vehicule.vitesse_moyenne) * 60
        
        # Coût par distance pour véhicule partagé
        cout = distance * vehicule.cout_par_km
        
        confort = 6  # Confort moyen
        
        return duree, cout, confort
    
    def _calculer_metriques_transport_actif(self, distance: float, vehicule: TypeVehiculeIntelligent,
                                          contexte: Dict, conditions: Dict) -> Tuple[float, float, int]:
        """Calcule durée, coût, confort pour transport actif"""
        
        duree = (distance / vehicule.vitesse_moyenne) * 60
        
        cout = 0  # Gratuit
        
        # Confort dépend de la météo
        confort = 8
        if conditions['conditions_meteo']['precipitation'] != 'none':
            confort -= 3
        if conditions['conditions_meteo']['temperature'] < 5 or conditions['conditions_meteo']['temperature'] > 30:
            confort -= 2
            
        return duree, max(cout, 0), max(1, confort)
    
    def _calculer_scores_trajets(self, options: List[Dict], demande: DemandeTrajetIntelligent, 
                               preferences: Dict) -> List[Dict]:
        """Calcule les scores pour chaque option de trajet"""
        
        for option in options:
            score = 0
            facteurs = []
            
            priorite = demande.priorite
            poids_priorite = self.facteurs_poids.get(priorite, {})
            
            # Score basé sur la priorité principale
            if priorite == 'rapidite':
                score_duree = max(0, 10 - (option['duree_minutes'] / 10))
                score += score_duree * poids_priorite.get('duree', 0.8)
                facteurs.append(f"Rapidité: {score_duree:.1f}")
                
            elif priorite == 'economique':
                score_cout = max(0, 10 - option['cout_euros'])
                score += score_cout * poids_priorite.get('cout', 0.9)
                facteurs.append(f"Économie: {score_cout:.1f}")
                
            elif priorite == 'ecologique':
                score_eco = max(0, 10 - (option['empreinte_carbone_g'] / 100))
                score += score_eco * poids_priorite.get('empreinte_carbone', 0.9)
                facteurs.append(f"Écologie: {score_eco:.1f}")
                
            elif priorite == 'confort':
                score += option['score_confort'] * poids_priorite.get('confort_vehicule', 0.8)
                facteurs.append(f"Confort: {option['score_confort']}")
            
            # Bonus/malus selon les contraintes
            if demande.budget_maximum and option['cout_euros'] > demande.budget_maximum:
                score *= 0.5  # Pénalité importante si dépasse le budget
                
            if demande.duree_maximum and option['duree_minutes'] > demande.duree_maximum:
                score *= 0.7  # Pénalité si dépasse la durée
            
            # Bonus préférences véhicule
            if demande.vehicules_preferes.filter(id=option['vehicule_id']).exists():
                score += 1
                facteurs.append("Véhicule préféré: +1")
            
            option['score_ia'] = round(score, 2)
            option['facteurs_decision'] = facteurs
        
        return sorted(options, key=lambda x: x['score_ia'], reverse=True)
    
    def _selectionner_meilleurs_trajets(self, trajets_scores: List[Dict], nb_max: int = 3) -> List[Dict]:
        """Sélectionne les meilleurs trajets à recommander"""
        return trajets_scores[:nb_max]
    
    def _enrichir_trajets_temps_reel(self, trajets: List[Dict], conditions: Dict) -> List[Dict]:
        """Enrichit les trajets avec des informations temps réel"""
        
        for i, trajet in enumerate(trajets):
            # Ajouter des informations temps réel
            trajet.update({
                'rang': i + 1,
                'retard_estime': conditions['retards_moyens'].get(trajet['vehicule_type'], 0),
                'circulation_niveau': conditions['circulation_generale'],
                'alertes_actives': [a for a in conditions['alertes_transport'] 
                                  if a.get('vehicule_type') == trajet['vehicule_type']],
                'recommandation_ia': self._generer_recommandation_textuelle(trajet, conditions),
                'prochains_departs': self._generer_prochains_horaires(trajet)
            })
        
        return trajets
    
    # Méthodes utilitaires
    
    def _calculer_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> Optional[float]:
        """Calcule la distance entre deux points géographiques"""
        if not all([lat1, lon1, lat2, lon2]):
            return None
            
        # Formule de Haversine
        R = 6371  # Rayon de la Terre en km
        
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat/2) * math.sin(dlat/2) + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dlon/2) * math.sin(dlon/2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        
        return distance
    
    def _determiner_periode_journee(self, heure: int) -> str:
        """Détermine la période de la journée"""
        if 6 <= heure < 12:
            return 'matin'
        elif 12 <= heure < 18:
            return 'apres_midi'
        elif 18 <= heure < 22:
            return 'soir'
        else:
            return 'nuit'
    
    def _est_heure_pointe(self, heure: int, jour_semaine: int) -> bool:
        """Détermine si c'est une heure de pointe"""
        if jour_semaine >= 5:  # Weekend
            return False
        return (7 <= heure <= 9) or (17 <= heure <= 19)
    
    def _generer_recommandation_textuelle(self, trajet: Dict, conditions: Dict) -> str:
        """Génère une recommandation textuelle pour le trajet"""
        vehicule = trajet['vehicule_nom']
        duree = trajet['duree_minutes']
        cout = trajet['cout_euros']
        
        recommandations = [
            f"🚗 {vehicule} - {duree}min, {cout}€",
        ]
        
        if trajet['score_confort'] >= 8:
            recommandations.append("💺 Très confortable")
        
        if trajet['empreinte_carbone_g'] < 50:
            recommandations.append("🌱 Écologique")
            
        if trajet['cout_euros'] < 2:
            recommandations.append("💰 Économique")
        
        if conditions['circulation_generale'] == 'faible':
            recommandations.append("🟢 Circulation fluide")
        elif conditions['circulation_generale'] == 'fort':
            recommandations.append("🔴 Attention circulation dense")
        
        return " | ".join(recommandations)
    
    def _obtenir_preferences_utilisateur(self, user) -> Dict:
        """Récupère les préférences de l'utilisateur"""
        try:
            preferences = PreferenceUtilisateurIA.objects.get(utilisateur=user)
            return {
                'vehicules_favoris': list(preferences.vehicules_favoris.values_list('id', flat=True)),
                'vehicules_evites': list(preferences.vehicules_evites.values_list('id', flat=True)),
                'priorite_defaut': preferences.priorite_defaut,
                'budget_defaut': preferences.budget_defaut,
                'necessite_pmr': preferences.necessite_pmr,
            }
        except PreferenceUtilisateurIA.DoesNotExist:
            return {'vehicules_favoris': [], 'vehicules_evites': []}
    
    def _generer_trajets_multimodaux(self, demande: DemandeTrajetIntelligent, contexte: Dict, 
                                    conditions: Dict, distance_reelle: float) -> List[Dict]:
        """Génère des options de trajets multimodaux (combinaison de véhicules)"""
        # Simulation simple - en production cela serait plus complexe
        options_multimodales = []
        
        # Exemple: Vélo + Métro
        if random.choice([True, False]):
            # Calculer un score IA simple pour ce trajet
            duree_mins = random.randint(25, 45)
            cout = random.uniform(1.5, 3.0)
            confort = random.randint(6, 8)
            distance = distance_reelle  # Utiliser la distance réelle
            empreinte = random.uniform(20, 50)
            
            # Score simple basé sur les critères
            score_ia = (10 - duree_mins/6) + (10 - cout*2) + confort + (10 - empreinte/10)
            
            option = {
                'vehicule_id': None,  # Pas d'ID spécifique pour multimodal
                'vehicule_nom': 'Vélo + Métro',
                'vehicule_type': 'multimodal',
                'distance_km': distance,
                'duree_minutes': duree_mins,
                'cout_euros': cout,
                'empreinte_carbone_g': empreinte,
                'score_confort': confort,
                'facteur_circulation': 0.9,
                'etapes': ['5min à vélo', 'Métro ligne 1', '3min à pied'],
                'fiabilite': 8.5,
                'horaires_temps_reel': {},
                'score_ia': score_ia,
                'circulation_niveau': 'moyen',
                'retard_estime': random.randint(0, 5),
                'alertes_actives': [],
                'facteurs_decision': ['Combinaison efficace', 'Évite les embouteillages', 'Eco-responsable']
            }
            options_multimodales.append(option)
        
        return options_multimodales
    
    def _generer_etapes_trajet(self, demande, vehicule, distance) -> List[str]:
        """Génère les étapes du trajet"""
        if vehicule.categorie == 'public':
            return [
                f"Marche vers l'arrêt (3min)",
                f"{vehicule.nom} jusqu'à destination",
                f"Marche finale (2min)"
            ]
        else:
            return [f"Trajet direct en {vehicule.nom}"]
    
    def _calculer_fiabilite(self, vehicule, conditions) -> float:
        """Calcule le score de fiabilité"""
        base = 8.0
        if vehicule.categorie == 'public':
            base -= conditions['retards_moyens'].get(vehicule.nom.lower(), 0) * 0.2
        return max(1.0, base)
    
    def _obtenir_horaires_temps_reel(self, vehicule) -> Dict:
        """Simule les horaires temps réel"""
        if vehicule.categorie == 'public':
            prochains = []
            for i in range(3):
                temps = 5 + i * (vehicule.frequence_passage or 10)
                prochains.append(f"{temps}min")
            return {'prochains_passages': prochains}
        return {}
    
    def _generer_prochains_horaires(self, trajet) -> List[str]:
        """Génère les prochains horaires de départ"""
        horaires = []
        maintenant = timezone.now()
        
        for i in range(3):
            heure_depart = maintenant + timedelta(minutes=5 + i * 10)
            horaires.append(heure_depart.strftime("%H:%M"))
            
        return horaires
    
    # Méthodes de simulation (en production seraient des appels API)
    
    def _determiner_saison(self, date) -> str:
        month = date.month
        if month in [12, 1, 2]:
            return 'hiver'
        elif month in [3, 4, 5]:
            return 'printemps'
        elif month in [6, 7, 8]:
            return 'ete'
        else:
            return 'automne'
    
    def _obtenir_meteo(self, date) -> Dict:
        return {
            'temperature': random.randint(5, 25),
            'precipitation': random.choice(['none', 'light', 'moderate']),
            'vent': random.randint(0, 20)
        }
    
    def _obtenir_evenements(self, date) -> List[Dict]:
        return []  # Simulation vide
    
    def _calculer_facteur_circulation(self, vehicule, conditions) -> float:
        """Calcule le facteur d'impact de la circulation"""
        if vehicule.categorie == 'public':
            return 1.1 if conditions['circulation_generale'] == 'fort' else 1.0
        elif vehicule.categorie == 'prive':
            if conditions['circulation_generale'] == 'fort':
                return 1.5
            elif conditions['circulation_generale'] == 'moyen':
                return 1.2
            else:
                return 1.0
        else:
            return 1.0  # Transport actif non impacté


# Instance globale du moteur
moteur_trajet_ia = MoteurRecommandationTrajet()