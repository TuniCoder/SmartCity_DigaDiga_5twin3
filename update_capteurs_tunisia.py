#!/usr/bin/env python
"""
Script pour mettre à jour les capteurs avec des noms réels tunisiens
et les réassocier aux nouvelles zones
"""

import os
import django
from datetime import date, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartcity_core.settings')
django.setup()

from smartcity_app.gestion_trafic.models import CapteurTrafic, ZoneTrafic

# Mapping des capteurs avec les zones réelles tunisiennes
CAPTEURS_TUNISIA = [
    # Tunis - Centre-Ville
    {
        'nom': 'Capteur Avenue Habib Bourguiba - Tunis',
        'code_capteur': 'CAP-TUNIS-AVE-001',
        'type_capteur': 'camera_ia',
        'zone_nom': 'Centre-Ville Tunis',
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
    # Tunis - Bab Saadoun
    {
        'nom': 'Capteur Carrefour Bab Saadoun - Tunis',
        'code_capteur': 'CAP-TUNIS-BAB-001',
        'type_capteur': 'camera_ia',
        'zone_nom': 'Bab Saadoun - Tunis',
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
    # Autoroute A1 - Tunis Nord
    {
        'nom': 'Radar Autoroute A1 - Tunis Nord',
        'code_capteur': 'RAD-A1-TUNIS-001',
        'type_capteur': 'radar',
        'zone_nom': 'Autoroute A1 - Tunis Nord',
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
    # Rocade Nord Tunis
    {
        'nom': 'Capteur Rocade Nord Tunis',
        'code_capteur': 'CAP-ROCADE-TUNIS-001',
        'type_capteur': 'boucle_magnetique',
        'zone_nom': 'Rocade Nord Tunis',
        'latitude': 36.8700,
        'longitude': 10.1800,
        'direction_mesure': 'Est-Ouest',
        'statut': 'actif',
        'frequence_mesure': 30,
        'precision_detection': 94.0,
        'vitesse_min_detection': 5,
        'vitesse_max_detection': 120,
        'fournisseur': 'Siemens',
        'modele': 'Siemens Loop Detector',
    },
    # Sfax - Zone Industrielle
    {
        'nom': 'Capteur Zone Industrielle Sfax',
        'code_capteur': 'CAP-SFAX-IND-001',
        'type_capteur': 'camera_ia',
        'zone_nom': 'Zone Industrielle Sfax',
        'latitude': 34.7450,
        'longitude': 10.7650,
        'direction_mesure': 'Nord-Sud',
        'statut': 'actif',
        'frequence_mesure': 60,
        'precision_detection': 95.0,
        'vitesse_min_detection': 5,
        'vitesse_max_detection': 80,
        'fournisseur': 'Hikvision',
        'modele': 'Hikvision DS-2CD7A26G0-IZS',
    },
    # Sfax - Centre-Ville
    {
        'nom': 'Capteur Rue Bourguiba - Sfax',
        'code_capteur': 'CAP-SFAX-RUE-001',
        'type_capteur': 'camera_ia',
        'zone_nom': 'Centre-Ville Sfax',
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
    # Autoroute A1 - Sfax
    {
        'nom': 'Radar Autoroute A1 - Sfax',
        'code_capteur': 'RAD-A1-SFAX-001',
        'type_capteur': 'radar',
        'zone_nom': 'Autoroute A1 - Sousse',
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
    # Sousse - Corniche
    {
        'nom': 'Capteur Corniche Sousse',
        'code_capteur': 'CAP-SOUSSE-CORN-001',
        'type_capteur': 'camera_ia',
        'zone_nom': 'Corniche Sousse',
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
    # Autoroute A1 - Sousse
    {
        'nom': 'Radar Autoroute A1 - Sousse',
        'code_capteur': 'RAD-A1-SOUSSE-001',
        'type_capteur': 'radar',
        'zone_nom': 'Autoroute A1 - Sousse',
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
    # Kairouan - Centre-Ville
    {
        'nom': 'Capteur Centre-Ville Kairouan',
        'code_capteur': 'CAP-KAIROUAN-CTR-001',
        'type_capteur': 'camera_ia',
        'zone_nom': 'Centre-Ville Kairouan',
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
    # Autoroute A3 - Kairouan
    {
        'nom': 'Radar Autoroute A3 - Kairouan',
        'code_capteur': 'RAD-A3-KAIROUAN-001',
        'type_capteur': 'radar',
        'zone_nom': 'Autoroute A3 - Kairouan',
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
]

def update_capteurs():
    """Mettre à jour les capteurs avec des noms réels tunisiens"""
    
    print("=" * 80)
    print("🇹🇳 MISE À JOUR DES CAPTEURS - NOMS RÉELS TUNISIENS")
    print("=" * 80)
    print()
    
    # Supprimer les anciens capteurs
    old_capteurs = CapteurTrafic.objects.all()
    print(f"🗑️  Suppression de {old_capteurs.count()} anciens capteurs...")
    old_capteurs.delete()
    print()
    
    # Créer les nouveaux capteurs
    created_count = 0
    for capteur_data in CAPTEURS_TUNISIA:
        try:
            # Récupérer la zone
            zone = ZoneTrafic.objects.get(nom=capteur_data['zone_nom'])
            
            # Créer le capteur
            capteur = CapteurTrafic.objects.create(
                nom=capteur_data['nom'],
                code_capteur=capteur_data['code_capteur'],
                type_capteur=capteur_data['type_capteur'],
                zone_trafic=zone,
                latitude=capteur_data['latitude'],
                longitude=capteur_data['longitude'],
                direction_mesure=capteur_data['direction_mesure'],
                statut=capteur_data['statut'],
                frequence_mesure=capteur_data['frequence_mesure'],
                precision_detection=capteur_data['precision_detection'],
                vitesse_min_detection=capteur_data['vitesse_min_detection'],
                vitesse_max_detection=capteur_data['vitesse_max_detection'],
                date_installation=date.today() - timedelta(days=30),
                fournisseur=capteur_data['fournisseur'],
                modele=capteur_data['modele'],
            )
            
            icon = "📡" if capteur_data['type_capteur'] == 'radar' else "📹" if capteur_data['type_capteur'] == 'camera_ia' else "🔄"
            print(f"✅ {icon} {capteur_data['nom']}")
            created_count += 1
            
        except ZoneTrafic.DoesNotExist:
            print(f"❌ Zone non trouvée: {capteur_data['zone_nom']}")
        except Exception as e:
            print(f"❌ Erreur: {str(e)}")
    
    print()
    print("=" * 80)
    print(f"✅ {created_count} capteurs créés avec succès")
    print("=" * 80)
    print()
    
    # Afficher les statistiques
    radars = CapteurTrafic.objects.filter(type_capteur='radar')
    cameras = CapteurTrafic.objects.filter(type_capteur='camera_ia')
    autres = CapteurTrafic.objects.exclude(type_capteur__in=['radar', 'camera_ia'])
    
    print(f"📡 Radars: {radars.count()}")
    print(f"📹 Caméras: {cameras.count()}")
    print(f"🔄 Autres: {autres.count()}")
    print(f"📊 Total: {CapteurTrafic.objects.count()}")

if __name__ == '__main__':
    update_capteurs()

