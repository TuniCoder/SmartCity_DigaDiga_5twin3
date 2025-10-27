#!/usr/bin/env python
"""
Script pour créer des radars et caméras de surveillance en Tunisie
Ajoute des données réalistes pour les principales routes et zones urbaines
"""

import os
import django
from datetime import date, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartcity_core.settings')
django.setup()

from smartcity_app.gestion_trafic.models import CapteurTrafic, ZoneTrafic

# Données des radars et caméras en Tunisie
TUNISIA_SENSORS = [
    # ========== RADARS - Routes principales ==========
    {
        'nom': 'Radar A1 - Tunis Nord',
        'code_capteur': 'RADAR-A1-001',
        'type_capteur': 'radar',
        'latitude': 36.8500,
        'longitude': 10.2000,
        'direction_mesure': 'Nord-Sud',
        'statut': 'actif',
        'frequence_mesure': 30,
        'precision_detection': 98.5,
        'vitesse_min_detection': 5,
        'vitesse_max_detection': 200,
        'fournisseur': 'Bosch Traffic',
        'modele': 'Bosch Radar Pro 2024',
    },
    {
        'nom': 'Radar A1 - Sfax',
        'code_capteur': 'RADAR-A1-002',
        'type_capteur': 'radar',
        'latitude': 34.7405,
        'longitude': 10.7603,
        'direction_mesure': 'Nord-Sud',
        'statut': 'actif',
        'frequence_mesure': 30,
        'precision_detection': 98.5,
        'vitesse_min_detection': 5,
        'vitesse_max_detection': 200,
        'fournisseur': 'Bosch Traffic',
        'modele': 'Bosch Radar Pro 2024',
    },
    {
        'nom': 'Radar GP1 - Sousse',
        'code_capteur': 'RADAR-GP1-001',
        'type_capteur': 'radar',
        'latitude': 35.8256,
        'longitude': 10.6369,
        'direction_mesure': 'Est-Ouest',
        'statut': 'actif',
        'frequence_mesure': 30,
        'precision_detection': 98.0,
        'vitesse_min_detection': 5,
        'vitesse_max_detection': 200,
        'fournisseur': 'Siemens Traffic',
        'modele': 'Siemens Radar 3000',
    },
    {
        'nom': 'Radar A3 - Kairouan',
        'code_capteur': 'RADAR-A3-001',
        'type_capteur': 'radar',
        'latitude': 35.6781,
        'longitude': 9.9197,
        'direction_mesure': 'Nord-Sud',
        'statut': 'actif',
        'frequence_mesure': 30,
        'precision_detection': 97.5,
        'vitesse_min_detection': 5,
        'vitesse_max_detection': 200,
        'fournisseur': 'Siemens Traffic',
        'modele': 'Siemens Radar 3000',
    },
    
    # ========== CAMÉRAS - Zones urbaines ==========
    {
        'nom': 'Caméra Centre Tunis - Avenue Habib Bourguiba',
        'code_capteur': 'CAM-TUNIS-001',
        'type_capteur': 'camera_ia',
        'latitude': 36.8065,
        'longitude': 10.1815,
        'direction_mesure': 'Nord-Sud',
        'statut': 'actif',
        'frequence_mesure': 60,
        'precision_detection': 96.0,
        'vitesse_min_detection': 5,
        'vitesse_max_detection': 80,
        'fournisseur': 'Hikvision',
        'modele': 'Hikvision DS-2CD7A26G0-IZS',
    },
    {
        'nom': 'Caméra Carrefour Bab Saadoun',
        'code_capteur': 'CAM-TUNIS-002',
        'type_capteur': 'camera_ia',
        'latitude': 36.7994,
        'longitude': 10.1956,
        'direction_mesure': 'Est-Ouest',
        'statut': 'actif',
        'frequence_mesure': 60,
        'precision_detection': 95.5,
        'vitesse_min_detection': 5,
        'vitesse_max_detection': 80,
        'fournisseur': 'Dahua',
        'modele': 'Dahua IPC-HFW5241E-Z',
    },
    {
        'nom': 'Caméra Sfax - Rue Bourguiba',
        'code_capteur': 'CAM-SFAX-001',
        'type_capteur': 'camera_ia',
        'latitude': 34.7405,
        'longitude': 10.7603,
        'direction_mesure': 'Nord-Sud',
        'statut': 'actif',
        'frequence_mesure': 60,
        'precision_detection': 95.0,
        'vitesse_min_detection': 5,
        'vitesse_max_detection': 80,
        'fournisseur': 'Hikvision',
        'modele': 'Hikvision DS-2CD7A26G0-IZS',
    },
    {
        'nom': 'Caméra Sousse - Corniche',
        'code_capteur': 'CAM-SOUSSE-001',
        'type_capteur': 'camera_ia',
        'latitude': 35.8256,
        'longitude': 10.6369,
        'direction_mesure': 'Est-Ouest',
        'statut': 'actif',
        'frequence_mesure': 60,
        'precision_detection': 94.5,
        'vitesse_min_detection': 5,
        'vitesse_max_detection': 80,
        'fournisseur': 'Dahua',
        'modele': 'Dahua IPC-HFW5241E-Z',
    },
    {
        'nom': 'Caméra Kairouan - Centre Ville',
        'code_capteur': 'CAM-KAIROUAN-001',
        'type_capteur': 'camera_ia',
        'latitude': 35.6781,
        'longitude': 9.9197,
        'direction_mesure': 'Nord-Sud',
        'statut': 'actif',
        'frequence_mesure': 60,
        'precision_detection': 94.0,
        'vitesse_min_detection': 5,
        'vitesse_max_detection': 80,
        'fournisseur': 'Hikvision',
        'modele': 'Hikvision DS-2CD7A26G0-IZS',
    },
]

def create_sensors():
    """Créer les radars et caméras en Tunisie"""
    
    print("=" * 80)
    print("🇹🇳 CRÉATION DES RADARS ET CAMÉRAS EN TUNISIE")
    print("=" * 80)
    print()
    
    # Récupérer une zone par défaut
    zone = ZoneTrafic.objects.first()
    if not zone:
        print("❌ Aucune zone de trafic trouvée. Créez d'abord des zones.")
        return False
    
    print(f"📍 Zone utilisée: {zone.nom}")
    print()
    
    created_count = 0
    skipped_count = 0
    
    for sensor_data in TUNISIA_SENSORS:
        try:
            # Vérifier si le capteur existe déjà
            if CapteurTrafic.objects.filter(code_capteur=sensor_data['code_capteur']).exists():
                print(f"⏭️  {sensor_data['nom']} - Déjà existant")
                skipped_count += 1
                continue
            
            # Créer le capteur
            capteur = CapteurTrafic.objects.create(
                nom=sensor_data['nom'],
                code_capteur=sensor_data['code_capteur'],
                type_capteur=sensor_data['type_capteur'],
                zone_trafic=zone,
                latitude=sensor_data['latitude'],
                longitude=sensor_data['longitude'],
                direction_mesure=sensor_data['direction_mesure'],
                statut=sensor_data['statut'],
                frequence_mesure=sensor_data['frequence_mesure'],
                precision_detection=sensor_data['precision_detection'],
                vitesse_min_detection=sensor_data['vitesse_min_detection'],
                vitesse_max_detection=sensor_data['vitesse_max_detection'],
                date_installation=date.today() - timedelta(days=30),
                fournisseur=sensor_data['fournisseur'],
                modele=sensor_data['modele'],
            )
            
            icon = "📡" if sensor_data['type_capteur'] == 'radar' else "📹"
            print(f"✅ {icon} {sensor_data['nom']} créé")
            created_count += 1
            
        except Exception as e:
            print(f"❌ Erreur lors de la création de {sensor_data['nom']}: {str(e)}")
    
    print()
    print("=" * 80)
    print(f"✅ RÉSUMÉ: {created_count} capteurs créés, {skipped_count} ignorés")
    print("=" * 80)
    print()
    
    # Afficher les statistiques
    radars = CapteurTrafic.objects.filter(type_capteur='radar')
    cameras = CapteurTrafic.objects.filter(type_capteur='camera_ia')
    
    print(f"📡 Radars: {radars.count()}")
    print(f"📹 Caméras: {cameras.count()}")
    print()
    
    return True

if __name__ == '__main__':
    create_sensors()

