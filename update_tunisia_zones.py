#!/usr/bin/env python
"""
Script pour mettre à jour les zones avec des noms réels tunisiens
et mettre à jour les capteurs correspondants
"""

import os
import django
from datetime import date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartcity_core.settings')
django.setup()

from smartcity_app.gestion_trafic.models import ZoneTrafic, CapteurTrafic

# Zones réelles en Tunisie avec leurs coordonnées
TUNISIA_ZONES = [
    {
        'nom': 'Centre-Ville Tunis',
        'type_zone': 'centre_ville',
        'description': 'Centre-ville de Tunis - Avenue Habib Bourguiba et alentours',
        'coordonnees_zone': {
            'type': 'Polygon',
            'coordinates': [[[10.1815, 36.8065], [10.1900, 36.8065], [10.1900, 36.8150], [10.1815, 36.8150], [10.1815, 36.8065]]]
        },
        'vitesse_limite': 50,
        'nombre_voies': 4,
        'sens_circulation': 'bidirectionnel',
    },
    {
        'nom': 'Bab Saadoun - Tunis',
        'type_zone': 'centre_ville',
        'description': 'Quartier Bab Saadoun - Centre historique',
        'coordonnees_zone': {
            'type': 'Polygon',
            'coordinates': [[[10.1956, 36.7994], [10.2050, 36.7994], [10.2050, 36.8080], [10.1956, 36.8080], [10.1956, 36.7994]]]
        },
        'vitesse_limite': 40,
        'nombre_voies': 2,
        'sens_circulation': 'bidirectionnel',
    },
    {
        'nom': 'Autoroute A1 - Tunis Nord',
        'type_zone': 'autoroute',
        'description': 'Autoroute A1 - Tunis vers Sfax (section Nord)',
        'coordonnees_zone': {
            'type': 'Polygon',
            'coordinates': [[[10.2000, 36.8500], [10.2100, 36.8500], [10.2100, 36.8600], [10.2000, 36.8600], [10.2000, 36.8500]]]
        },
        'vitesse_limite': 110,
        'nombre_voies': 4,
        'sens_circulation': 'bidirectionnel',
    },
    {
        'nom': 'Rocade Nord Tunis',
        'type_zone': 'rocade',
        'description': 'Rocade Nord de Tunis - Contournement',
        'coordonnees_zone': {
            'type': 'Polygon',
            'coordinates': [[[10.1500, 36.8500], [10.2500, 36.8500], [10.2500, 36.9000], [10.1500, 36.9000], [10.1500, 36.8500]]]
        },
        'vitesse_limite': 90,
        'nombre_voies': 3,
        'sens_circulation': 'bidirectionnel',
    },
    {
        'nom': 'Zone Industrielle Sfax',
        'type_zone': 'zone_industrielle',
        'description': 'Zone industrielle de Sfax - Secteur manufacturier',
        'coordonnees_zone': {
            'type': 'Polygon',
            'coordinates': [[[10.7603, 34.7405], [10.7700, 34.7405], [10.7700, 34.7500], [10.7603, 34.7500], [10.7603, 34.7405]]]
        },
        'vitesse_limite': 60,
        'nombre_voies': 2,
        'sens_circulation': 'bidirectionnel',
    },
    {
        'nom': 'Centre-Ville Sfax',
        'type_zone': 'centre_ville',
        'description': 'Centre-ville de Sfax - Rue Bourguiba',
        'coordonnees_zone': {
            'type': 'Polygon',
            'coordinates': [[[10.7603, 34.7405], [10.7700, 34.7405], [10.7700, 34.7500], [10.7603, 34.7500], [10.7603, 34.7405]]]
        },
        'vitesse_limite': 50,
        'nombre_voies': 3,
        'sens_circulation': 'bidirectionnel',
    },
    {
        'nom': 'Corniche Sousse',
        'type_zone': 'zone_residentielle',
        'description': 'Corniche de Sousse - Zone touristique et résidentielle',
        'coordonnees_zone': {
            'type': 'Polygon',
            'coordinates': [[[10.6369, 35.8256], [10.6450, 35.8256], [10.6450, 35.8350], [10.6369, 35.8350], [10.6369, 35.8256]]]
        },
        'vitesse_limite': 40,
        'nombre_voies': 2,
        'sens_circulation': 'bidirectionnel',
    },
    {
        'nom': 'Autoroute A1 - Sousse',
        'type_zone': 'autoroute',
        'description': 'Autoroute A1 - Section Sousse',
        'coordonnees_zone': {
            'type': 'Polygon',
            'coordinates': [[[10.6369, 35.8256], [10.6450, 35.8256], [10.6450, 35.8350], [10.6369, 35.8350], [10.6369, 35.8256]]]
        },
        'vitesse_limite': 110,
        'nombre_voies': 4,
        'sens_circulation': 'bidirectionnel',
    },
    {
        'nom': 'Centre-Ville Kairouan',
        'type_zone': 'centre_ville',
        'description': 'Centre-ville de Kairouan - Médina',
        'coordonnees_zone': {
            'type': 'Polygon',
            'coordinates': [[[9.9197, 35.6781], [9.9300, 35.6781], [9.9300, 35.6880], [9.9197, 35.6880], [9.9197, 35.6781]]]
        },
        'vitesse_limite': 40,
        'nombre_voies': 2,
        'sens_circulation': 'bidirectionnel',
    },
    {
        'nom': 'Autoroute A3 - Kairouan',
        'type_zone': 'autoroute',
        'description': 'Autoroute A3 - Section Kairouan',
        'coordonnees_zone': {
            'type': 'Polygon',
            'coordinates': [[[9.9197, 35.6781], [9.9300, 35.6781], [9.9300, 35.6880], [9.9197, 35.6880], [9.9197, 35.6781]]]
        },
        'vitesse_limite': 110,
        'nombre_voies': 4,
        'sens_circulation': 'bidirectionnel',
    },
]

def update_zones():
    """Mettre à jour les zones avec des noms réels tunisiens"""
    
    print("=" * 80)
    print("🇹🇳 MISE À JOUR DES ZONES - NOMS RÉELS TUNISIENS")
    print("=" * 80)
    print()
    
    # Supprimer les anciennes zones
    old_zones = ZoneTrafic.objects.all()
    print(f"🗑️  Suppression de {old_zones.count()} anciennes zones...")
    old_zones.delete()
    print()
    
    # Créer les nouvelles zones
    created_zones = []
    for zone_data in TUNISIA_ZONES:
        try:
            zone = ZoneTrafic.objects.create(
                nom=zone_data['nom'],
                type_zone=zone_data['type_zone'],
                description=zone_data['description'],
                coordonnees_zone=zone_data['coordonnees_zone'],
                vitesse_limite=zone_data['vitesse_limite'],
                nombre_voies=zone_data['nombre_voies'],
                sens_circulation=zone_data['sens_circulation'],
            )
            created_zones.append(zone)
            print(f"✅ Zone créée: {zone.nom} ({zone.get_type_zone_display()})")
        except Exception as e:
            print(f"❌ Erreur lors de la création de {zone_data['nom']}: {str(e)}")
    
    print()
    print("=" * 80)
    print(f"✅ {len(created_zones)} zones créées avec succès")
    print("=" * 80)
    print()
    
    # Afficher les zones créées
    print("📍 Zones Créées:")
    for zone in created_zones:
        print(f"   • {zone.nom} ({zone.get_type_zone_display()})")
    
    return created_zones

if __name__ == '__main__':
    update_zones()

