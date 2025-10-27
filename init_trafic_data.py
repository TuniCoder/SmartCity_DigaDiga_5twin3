#!/usr/bin/env python
"""
Script d'initialisation des données de test pour le module Gestion du Trafic
"""

import os
import sys
import django
from datetime import datetime, timedelta
import random

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartcity_core.settings')
django.setup()

from smartcity_app.gestion_trafic.models import ZoneTrafic, CapteurTrafic, DonneesTrafic
from django.contrib.auth.models import User


def create_zones_trafic():
    """Créer des zones de trafic de test"""
    print("🏙️ Création des zones de trafic...")
    
    zones_data = [
        {
            'nom': 'Centre-Ville Principal',
            'type_zone': 'centre_ville',
            'description': 'Zone commerciale et administrative du centre-ville',
            'coordonnees_zone': {
                "type": "Polygon",
                "coordinates": [[[10.18, 36.80], [10.19, 36.80], [10.19, 36.81], [10.18, 36.81], [10.18, 36.80]]]
            },
            'vitesse_limite': 50,
            'nombre_voies': 4,
            'sens_circulation': 'bidirectionnel',
        },
        {
            'nom': 'Avenue des Champs-Élysées',
            'type_zone': 'zone_commerciale',
            'description': 'Axe principal commercial avec forte affluence',
            'coordonnees_zone': {
                "type": "Polygon",
                "coordinates": [[[10.18, 36.81], [10.20, 36.81], [10.20, 36.82], [10.18, 36.82], [10.18, 36.81]]]
            },
            'vitesse_limite': 50,
            'nombre_voies': 6,
            'sens_circulation': 'bidirectionnel',
        },
        {
            'nom': 'Rocade Est',
            'type_zone': 'rocade',
            'description': 'Rocade périphérique est de la ville',
            'coordonnees_zone': {
                "type": "Polygon",
                "coordinates": [[[10.18, 36.82], [10.21, 36.82], [10.21, 36.83], [10.18, 36.83], [10.18, 36.82]]]
            },
            'vitesse_limite': 90,
            'nombre_voies': 4,
            'sens_circulation': 'bidirectionnel',
        },
        {
            'nom': 'Zone Industrielle Nord',
            'type_zone': 'zone_industrielle',
            'description': 'Zone industrielle avec circulation de poids lourds',
            'coordonnees_zone': {
                "type": "Polygon",
                "coordinates": [[[10.18, 36.83], [10.20, 36.83], [10.20, 36.84], [10.18, 36.84], [10.18, 36.83]]]
            },
            'vitesse_limite': 70,
            'nombre_voies': 2,
            'sens_circulation': 'bidirectionnel',
        },
        {
            'nom': 'Quartier Résidentiel Sud',
            'type_zone': 'zone_residentielle',
            'description': 'Quartier résidentiel calme',
            'coordonnees_zone': {
                "type": "Polygon",
                "coordinates": [[[10.18, 36.84], [10.20, 36.84], [10.20, 36.85], [10.18, 36.85], [10.18, 36.84]]]
            },
            'vitesse_limite': 30,
            'nombre_voies': 2,
            'sens_circulation': 'bidirectionnel',
        },
    ]
    
    zones_created = 0
    for zone_data in zones_data:
        zone, created = ZoneTrafic.objects.get_or_create(
            nom=zone_data['nom'],
            defaults=zone_data
        )
        if created:
            zones_created += 1
            print(f"  ✅ Zone créée: {zone.nom}")
        else:
            print(f"  ⚠️ Zone existante: {zone.nom}")
    
    print(f"📊 {zones_created} nouvelles zones créées")
    return ZoneTrafic.objects.all()


def create_capteurs_trafic(zones):
    """Créer des capteurs de trafic de test"""
    print("📡 Création des capteurs de trafic...")
    
    capteurs_data = [
        {
            'nom': 'Capteur Centre-1',
            'code_capteur': 'CTR-001',
            'type_capteur': 'camera_ia',
            'zone_trafic': zones[0],
            'latitude': 36.8065,
            'longitude': 10.1815,
            'direction_mesure': 'Nord-Sud',
            'statut': 'actif',
            'frequence_mesure': 60,
            'precision_detection': 95.0,
            'vitesse_min_detection': 5,
            'vitesse_max_detection': 200,
            'date_installation': datetime.now().date() - timedelta(days=30),
            'fournisseur': 'TrafficTech Solutions',
            'modele': 'TT-CAM-2024',
        },
        {
            'nom': 'Capteur Champs-Élysées-1',
            'code_capteur': 'CHM-001',
            'type_capteur': 'boucle_magnetique',
            'zone_trafic': zones[1],
            'latitude': 36.8075,
            'longitude': 10.1825,
            'direction_mesure': 'Est-Ouest',
            'statut': 'actif',
            'frequence_mesure': 30,
            'precision_detection': 98.0,
            'vitesse_min_detection': 10,
            'vitesse_max_detection': 150,
            'date_installation': datetime.now().date() - timedelta(days=45),
            'fournisseur': 'MagneticFlow Inc',
            'modele': 'MF-LOOP-2024',
        },
        {
            'nom': 'Capteur Rocade-Est-1',
            'code_capteur': 'RCE-001',
            'type_capteur': 'radar',
            'zone_trafic': zones[2],
            'latitude': 36.8085,
            'longitude': 10.1835,
            'direction_mesure': 'Nord-Sud',
            'statut': 'actif',
            'frequence_mesure': 120,
            'precision_detection': 92.0,
            'vitesse_min_detection': 20,
            'vitesse_max_detection': 200,
            'date_installation': datetime.now().date() - timedelta(days=60),
            'fournisseur': 'RadarTech Pro',
            'modele': 'RT-RADAR-2024',
        },
        {
            'nom': 'Capteur Industriel-Nord-1',
            'code_capteur': 'IND-001',
            'type_capteur': 'lidar',
            'zone_trafic': zones[3],
            'latitude': 36.8095,
            'longitude': 10.1845,
            'direction_mesure': 'Est-Ouest',
            'statut': 'maintenance',
            'frequence_mesure': 90,
            'precision_detection': 97.0,
            'vitesse_min_detection': 5,
            'vitesse_max_detection': 100,
            'date_installation': datetime.now().date() - timedelta(days=20),
            'fournisseur': 'LiDAR Systems',
            'modele': 'LS-LIDAR-2024',
        },
        {
            'nom': 'Capteur Résidentiel-Sud-1',
            'code_capteur': 'RES-001',
            'type_capteur': 'capteur_bluetooth',
            'zone_trafic': zones[4],
            'latitude': 36.8105,
            'longitude': 10.1855,
            'direction_mesure': 'Nord-Sud',
            'statut': 'actif',
            'frequence_mesure': 180,
            'precision_detection': 85.0,
            'vitesse_min_detection': 5,
            'vitesse_max_detection': 80,
            'date_installation': datetime.now().date() - timedelta(days=15),
            'fournisseur': 'BluetoothTraffic',
            'modele': 'BT-SENSOR-2024',
        },
        {
            'nom': 'Capteur Centre-2',
            'code_capteur': 'CTR-002',
            'type_capteur': 'camera_ia',
            'zone_trafic': zones[0],
            'latitude': 36.8067,
            'longitude': 10.1817,
            'direction_mesure': 'Est-Ouest',
            'statut': 'inactif',
            'frequence_mesure': 60,
            'precision_detection': 95.0,
            'vitesse_min_detection': 5,
            'vitesse_max_detection': 200,
            'date_installation': datetime.now().date() - timedelta(days=10),
            'fournisseur': 'TrafficTech Solutions',
            'modele': 'TT-CAM-2024',
        },
    ]
    
    capteurs_created = 0
    for capteur_data in capteurs_data:
        capteur, created = CapteurTrafic.objects.get_or_create(
            code_capteur=capteur_data['code_capteur'],
            defaults=capteur_data
        )
        if created:
            capteurs_created += 1
            print(f"  ✅ Capteur créé: {capteur.nom} ({capteur.code_capteur})")
        else:
            print(f"  ⚠️ Capteur existant: {capteur.nom} ({capteur.code_capteur})")
    
    print(f"📊 {capteurs_created} nouveaux capteurs créés")
    return CapteurTrafic.objects.all()


def create_donnees_trafic(capteurs):
    """Créer des données de trafic de test"""
    print("📊 Création des données de trafic...")
    
    niveaux_congestion = ['fluide', 'dense', 'ralenti', 'bouchon', 'bloque']
    
    donnees_created = 0
    for capteur in capteurs:
        if capteur.statut != 'actif':
            continue
            
        # Créer des données pour les 7 derniers jours
        for day in range(7):
            date_base = datetime.now() - timedelta(days=day)
            
            # Créer des données toutes les heures
            for hour in range(24):
                timestamp = date_base.replace(hour=hour, minute=0, second=0, microsecond=0)
                
                # Simuler des variations selon l'heure
                if 7 <= hour <= 9 or 17 <= hour <= 19:  # Heures de pointe
                    base_vehicules = random.randint(80, 150)
                    base_vitesse = random.randint(15, 35)
                    niveau = random.choice(['dense', 'ralenti', 'bouchon'])
                elif 22 <= hour or hour <= 5:  # Nuit
                    base_vehicules = random.randint(5, 25)
                    base_vitesse = random.randint(40, 80)
                    niveau = 'fluide'
                else:  # Heures normales
                    base_vehicules = random.randint(30, 80)
                    base_vitesse = random.randint(25, 50)
                    niveau = random.choice(['fluide', 'dense'])
                
                # Créer la donnée
                donnee, created = DonneesTrafic.objects.get_or_create(
                    capteur=capteur,
                    timestamp=timestamp,
                    defaults={
                        'nombre_vehicules': base_vehicules,
                        'vitesse_moyenne': base_vitesse,
                        'vitesse_mediane': base_vitesse + random.randint(-5, 5),
                        'debit_vehicules': base_vehicules * 60,  # Véhicules par heure
                        'vehicules_legers': int(base_vehicules * 0.8),
                        'vehicules_lourds': int(base_vehicules * 0.15),
                        'deux_roues': int(base_vehicules * 0.05),
                        'transports_publics': random.randint(0, 5),
                        'niveau_congestion': niveau,
                        'taux_occupation': random.uniform(20, 90),
                        'conditions_meteo': random.choice(['ensoleillé', 'nuageux', 'pluvieux']),
                        'visibilite': random.randint(100, 1000),
                        'temperature': random.uniform(15, 35),
                        'incident_detecte': random.choice([True, False]) if random.random() < 0.05 else False,
                        'type_incident': random.choice(['accident', 'panne', 'travaux']) if random.random() < 0.05 else '',
                    }
                )
                
                if created:
                    donnees_created += 1
    
    print(f"📊 {donnees_created} nouvelles données créées")
    return DonneesTrafic.objects.count()


def main():
    """Fonction principale"""
    print("🚦 Initialisation des données de test - Module Gestion du Trafic")
    print("=" * 60)
    
    try:
        # Créer les zones de trafic
        zones = create_zones_trafic()
        
        # Créer les capteurs
        capteurs = create_capteurs_trafic(zones)
        
        # Créer les données de trafic
        total_donnees = create_donnees_trafic(capteurs)
        
        print("\n" + "=" * 60)
        print("✅ Initialisation terminée avec succès !")
        print(f"📊 Résumé:")
        print(f"   - Zones de trafic: {zones.count()}")
        print(f"   - Capteurs: {capteurs.count()}")
        print(f"   - Données de trafic: {total_donnees}")
        print("\n🌐 Vous pouvez maintenant accéder au module via:")
        print("   http://127.0.0.1:8000/trafic/")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
