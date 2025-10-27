"""
Moteur IA pour la Gestion de Location - SmartCity
Module : 🚗 Intelligence Artificielle pour Recommandations de Location
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from django.utils import timezone
from django.contrib.auth.models import User

from ..gestion_location.models import (
    TypeLocation,
    VehiculeLocation,
    ReservationLocation,
    OptionLocation,
    ServiceLocation,
    HistoriqueLocation
)
from ..gestion_utilisateurs.models import ProfilUtilisateur

logger = logging.getLogger(__name__)


class LocationIAEngine:
    """
    Moteur d'Intelligence Artificielle pour les recommandations de location
    """
    
    def __init__(self):
        self.logger = logger
        self.poids_criteres = {
            'prix': 0.25,
            'confort': 0.20,
            'ecologie': 0.20,
            'disponibilite': 0.15,
            'proximite': 0.10,
            'preferences_utilisateur': 0.10
        }
    
    def analyser_demande_location(self, demande_data: Dict) -> Dict:
        """
        Analyse une demande de location et génère des recommandations intelligentes
        
        Args:
            demande_data: Dictionnaire avec les données de la demande
                - lieu_prise, lieu_retour, date_debut, date_fin
                - conducteur_principal, nombre_passagers, bagages
                - budget_max, preferences_ecologiques, niveau_confort
        
        Returns:
            Dictionnaire avec les recommandations et scores
        """
        try:
            self.logger.info("🔍 Analyse de la demande de location IA")
            
            # Extraire les paramètres
            lieu_prise = demande_data.get('lieu_prise', '')
            lieu_retour = demande_data.get('lieu_retour', '')
            date_debut = demande_data.get('date_debut')
            date_fin = demande_data.get('date_fin')
            nombre_passagers = demande_data.get('nombre_passagers', 1)
            bagages = demande_data.get('bagages', 0)
            budget_max = demande_data.get('budget_max', 100)
            preferences_ecologiques = demande_data.get('preferences_ecologiques', False)
            niveau_confort = demande_data.get('niveau_confort', 'moyen')
            
            # Calculer la durée
            if date_debut and date_fin:
                duree_heures = self._calculer_duree(date_debut, date_fin)
            else:
                duree_heures = 24  # Par défaut
            
            # Analyser le contexte
            contexte = self._analyser_contexte_location(date_debut, lieu_prise, lieu_retour)
            
            # Récupérer les véhicules disponibles
            vehicules_disponibles = self._recuperer_vehicules_disponibles(
                date_debut, date_fin, nombre_passagers, bagages
            )
            
            # Calculer les scores pour chaque véhicule
            recommandations = []
            for vehicule in vehicules_disponibles:
                score = self._calculer_score_vehicule(
                    vehicule, demande_data, contexte, duree_heures
                )
                
                if score['score_total'] > 0.3:  # Seuil minimum
                    recommandations.append({
                        'vehicule': vehicule,
                        'score': score,
                        'prix_estime': self._calculer_prix_estime(vehicule, duree_heures),
                        'recommandation_ia': self._generer_recommandation_textuelle(score, vehicule, contexte)
                    })
            
            # Trier par score décroissant
            recommandations.sort(key=lambda x: x['score']['score_total'], reverse=True)
            
            # Générer des insights IA
            insights = self._generer_insights_ia(recommandations, contexte, demande_data)
            
            resultat = {
                'recommandations': recommandations[:5],  # Top 5
                'insights_ia': insights,
                'contexte': contexte,
                'statistiques': {
                    'nombre_vehicules_analyses': len(vehicules_disponibles),
                    'nombre_recommandations': len(recommandations),
                    'duree_analyse': duree_heures,
                    'budget_recommandé': self._calculer_budget_optimal(recommandations)
                }
            }
            
            self.logger.info(f"✅ Analyse IA terminée: {len(recommandations)} recommandations générées")
            return resultat
            
        except Exception as e:
            self.logger.error(f"❌ Erreur lors de l'analyse IA: {e}")
            return {'erreur': str(e), 'recommandations': []}
    
    def _analyser_contexte_location(self, date_debut, lieu_prise: str, lieu_retour: str) -> Dict:
        """Analyse le contexte de la location"""
        contexte = {
            'periode_journee': 'jour',
            'type_jour': 'semaine',
            'saison': 'printemps',
            'meteo': 'normale',
            'trafic': 'modere',
            'evenements': [],
            'zone_geographique': 'urbaine'
        }
        
        if date_debut:
            # Analyser la période de la journée
            heure = date_debut.hour
            if 6 <= heure < 12:
                contexte['periode_journee'] = 'matin'
            elif 12 <= heure < 18:
                contexte['periode_journee'] = 'apres_midi'
            elif 18 <= heure < 22:
                contexte['periode_journee'] = 'soir'
            else:
                contexte['periode_journee'] = 'nuit'
            
            # Analyser le type de jour
            if date_debut.weekday() >= 5:  # Weekend
                contexte['type_jour'] = 'weekend'
            
            # Analyser la saison
            mois = date_debut.month
            if mois in [12, 1, 2]:
                contexte['saison'] = 'hiver'
            elif mois in [3, 4, 5]:
                contexte['saison'] = 'printemps'
            elif mois in [6, 7, 8]:
                contexte['saison'] = 'ete'
            else:
                contexte['saison'] = 'automne'
        
        # Analyser la zone géographique
        if 'centre' in lieu_prise.lower() or 'ville' in lieu_prise.lower():
            contexte['zone_geographique'] = 'urbaine'
        elif 'aeroport' in lieu_prise.lower() or 'gare' in lieu_prise.lower():
            contexte['zone_geographique'] = 'transport'
        else:
            contexte['zone_geographique'] = 'periurbaine'
        
        # Simuler les conditions de trafic
        if contexte['periode_journee'] in ['matin', 'soir'] and contexte['type_jour'] == 'semaine':
            contexte['trafic'] = 'fort'
        elif contexte['periode_journee'] == 'nuit':
            contexte['trafic'] = 'faible'
        
        return contexte
    
    def _recuperer_vehicules_disponibles(self, date_debut, date_fin, nombre_passagers: int, bagages: int) -> List:
        """Récupère les véhicules disponibles selon les critères"""
        try:
            # Véhicules disponibles
            vehicules_query = VehiculeLocation.objects.filter(statut='disponible')
            
            # Filtrer par capacité
            vehicules_query = vehicules_query.filter(
                type_location__capacite_passagers__gte=nombre_passagers,
                type_location__capacite_bagages__gte=bagages
            )
            
            # Vérifier la disponibilité pour la période
            if date_debut and date_fin:
                vehicules_disponibles = []
                for vehicule in vehicules_query:
                    if self._verifier_disponibilite_periode(vehicule, date_debut, date_fin):
                        vehicules_disponibles.append(vehicule)
                return vehicules_disponibles
            
            return list(vehicules_query)
            
        except Exception as e:
            self.logger.error(f"Erreur récupération véhicules: {e}")
            return []
    
    def _verifier_disponibilite_periode(self, vehicule, date_debut, date_fin) -> bool:
        """Vérifie la disponibilité d'un véhicule pour une période donnée"""
        conflits = ReservationLocation.objects.filter(
            vehicule=vehicule,
            statut__in=['en_attente', 'confirmee', 'en_cours'],
            date_debut__lt=date_fin,
            date_fin__gt=date_debut
        )
        return not conflits.exists()
    
    def _calculer_score_vehicule(self, vehicule, demande_data: Dict, contexte: Dict, duree_heures: float) -> Dict:
        """Calcule le score IA pour un véhicule"""
        scores = {}
        
        # Score prix (0-1, plus bas = mieux)
        prix_estime = self._calculer_prix_estime(vehicule, duree_heures)
        budget_max = demande_data.get('budget_max', 100)
        scores['prix'] = max(0, 1 - (prix_estime / budget_max))
        
        # Score confort
        scores['confort'] = self._calculer_score_confort(vehicule, demande_data)
        
        # Score écologie
        scores['ecologie'] = self._calculer_score_ecologie(vehicule, demande_data)
        
        # Score disponibilité
        scores['disponibilite'] = self._calculer_score_disponibilite(vehicule, contexte)
        
        # Score proximité
        scores['proximite'] = self._calculer_score_proximite(vehicule, demande_data)
        
        # Score préférences utilisateur
        scores['preferences_utilisateur'] = self._calculer_score_preferences(vehicule, demande_data)
        
        # Score total pondéré
        score_total = sum(
            scores[criteres] * poids 
            for criteres, poids in self.poids_criteres.items()
        )
        
        return {
            'score_total': score_total,
            'scores_detail': scores,
            'poids_appliques': self.poids_criteres
        }
    
    def _calculer_score_confort(self, vehicule, demande_data: Dict) -> float:
        """Calcule le score de confort (0-1)"""
        score = 0.5  # Base
        
        # Capacité passagers
        nombre_passagers = demande_data.get('nombre_passagers', 1)
        if vehicule.type_location.capacite_passagers >= nombre_passagers + 1:
            score += 0.2  # Bonus pour espace supplémentaire
        
        # Capacité bagages
        bagages = demande_data.get('bagages', 0)
        if vehicule.type_location.capacite_bagages >= bagages:
            score += 0.2
        
        # Accessibilité PMR
        if vehicule.type_location.accessible_pmr:
            score += 0.1
        
        # Équipements
        if vehicule.type_location.equipements:
            score += 0.1
        
        return min(1.0, score)
    
    def _calculer_score_ecologie(self, vehicule, demande_data: Dict) -> float:
        """Calcule le score écologique (0-1)"""
        preferences_ecologiques = demande_data.get('preferences_ecologiques', False)
        
        # Score de base selon les émissions
        emission_co2 = vehicule.type_location.emission_co2_par_km
        
        if emission_co2 < 50:  # Véhicule électrique
            score_ecologie = 1.0
        elif emission_co2 < 100:  # Véhicule hybride
            score_ecologie = 0.8
        elif emission_co2 < 150:  # Véhicule économique
            score_ecologie = 0.6
        else:  # Véhicule standard
            score_ecologie = 0.4
        
        # Bonus si l'utilisateur privilégie l'écologie
        if preferences_ecologiques and score_ecologie > 0.7:
            score_ecologie = min(1.0, score_ecologie + 0.2)
        
        return score_ecologie
    
    def _calculer_score_disponibilite(self, vehicule, contexte: Dict) -> float:
        """Calcule le score de disponibilité (0-1)"""
        score = 0.8  # Base
        
        # Bonus si le véhicule est proche
        if vehicule.statut == 'disponible':
            score += 0.2
        
        # Malus selon le contexte de trafic
        if contexte['trafic'] == 'fort':
            score -= 0.1
        
        return max(0.0, min(1.0, score))
    
    def _calculer_score_proximite(self, vehicule, demande_data: Dict) -> float:
        """Calcule le score de proximité (0-1)"""
        # Simulation basée sur la station
        lieu_prise = demande_data.get('lieu_prise', '').lower()
        station = vehicule.station_location.lower()
        
        if 'centre' in lieu_prise and 'centre' in station:
            return 1.0
        elif 'aeroport' in lieu_prise and 'aeroport' in station:
            return 1.0
        elif 'gare' in lieu_prise and 'gare' in station:
            return 1.0
        else:
            return 0.6  # Score moyen par défaut
    
    def _calculer_score_preferences(self, vehicule, demande_data: Dict) -> float:
        """Calcule le score selon les préférences utilisateur"""
        score = 0.5  # Base
        
        # Préférences de catégorie
        categorie_preferee = demande_data.get('categorie_preferee', '')
        if categorie_preferee and categorie_preferee == vehicule.type_location.categorie:
            score += 0.3
        
        # Niveau de confort demandé
        niveau_confort = demande_data.get('niveau_confort', 'moyen')
        if niveau_confort == 'eleve' and vehicule.type_location.categorie == 'luxe':
            score += 0.2
        elif niveau_confort == 'bas' and vehicule.type_location.categorie in ['velo', 'trottinette']:
            score += 0.2
        
        return min(1.0, score)
    
    def _calculer_prix_estime(self, vehicule, duree_heures: float) -> float:
        """Calcule le prix estimé pour une location"""
        prix_base = float(vehicule.type_location.prix_heure) * duree_heures
        
        # Appliquer des coefficients selon la durée
        if duree_heures >= 24:  # Location longue durée
            prix_base *= 0.9  # 10% de réduction
        elif duree_heures >= 48:  # Location très longue durée
            prix_base *= 0.85  # 15% de réduction
        
        return prix_base
    
    def _calculer_duree(self, date_debut, date_fin) -> float:
        """Calcule la durée en heures entre deux dates"""
        if isinstance(date_debut, str):
            date_debut = datetime.fromisoformat(date_debut.replace('T', ' '))
        if isinstance(date_fin, str):
            date_fin = datetime.fromisoformat(date_fin.replace('T', ' '))
        
        delta = date_fin - date_debut
        return delta.total_seconds() / 3600
    
    def _generer_recommandation_textuelle(self, score: Dict, vehicule, contexte: Dict) -> str:
        """Génère une recommandation textuelle personnalisée"""
        score_total = score['score_total']
        scores_detail = score['scores_detail']
        
        if score_total >= 0.8:
            niveau = "excellente"
        elif score_total >= 0.6:
            niveau = "très bonne"
        elif score_total >= 0.4:
            niveau = "bonne"
        else:
            niveau = "correcte"
        
        # Identifier les points forts
        points_forts = []
        if scores_detail['prix'] > 0.7:
            points_forts.append("prix attractif")
        if scores_detail['confort'] > 0.7:
            points_forts.append("confort élevé")
        if scores_detail['ecologie'] > 0.7:
            points_forts.append("respectueux de l'environnement")
        if scores_detail['disponibilite'] > 0.7:
            points_forts.append("excellente disponibilité")
        
        # Générer la recommandation
        recommandation = f"Recommandation {niveau} pour {vehicule.type_location.nom}"
        
        if points_forts:
            recommandation += f" avec {', '.join(points_forts)}"
        
        # Ajouter des conseils contextuels
        if contexte['trafic'] == 'fort':
            recommandation += ". Attention au trafic dense prévu."
        if contexte['periode_journee'] == 'nuit':
            recommandation += ". Parfait pour une sortie nocturne."
        
        return recommandation
    
    def _generer_insights_ia(self, recommandations: List, contexte: Dict, demande_data: Dict) -> List[str]:
        """Génère des insights intelligents basés sur l'analyse"""
        insights = []
        
        if not recommandations:
            insights.append("Aucun véhicule ne correspond parfaitement à vos critères. Essayez d'élargir votre recherche.")
            return insights
        
        # Insight sur le budget
        prix_moyen = sum(r['prix_estime'] for r in recommandations) / len(recommandations)
        budget_max = demande_data.get('budget_max', 100)
        
        if prix_moyen > budget_max * 0.8:
            insights.append(f"⚠️ Les prix sont élevés pour votre budget ({budget_max}€). Considérez une durée plus courte.")
        elif prix_moyen < budget_max * 0.5:
            insights.append(f"💰 Excellente opportunité ! Vous pouvez économiser sur votre budget de {budget_max}€.")
        
        # Insight sur la disponibilité
        if contexte['trafic'] == 'fort':
            insights.append("🚗 Trafic dense prévu. Réservez rapidement pour garantir la disponibilité.")
        
        # Insight sur l'écologie
        vehicules_ecologiques = [r for r in recommandations if r['score']['scores_detail']['ecologie'] > 0.7]
        if vehicules_ecologiques and demande_data.get('preferences_ecologiques'):
            insights.append("🌱 Excellentes options écologiques disponibles !")
        
        # Insight sur le confort
        if demande_data.get('nombre_passagers', 1) > 3:
            insights.append("👥 Pour plus de confort avec plusieurs passagers, privilégiez les véhicules avec espace supplémentaire.")
        
        return insights
    
    def _calculer_budget_optimal(self, recommandations: List) -> Dict:
        """Calcule le budget optimal basé sur les recommandations"""
        if not recommandations:
            return {'min': 0, 'max': 0, 'moyen': 0}
        
        prix = [r['prix_estime'] for r in recommandations]
        
        return {
            'min': min(prix),
            'max': max(prix),
            'moyen': sum(prix) / len(prix),
            'recommandé': sorted(prix)[len(prix)//2]  # Médiane
        }
    
    def analyser_historique_utilisateur(self, user_id: int) -> Dict:
        """Analyse l'historique de location d'un utilisateur pour des recommandations personnalisées"""
        try:
            # Récupérer l'historique
            reservations = ReservationLocation.objects.filter(
                utilisateur_id=user_id,
                statut='terminee'
            ).order_by('-date_creation')[:20]
            
            if not reservations:
                return {'message': 'Aucun historique disponible', 'preferences': {}}
            
            # Analyser les préférences
            preferences = {
                'categories_preferees': {},
                'durees_moyennes': [],
                'budgets_moyens': [],
                'lieux_frequents': {},
                'horaires_preferes': [],
                'satisfaction_moyenne': 0
            }
            
            for reservation in reservations:
                # Catégories préférées
                categorie = reservation.vehicule.type_location.categorie
                preferences['categories_preferees'][categorie] = \
                    preferences['categories_preferees'].get(categorie, 0) + 1
                
                # Durées
                duree = reservation.duree_location
                preferences['durees_moyennes'].append(duree)
                
                # Budgets
                prix = float(reservation.prix_total_calcule)
                preferences['budgets_moyens'].append(prix)
                
                # Lieux fréquents
                lieu = reservation.lieu_prise
                preferences['lieux_frequents'][lieu] = \
                    preferences['lieux_frequents'].get(lieu, 0) + 1
                
                # Horaires préférés
                heure = reservation.date_debut.hour
                preferences['horaires_preferes'].append(heure)
                
                # Satisfaction
                if reservation.note_experience:
                    preferences['satisfaction_moyenne'] += reservation.note_experience
            
            # Calculer les moyennes
            if preferences['durees_moyennes']:
                preferences['duree_moyenne'] = sum(preferences['durees_moyennes']) / len(preferences['durees_moyennes'])
            if preferences['budgets_moyens']:
                preferences['budget_moyen'] = sum(preferences['budgets_moyens']) / len(preferences['budgets_moyens'])
            if preferences['horaires_preferes']:
                preferences['horaire_prefere'] = sum(preferences['horaires_preferes']) / len(preferences['horaires_preferes'])
            if reservations.filter(note_experience__isnull=False).exists():
                notes = [r.note_experience for r in reservations if r.note_experience]
                preferences['satisfaction_moyenne'] = sum(notes) / len(notes)
            
            # Générer des recommandations personnalisées
            recommandations_personnalisees = self._generer_recommandations_personnalisees(preferences)
            
            return {
                'preferences': preferences,
                'recommandations_personnalisees': recommandations_personnalisees,
                'nombre_reservations_analysees': len(reservations)
            }
            
        except Exception as e:
            self.logger.error(f"Erreur analyse historique: {e}")
            return {'erreur': str(e)}


# Instance globale du moteur IA
location_ia_engine = LocationIAEngine()

