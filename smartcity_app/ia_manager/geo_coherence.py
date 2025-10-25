"""
Module de cohérence géographique pour les recommandations de trajets
Garantit des recommandations réalistes basées sur la géographie réelle
"""

import math
from typing import Dict, List, Tuple, Optional
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import logging

logger = logging.getLogger(__name__)


class GeoCoherenceManager:
    """Gestionnaire de cohérence géographique pour les trajets"""
    
    def __init__(self):
        # Définition des zones géographiques de Tunis et environs
        self.zones_tunis = {
            'centre_ville': {
                'nom': 'Centre-ville de Tunis',
                'centre': (36.8065, 10.1815),
                'rayon_km': 3,
                'transports_disponibles': ['metro', 'bus', 'tramway', 'taxi', 'velo', 'marche', 'trottinette']
            },
            'banlieue_proche': {
                'nom': 'Banlieue proche',
                'centre': (36.8065, 10.1815),
                'rayon_km': 15,
                'transports_disponibles': ['bus', 'tramway', 'taxi', 'voiture', 'velo_electrique', 'covoiturage']
            },
            'grande_tunis': {
                'nom': 'Grand Tunis',
                'centre': (36.8065, 10.1815),
                'rayon_km': 40,
                'transports_disponibles': ['bus', 'taxi', 'voiture', 'covoiturage']
            },
            'nationale': {
                'nom': 'Inter-villes Tunisie',
                'centre': (36.8065, 10.1815),
                'rayon_km': 300,
                'transports_disponibles': ['voiture', 'taxi_longue_distance', 'bus_inter_villes', 'covoiturage']
            },
            'internationale': {
                'nom': 'International',
                'centre': (36.8065, 10.1815),
                'rayon_km': 1000000,  # Illimité
                'transports_disponibles': ['avion', 'bateau']
            }
        }
        
        # Villes tunisiennes importantes avec coordonnées réelles
        self.villes_tunisie = {
            'tunis': (36.8065, 10.1815),
            'sfax': (34.7406, 10.7603),
            'sousse': (35.8256, 10.6369),
            'kairouan': (35.6781, 10.0963),
            'bizerte': (37.2746, 9.8739),
            'gabes': (33.8815, 10.0982),
            'ariana': (36.8625, 10.1956),
            'gafsa': (34.425, 8.7842),
            'monastir': (35.7772, 10.8262),
            'ben_arous': (36.7539, 10.2189),
            'la_marsa': (36.8770, 10.3247),
            'carthage': (36.8531, 10.3231),
            'hammam_lif': (36.7290, 10.3389),
            'nabeul': (36.4561, 10.7354),
            'hammamet': (36.3997, 10.6166),
        }
        
        # 🔧 Dictionnaire de corrections orthographiques communes
        self.corrections_orthographiques = {
            'safax': 'sfax',
            'sefax': 'sfax',
            'safex': 'sfax',
            'soussa': 'sousse',
            'souse': 'sousse',
            'sousa': 'sousse',
            'tunus': 'tunis',
            'tuniss': 'tunis',
            'bizerta': 'bizerte',
            'kairouan': 'kairouan',
            'kairawan': 'kairouan',
            'monastire': 'monastir',
            'gabbes': 'gabes',
            'gabes': 'gabes',
            'aryana': 'ariana',
            'la marsa': 'la_marsa',
            'lamarsa': 'la_marsa',
            'hamam lif': 'hammam_lif',
            'hammamlif': 'hammam_lif',
            'ben arrous': 'ben_arous',
            'benarous': 'ben_arous',
        }
        
        # Mapping nom de véhicule -> catégorie transport
        self.mapping_vehicules = {
            'Métro': 'metro',
            'Bus': 'bus',
            'Tramway': 'tramway',
            'Voiture Personnelle': 'voiture',
            'Moto': 'voiture',  # Même règles que voiture
            'Taxi': 'taxi',
            'Vélib (Vélo Partagé)': 'velo',
            'Autolib (Voiture Partagée)': 'covoiturage',
            'Trottinette Électrique': 'trottinette',
            'Vélo Personnel': 'velo',
            'Marche à Pied': 'marche',
            'Vélo Électrique': 'velo_electrique',
        }
        
        # Vitesses maximales réalistes (km/h)
        self.vitesses_max_reelles = {
            'metro': 35,
            'bus': 25,
            'tramway': 25,
            'voiture': 90,  # Sur autoroute
            'taxi': 80,
            'velo': 20,
            'velo_electrique': 25,
            'marche': 5,
            'trottinette': 20,
            'covoiturage': 80,
        }
        
        # Distances maximales recommandées (km)
        self.distances_max_recommandees = {
            'metro': 20,
            'bus': 30,
            'tramway': 15,
            'taxi': 40,
            'velo': 10,
            'velo_electrique': 25,
            'marche': 3,
            'trottinette': 8,
            'voiture': 300,
            'covoiturage': 300,
        }
    
    def calculer_distance_reelle(self, depart: Tuple[float, float], arrivee: Tuple[float, float]) -> float:
        """
        Calcule la distance réelle entre deux points géographiques
        
        Args:
            depart: (latitude, longitude) du point de départ
            arrivee: (latitude, longitude) du point d'arrivée
            
        Returns:
            Distance en kilomètres
        """
        try:
            distance_km = geodesic(depart, arrivee).kilometers
            return round(distance_km, 2)
        except Exception as e:
            logger.error(f"Erreur calcul distance: {e}")
            return None
    
    def determiner_zone_trajet(self, distance_km: float) -> str:
        """
        Détermine la zone géographique d'un trajet selon sa distance
        
        Returns:
            'centre_ville', 'banlieue_proche', 'grande_tunis', 'nationale', ou 'internationale'
        """
        if distance_km <= 3:
            return 'centre_ville'
        elif distance_km <= 15:
            return 'banlieue_proche'
        elif distance_km <= 40:
            return 'grande_tunis'
        elif distance_km <= 300:
            return 'nationale'
        else:
            return 'internationale'
    
    def vehicule_est_adapte(self, vehicule_nom: str, distance_km: float, 
                           depart_coords: Tuple[float, float], 
                           arrivee_coords: Tuple[float, float]) -> Tuple[bool, str]:
        """
        Vérifie si un véhicule est adapté pour un trajet donné
        
        Returns:
            (est_adapte: bool, raison: str)
        """
        # Mapper le nom du véhicule à sa catégorie
        categorie = self.mapping_vehicules.get(vehicule_nom, 'voiture')
        
        # Déterminer la zone du trajet
        zone = self.determiner_zone_trajet(distance_km)
        
        # Vérifier si le véhicule est disponible dans cette zone
        transports_zone = self.zones_tunis[zone]['transports_disponibles']
        
        if categorie not in transports_zone:
            raisons = {
                'centre_ville': f"Le {vehicule_nom} n'est pas disponible pour les trajets en centre-ville",
                'banlieue_proche': f"Le {vehicule_nom} n'est pas adapté pour la banlieue",
                'grande_tunis': f"Le {vehicule_nom} n'est pas recommandé pour le Grand Tunis",
                'nationale': f"Le {vehicule_nom} n'est pas adapté pour les trajets inter-villes",
                'internationale': f"Le {vehicule_nom} ne peut pas être utilisé pour les trajets internationaux",
            }
            return False, raisons.get(zone, f"{vehicule_nom} non disponible")
        
        # Vérifier la distance maximale recommandée
        distance_max = self.distances_max_recommandees.get(categorie, 1000)
        if distance_km > distance_max:
            return False, f"{vehicule_nom} non recommandé pour {distance_km}km (max conseillé: {distance_max}km)"
        
        # Vérifier la cohérence spécifique
        if zone == 'internationale':
            if categorie not in ['avion', 'bateau']:
                return False, f"Pour un trajet international ({distance_km}km), utilisez l'avion ou le bateau"
        
        if zone == 'nationale' and distance_km > 100:
            if categorie in ['metro', 'tramway', 'velo', 'marche', 'trottinette']:
                return False, f"{vehicule_nom} impossible pour {distance_km}km entre villes"
        
        return True, "Véhicule adapté"
    
    def calculer_duree_realiste(self, vehicule_nom: str, distance_km: float, 
                               heure_depart: int = 12, est_heure_pointe: bool = False) -> int:
        """
        Calcule une durée réaliste basée sur la distance et les conditions réelles
        
        Returns:
            Durée en minutes
        """
        categorie = self.mapping_vehicules.get(vehicule_nom, 'voiture')
        vitesse_base = self.vitesses_max_reelles.get(categorie, 30)
        
        # Ajustement selon le type de trajet
        if distance_km <= 3:  # Centre-ville
            vitesse_effective = vitesse_base * 0.6  # Circulation dense
        elif distance_km <= 15:  # Banlieue
            vitesse_effective = vitesse_base * 0.75
        elif distance_km <= 40:  # Grand Tunis
            vitesse_effective = vitesse_base * 0.85
        else:  # Longue distance
            vitesse_effective = vitesse_base * 0.9
        
        # Ajustement heure de pointe
        if est_heure_pointe and categorie in ['voiture', 'bus', 'tramway', 'taxi']:
            vitesse_effective *= 0.7
        
        # Calcul durée de base
        duree_base = (distance_km / vitesse_effective) * 60  # minutes
        
        # Ajouter temps d'attente pour transport public
        if categorie in ['metro', 'bus', 'tramway']:
            temps_attente = 8 if not est_heure_pointe else 5
            duree_base += temps_attente
        
        # Ajouter temps marche d'accès
        if categorie in ['metro', 'tramway']:
            duree_base += 6  # 3min aller + 3min retour
        
        return int(duree_base)
    
    def obtenir_coordonnees_ville(self, nom_ville: str) -> Optional[Tuple[float, float]]:
        """
        Obtient les coordonnées d'une ville connue avec correction orthographique
        
        Returns:
            (latitude, longitude) ou None
        """
        nom_normalise = nom_ville.lower().replace(' ', '_').replace('-', '_').strip()
        
        # 🔧 CORRECTION ORTHOGRAPHIQUE
        if nom_normalise in self.corrections_orthographiques:
            nom_corrige = self.corrections_orthographiques[nom_normalise]
            logger.info(f"✏️ Correction orthographique: '{nom_ville}' → '{nom_corrige}'")
            nom_normalise = nom_corrige
        
        # Recherche directe
        if nom_normalise in self.villes_tunisie:
            return self.villes_tunisie[nom_normalise]
        
        # Recherche dans les villes connues (fallback)
        for ville, coords in self.villes_tunisie.items():
            if nom_normalise in ville or ville in nom_normalise:
                return coords
        
        return None
    
    def generer_explication_coherence(self, vehicule_nom: str, distance_km: float, 
                                     zone: str, est_adapte: bool) -> str:
        """
        Génère une explication textuelle de la cohérence géographique
        """
        if est_adapte:
            return f"✅ {vehicule_nom} adapté pour {distance_km}km ({zone})"
        else:
            suggestions = {
                'centre_ville': ['Métro', 'Bus', 'Tramway', 'Vélo', 'Marche'],
                'banlieue_proche': ['Bus', 'Tramway', 'Taxi', 'Voiture'],
                'grande_tunis': ['Bus', 'Voiture', 'Taxi'],
                'nationale': ['Voiture', 'Bus inter-villes', 'Covoiturage'],
                'internationale': ['Avion', 'Bateau']
            }
            
            modes_sugges = suggestions.get(zone, ['Voiture'])
            return f"❌ {vehicule_nom} inadapté. Essayez: {', '.join(modes_sugges)}"
    
    def filtrer_vehicules_coherents(self, vehicules: List[Dict], distance_km: float,
                                   depart_coords: Tuple[float, float],
                                   arrivee_coords: Tuple[float, float]) -> List[Dict]:
        """
        Filtre une liste de véhicules pour ne garder que ceux qui sont cohérents
        
        Args:
            vehicules: Liste de dictionnaires avec informations véhicules
            distance_km: Distance du trajet
            depart_coords: Coordonnées de départ
            arrivee_coords: Coordonnées d'arrivée
            
        Returns:
            Liste filtrée avec ajout du champ 'coherence_geo'
        """
        vehicules_coherents = []
        zone = self.determiner_zone_trajet(distance_km)
        
        for vehicule in vehicules:
            vehicule_nom = vehicule.get('nom') or vehicule.get('vehicule_nom')
            
            est_adapte, raison = self.vehicule_est_adapte(
                vehicule_nom, distance_km, depart_coords, arrivee_coords
            )
            
            vehicule['coherence_geo'] = {
                'est_adapte': est_adapte,
                'raison': raison,
                'zone': zone,
                'explication': self.generer_explication_coherence(
                    vehicule_nom, distance_km, zone, est_adapte
                )
            }
            
            # Ajuster la durée pour être réaliste
            if 'duree_minutes' in vehicule:
                duree_realiste = self.calculer_duree_realiste(
                    vehicule_nom, distance_km
                )
                vehicule['duree_minutes_originale'] = vehicule['duree_minutes']
                vehicule['duree_minutes'] = duree_realiste
            
            # Ne garder que les véhicules adaptés
            if est_adapte:
                vehicules_coherents.append(vehicule)
        
        return vehicules_coherents
    
    def obtenir_info_zone(self, distance_km: float) -> Dict:
        """
        Retourne les informations détaillées sur la zone d'un trajet
        """
        zone_nom = self.determiner_zone_trajet(distance_km)
        zone_info = self.zones_tunis[zone_nom].copy()
        zone_info['zone_id'] = zone_nom
        return zone_info


# Instance globale
geo_coherence_manager = GeoCoherenceManager()
