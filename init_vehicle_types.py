#!/usr/bin/env python3
"""
Script d'initialisation des types de véhicules depuis l'ontologie RDF
"""

import os
import sys
import django

# Configuration Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartcity_core.settings')
django.setup()

from smartcity_app.gestion_vehicules.models import TypeVehicule
from django.db import transaction

def initialiser_types_vehicules():
    """Initialise les types de véhicules depuis l'ontologie RDF"""
    
    print("Initialisation des types de vehicules depuis l'ontologie RDF...")
    
    # Types de véhicules depuis l'ontologie RDF
    vehicules_data = [
        {
            'nom': 'Vélo',
            'categorie': 'vehicule_partage',
            'mode_propulsion': 'musculaire',
            'capacite_passagers': 1,
            'vitesse_max': 25.0,
            'autonomie': 0.0,  # Sans limite si le cycliste pédale
            'emission_co2': 0.0,
            'niveau_bruit': 40,
            'accessible_pmr': False,
            'description': 'Vélo à pédales pour déplacements urbains'
        },
        {
            'nom': 'Vélo Électrique',
            'categorie': 'vehicule_partage',
            'mode_propulsion': 'electrique',
            'capacite_passagers': 1,
            'vitesse_max': 25.0,
            'autonomie': 50.0,
            'emission_co2': 0.0,
            'niveau_bruit': 35,
            'accessible_pmr': False,
            'description': 'Vélo avec assistance électrique (VAE)'
        },
        {
            'nom': 'Voiture',
            'categorie': 'vehicule_prive',
            'mode_propulsion': 'essence',
            'capacite_passagers': 5,
            'vitesse_max': 180.0,
            'autonomie': 800.0,
            'emission_co2': 120.0,
            'niveau_bruit': 65,
            'accessible_pmr': True,
            'description': 'Véhicule automobile à quatre roues'
        },
        {
            'nom': 'Moto',
            'categorie': 'vehicule_prive',
            'mode_propulsion': 'essence',
            'capacite_passagers': 2,
            'vitesse_max': 200.0,
            'autonomie': 400.0,
            'emission_co2': 95.0,
            'niveau_bruit': 75,
            'accessible_pmr': False,
            'description': 'Véhicule à deux roues motorisé'
        },
        {
            'nom': 'Scooter',
            'categorie': 'vehicule_partage',
            'mode_propulsion': 'essence',
            'capacite_passagers': 2,
            'vitesse_max': 90.0,
            'autonomie': 250.0,
            'emission_co2': 70.0,
            'niveau_bruit': 70,
            'accessible_pmr': False,
            'description': 'Scooter à essence pour déplacements urbains'
        },
        {
            'nom': 'Trottinette',
            'categorie': 'vehicule_partage',
            'mode_propulsion': 'musculaire',
            'capacite_passagers': 1,
            'vitesse_max': 15.0,
            'autonomie': 0.0,
            'emission_co2': 0.0,
            'niveau_bruit': 30,
            'accessible_pmr': False,
            'description': 'Trottinette classique à propulsion manuelle'
        },
        {
            'nom': 'Trottinette Électrique',
            'categorie': 'vehicule_partage',
            'mode_propulsion': 'electrique',
            'capacite_passagers': 1,
            'vitesse_max': 25.0,
            'autonomie': 30.0,
            'emission_co2': 0.0,
            'niveau_bruit': 35,
            'accessible_pmr': False,
            'description': 'Trottinette avec assistance électrique'
        },
        {
            'nom': 'Camionnette',
            'categorie': 'vehicule_service',
            'mode_propulsion': 'diesel',
            'capacite_passagers': 3,
            'vitesse_max': 120.0,
            'autonomie': 800.0,
            'emission_co2': 150.0,
            'niveau_bruit': 70,
            'accessible_pmr': False,
            'description': 'Petit véhicule utilitaire pour transport de marchandises'
        },
        {
            'nom': 'Bus',
            'categorie': 'transport_public',
            'mode_propulsion': 'diesel',
            'capacite_passagers': 50,
            'vitesse_max': 80.0,
            'autonomie': 600.0,
            'emission_co2': 80.0,
            'niveau_bruit': 75,
            'accessible_pmr': True,
            'equipements_accessibilite': 'Rampes, espaces PMR',
            'description': 'Véhicule de transport public de grande capacité'
        },
        {
            'nom': 'Tramway',
            'categorie': 'transport_public',
            'mode_propulsion': 'electrique',
            'capacite_passagers': 200,
            'vitesse_max': 70.0,
            'autonomie': 0.0,  # Alimenté par caténaire
            'emission_co2': 0.0,
            'niveau_bruit': 60,
            'accessible_pmr': True,
            'equipements_accessibilite': 'Quai à niveau, rampes',
            'description': 'Véhicule ferroviaire urbain électrique'
        },
        {
            'nom': 'Métro',
            'categorie': 'transport_public',
            'mode_propulsion': 'electrique',
            'capacite_passagers': 600,
            'vitesse_max': 80.0,
            'autonomie': 0.0,  # Alimenté par caténaire
            'emission_co2': 0.0,
            'niveau_bruit': 70,
            'accessible_pmr': True,
            'equipements_accessibilite': 'Ascenseurs, quai à niveau',
            'description': 'Transport ferroviaire souterrain rapide'
        }
    ]
    
    # Créer ou mettre à jour chaque type de véhicule
    with transaction.atomic():
        for vehicule_data in vehicules_data:
            vehicule, created = TypeVehicule.objects.update_or_create(
                nom=vehicule_data['nom'],
                defaults=vehicule_data
            )
            
            if created:
                print(f"  [OK] Cree: {vehicule.nom}")
            else:
                print(f"  [UPDATE] Mis a jour: {vehicule.nom}")
    
    print(f"\n{len(vehicules_data)} types de vehicules initialises avec succes!")

if __name__ == '__main__':
    initialiser_types_vehicules()

