#!/usr/bin/env python3
"""
Script pour intégrer les données du fichier RDF dans le système Django
"""

import os
import django
import json
from datetime import datetime, date
from django.utils import timezone

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartcity_core.settings')
django.setup()

from smartcity_app.gestion_trafic.models import ZoneTrafic, CapteurTrafic, DonneesTrafic, FeuSignalisation, EvenementTrafic
from smartcity_app.gestion_utilisateurs.models import ProfilUtilisateur
from smartcity_app.gestion_vehicules.models import Vehicule, TypeVehicule
from smartcity_app.gestion_stations.models import Station, EquipementStation
from smartcity_app.gestion_trajets.models import DemandeTrajetIntelligent, TrajetRecommande

def parse_rdf_data():
    """Parser les données du fichier RDF et les convertir en format Django"""
    print("🔄 Analyse du fichier RDF...")
    
    # Données extraites du fichier RDF
    rdf_data = {
        'utilisateurs': [
            {
                'nom': 'System',
                'prenom': 'Admin',
                'email': 'admin@smartcity.com',
                'role': 'Administrateur',
                'statut': 'actif',
                'preferences_trajet': '{"mode_prefere": "auto", "distance_max": 50}'
            },
            {
                'nom': 'Normal',
                'prenom': 'Utilisateur',
                'email': 'user@smartcity.com',
                'role': 'Utilisateur',
                'statut': 'actif',
                'preferences_trajet': '{"mode_prefere": "auto", "distance_max": 50}'
            },
            {
                'nom': 'mrabet',
                'prenom': 'sofienne',
                'email': 'sofienne.mrabet@esprit.tn',
                'role': 'Utilisateur',
                'statut': 'actif',
                'preferences_trajet': '{"mode_prefere": "auto", "distance_max": 50}'
            }
        ],
        'stations': [
            {
                'nom': 'Station Centre',
                'latitude': 36.81897,
                'longitude': 10.16579,
                'adresse': 'Avenue Habib Bourguiba, Tunis Centre',
                'capacite': 50,
                'heures_ouverture': '24h/24',
                'type_station': 'mixte'
            }
        ],
        'vehicules': [
            {
                'immatriculation': '123-TUN-456',
                'type_vehicule': 'électrique',
                'marque': 'Tesla',
                'modele': 'Model 3',
                'couleur': 'blanc',
                'statut': 'disponible',
                'niveau_batterie': 92.0,
                'station': 'Station Centre'
            }
        ],
        'velos': [
            {
                'marque': 'CityBike',
                'modele': 'Urban Pro',
                'couleur': 'bleu',
                'statut': 'disponible',
                'niveau_batterie': 85.5,
                'station': 'Station Centre'
            }
        ],
        'trajets': [
            {
                'point_depart': 'tunis',
                'point_arrivee': 'sousse',
                'distance': 116.27,
                'duree': 86.0,
                'cout': 42.69,
                'mode': 'Voiture Personnelle',
                'utilisateur': 'user@smartcity.com',
                'score_ia': 1.78,
                'niveau_circulation': 'fort'
            },
            {
                'point_depart': 'tunis',
                'point_arrivee': 'sfax',
                'distance': 235.12,
                'duree': 174.0,
                'cout': 37.27,
                'mode': 'Autolib (Voiture Partagée)',
                'utilisateur': 'user@smartcity.com',
                'score_ia': 1.0,
                'niveau_circulation': 'moyen'
            },
            {
                'point_depart': 'paris',
                'point_arrivee': 'marceille',
                'distance': 13.7,
                'duree': 32.0,
                'cout': 6.8,
                'mode': 'Voiture Personnelle',
                'utilisateur': 'user@smartcity.com',
                'score_ia': 6.44,
                'niveau_circulation': 'moyen'
            }
        ],
        'routes': [
            {
                'nom': 'Centre vers Université',
                'distance': 3.5,
                'temps_estime': 15,
                'type_route': 'urbaine',
                'station': 'Station Centre'
            }
        ],
        'pistes_cyclables': [
            {
                'nom': 'Piste Avenue Bourguiba',
                'longueur': 2.8,
                'type_piste': 'séparée',
                'etat_piste': 'bon'
            }
        ],
        'arrets': [
            {
                'nom': 'Arrêt Université',
                'latitude': 36.82456,
                'longitude': 10.1789,
                'accessibilite': True
            }
        ],
        'transports_publics': [
            {
                'ligne': '12',
                'frequence': 10,
                'type_transport': 'bus',
                'tarif': 0.8
            }
        ]
    }
    
    return rdf_data

def create_zones_from_rdf():
    """Créer des zones de trafic basées sur les données RDF"""
    print("🏙️ Création des zones de trafic à partir des données RDF...")
    
    zones_data = [
        {
            'nom': 'Zone Centre-Ville (RDF)',
            'type_zone': 'centre_ville',
            'description': 'Zone centrale basée sur les données RDF',
            'coordonnees_zone': {
                "type": "Polygon",
                "coordinates": [[[10.16, 36.81], [10.17, 36.81], [10.17, 36.82], [10.16, 36.82], [10.16, 36.81]]]
            },
            'vitesse_limite': 50,
            'nombre_voies': 4,
            'sens_circulation': 'bidirectionnel',
        },
        {
            'nom': 'Zone Université (RDF)',
            'type_zone': 'zone_educative',
            'description': 'Zone universitaire basée sur les données RDF',
            'coordonnees_zone': {
                "type": "Polygon",
                "coordinates": [[[10.17, 36.82], [10.18, 36.82], [10.18, 36.83], [10.17, 36.83], [10.17, 36.82]]]
            },
            'vitesse_limite': 30,
            'nombre_voies': 2,
            'sens_circulation': 'bidirectionnel',
        }
    ]
    
    zones_created = 0
    for zone_data in zones_data:
        zone, created = ZoneTrafic.objects.get_or_create(
            nom=zone_data['nom'],
            defaults=zone_data
        )
        if created:
            zones_created += 1
            print(f"  ✅ Zone '{zone.nom}' créée.")
        else:
            print(f"  ℹ️ Zone '{zone.nom}' existe déjà.")
    
    print(f"📊 {zones_created} nouvelles zones créées.")
    return ZoneTrafic.objects.filter(nom__contains='RDF')

def create_capteurs_from_rdf(zones):
    """Créer des capteurs de trafic basés sur les données RDF"""
    print("📡 Création des capteurs de trafic à partir des données RDF...")
    
    capteurs_data = [
        {
            'nom': 'Capteur RDF Centre',
            'code_capteur': 'RDF-C-001',
            'type_capteur': 'camera_ia',
            'zone_trafic': zones[0] if zones.exists() else None,
            'latitude': 36.81897,
            'longitude': 10.16579,
            'direction_mesure': 'Nord-Sud',
            'statut': 'actif',
            'frequence_mesure': 30,
            'precision_detection': 98.0,
            'vitesse_min_detection': 5,
            'vitesse_max_detection': 80,
            'date_installation': date(2024, 1, 1),
            'fournisseur': 'SmartCity RDF',
            'modele': 'RDF-Camera-Pro'
        },
        {
            'nom': 'Capteur RDF Université',
            'code_capteur': 'RDF-U-001',
            'type_capteur': 'radar',
            'zone_trafic': zones[1] if zones.count() > 1 else zones[0],
            'latitude': 36.82456,
            'longitude': 10.1789,
            'direction_mesure': 'Est-Ouest',
            'statut': 'actif',
            'frequence_mesure': 60,
            'precision_detection': 95.0,
            'vitesse_min_detection': 5,
            'vitesse_max_detection': 50,
            'date_installation': date(2024, 2, 1),
            'fournisseur': 'SmartCity RDF',
            'modele': 'RDF-Radar-Edu'
        }
    ]
    
    capteurs_created = 0
    for capteur_data in capteurs_data:
        if capteur_data['zone_trafic']:
            capteur, created = CapteurTrafic.objects.get_or_create(
                code_capteur=capteur_data['code_capteur'],
                defaults=capteur_data
            )
            if created:
                capteurs_created += 1
                print(f"  ✅ Capteur '{capteur.nom}' créé.")
            else:
                print(f"  ℹ️ Capteur '{capteur.nom}' existe déjà.")
    
    print(f"📊 {capteurs_created} nouveaux capteurs créés.")
    return CapteurTrafic.objects.filter(code_capteur__startswith='RDF')

def create_donnees_trafic_from_rdf(capteurs):
    """Créer des données de trafic basées sur les trajets RDF"""
    print("📈 Création des données de trafic à partir des trajets RDF...")
    
    rdf_data = parse_rdf_data()
    donnees_created = 0
    
    for capteur in capteurs:
        # Créer des données basées sur les trajets RDF
        for i, trajet in enumerate(rdf_data['trajets']):
            timestamp = timezone.now() - timezone.timedelta(hours=i*2)
            
            # Calculer le nombre de véhicules basé sur la distance et le mode
            base_vehicules = 50
            if trajet['mode'] == 'Voiture Personnelle':
                base_vehicules = 80
            elif 'Partagée' in trajet['mode']:
                base_vehicules = 60
            elif 'Moto' in trajet['mode']:
                base_vehicules = 40
            
            # Calculer la vitesse moyenne basée sur la durée et distance
            vitesse_moyenne = (trajet['distance'] / trajet['duree']) * 60 if trajet['duree'] > 0 else 30
            
            # Déterminer le niveau de congestion
            niveau_congestion = 'faible'
            if trajet['niveau_circulation'] == 'fort':
                niveau_congestion = 'eleve'
            elif trajet['niveau_circulation'] == 'moyen':
                niveau_congestion = 'modere'
            
            # Calculer le taux d'occupation
            taux_occupation = min(90, base_vehicules * 0.8)
            
            donnee, created = DonneesTrafic.objects.get_or_create(
                capteur=capteur,
                timestamp=timestamp,
                defaults={
                    'nombre_vehicules': base_vehicules,
                    'vitesse_moyenne': round(vitesse_moyenne, 2),
                    'niveau_congestion': niveau_congestion,
                    'taux_occupation': round(taux_occupation, 2),
                }
            )
            if created:
                donnees_created += 1
    
    print(f"📊 {donnees_created} nouvelles données de trafic créées.")

def create_feux_from_rdf(zones):
    """Créer des feux de signalisation basés sur les données RDF"""
    print("🚦 Création des feux de signalisation à partir des données RDF...")
    
    feux_data = [
        {
            'nom': 'Feu RDF Centre-Bourguiba',
            'code_feu': 'RDF-F-001',
            'type_feu': 'tricolore_standard',
            'zone_trafic': zones[0] if zones.exists() else None,
            'latitude': 36.819,
            'longitude': 10.166,
            'carrefour': 'Avenue Bourguiba / Rue de la République',
            'date_installation': date(2024, 1, 15),
            'statut': 'actif'
        },
        {
            'nom': 'Feu RDF Université',
            'code_feu': 'RDF-F-002',
            'type_feu': 'tricolore_pietons',
            'zone_trafic': zones[1] if zones.count() > 1 else zones[0],
            'latitude': 36.825,
            'longitude': 10.179,
            'carrefour': 'Rue Université / Avenue des Sciences',
            'date_installation': date(2024, 2, 1),
            'statut': 'actif'
        }
    ]
    
    feux_created = 0
    for feu_data in feux_data:
        if feu_data['zone_trafic']:
            feu, created = FeuSignalisation.objects.get_or_create(
                code_feu=feu_data['code_feu'],
                defaults=feu_data
            )
            if created:
                feux_created += 1
                print(f"  ✅ Feu '{feu.nom}' créé.")
            else:
                print(f"  ℹ️ Feu '{feu.nom}' existe déjà.")
    
    print(f"📊 {feux_created} nouveaux feux créés.")

def create_evenements_from_rdf(zones):
    """Créer des événements de trafic basés sur les données RDF"""
    print("⚠️ Création des événements de trafic à partir des données RDF...")
    
    now = timezone.now()
    evenements_data = [
        {
            'titre': 'Travaux Avenue Bourguiba (RDF)',
            'type_evenement': 'travaux',
            'description': 'Réfection de la chaussée principale basée sur les données RDF',
            'zones_affectees': [zones[0]] if zones.exists() else [],
            'niveau_impact': 'modere',
            'date_debut': now - timezone.timedelta(days=1),
            'date_fin_prevue': now + timezone.timedelta(days=3),
            'statut': 'en_cours'
        },
        {
            'titre': 'Manifestation Université (RDF)',
            'type_evenement': 'manifestation',
            'description': 'Manifestation étudiante affectant la circulation',
            'zones_affectees': [zones[1]] if zones.count() > 1 else [zones[0]],
            'niveau_impact': 'faible',
            'date_debut': now - timezone.timedelta(hours=2),
            'date_fin_prevue': now + timezone.timedelta(hours=4),
            'statut': 'en_cours'
        }
    ]
    
    evenements_created = 0
    for evenement_data in evenements_data:
        if evenement_data['zones_affectees']:
            zones_affectees_list = evenement_data.pop('zones_affectees')
            evenement, created = EvenementTrafic.objects.get_or_create(
                titre=evenement_data['titre'],
                defaults=evenement_data
            )
            if created:
                evenement.zones_affectees.set(zones_affectees_list)
                evenements_created += 1
                print(f"  ✅ Événement '{evenement.titre}' créé.")
            else:
                print(f"  ℹ️ Événement '{evenement.titre}' existe déjà.")
    
    print(f"📊 {evenements_created} nouveaux événements créés.")

def integrate_rdf_data():
    """Fonction principale pour intégrer toutes les données RDF"""
    print("🚀 === INTÉGRATION DES DONNÉES RDF ===")
    print()
    
    try:
        # 1. Créer les zones de trafic
        zones = create_zones_from_rdf()
        print()
        
        # 2. Créer les capteurs de trafic
        capteurs = create_capteurs_from_rdf(zones)
        print()
        
        # 3. Créer les données de trafic
        create_donnees_trafic_from_rdf(capteurs)
        print()
        
        # 4. Créer les feux de signalisation
        create_feux_from_rdf(zones)
        print()
        
        # 5. Créer les événements de trafic
        create_evenements_from_rdf(zones)
        print()
        
        print("✅ === INTÉGRATION RDF TERMINÉE AVEC SUCCÈS ===")
        print()
        print("📊 Résumé de l'intégration :")
        print(f"   • Zones de trafic RDF : {zones.count()}")
        print(f"   • Capteurs de trafic RDF : {capteurs.count()}")
        print(f"   • Feux de signalisation RDF : {FeuSignalisation.objects.filter(code_feu__startswith='RDF').count()}")
        print(f"   • Événements de trafic RDF : {EvenementTrafic.objects.filter(titre__contains='RDF').count()}")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'intégration RDF : {str(e)}")
        raise

if __name__ == '__main__':
    integrate_rdf_data()
