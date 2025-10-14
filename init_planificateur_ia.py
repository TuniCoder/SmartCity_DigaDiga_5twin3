#!/usr/bin/env python3
"""
Script d'initialisation des données pour le Planificateur de Trajets IA
"""

import os
import sys
import django

# Configuration Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartcity_core.settings')
django.setup()

from smartcity_app.gestion_trajets.models import (
    TypeVehiculeIntelligent, 
    AlerteTransportTempsReel,
    PreferenceUtilisateurIA
)
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

def initialiser_vehicules():
    """Initialise les types de véhicules intelligents"""
    
    print("🚗 Initialisation des véhicules intelligents...")
    
    vehicules_data = [
        # Transport Public
        {
            'nom': 'Métro',
            'categorie': 'public',
            'icone': 'fas fa-subway',
            'couleur': '#007bff',
            'vitesse_moyenne': 35.0,
            'cout_par_km': 0.1,
            'empreinte_carbone': 25.0,
            'capacite_passagers': 300,
            'accessible_pmr': True,
            'frequence_passage': 8,
            'horaires_service': {
                'debut': '05:30',
                'fin': '01:30',
                'frequence_pointe': 3,
                'frequence_normale': 8
            }
        },
        {
            'nom': 'Bus',
            'categorie': 'public',
            'icone': 'fas fa-bus',
            'couleur': '#28a745',
            'vitesse_moyenne': 18.0,
            'cout_par_km': 0.08,
            'empreinte_carbone': 80.0,
            'capacite_passagers': 50,
            'accessible_pmr': True,
            'frequence_passage': 12,
            'horaires_service': {
                'debut': '06:00',
                'fin': '23:00',
                'frequence_pointe': 5,
                'frequence_normale': 12
            }
        },
        {
            'nom': 'Tramway',
            'categorie': 'public',
            'icone': 'fas fa-train',
            'couleur': '#17a2b8',
            'vitesse_moyenne': 22.0,
            'cout_par_km': 0.09,
            'empreinte_carbone': 30.0,
            'capacite_passagers': 150,
            'accessible_pmr': True,
            'frequence_passage': 10,
            'horaires_service': {
                'debut': '06:00',
                'fin': '00:30',
                'frequence_pointe': 4,
                'frequence_normale': 10
            }
        },
        
        # Transport Privé
        {
            'nom': 'Voiture Personnelle',
            'categorie': 'prive',
            'icone': 'fas fa-car',
            'couleur': '#6f42c1',
            'vitesse_moyenne': 30.0,
            'cout_par_km': 0.35,
            'empreinte_carbone': 120.0,
            'capacite_passagers': 5,
            'accessible_pmr': False,
            'frequence_passage': None,
            'horaires_service': {'disponible': '24h/24'}
        },
        {
            'nom': 'Moto',
            'categorie': 'prive',
            'icone': 'fas fa-motorcycle',
            'couleur': '#fd7e14',
            'vitesse_moyenne': 35.0,
            'cout_par_km': 0.15,
            'empreinte_carbone': 90.0,
            'capacite_passagers': 2,
            'accessible_pmr': False,
            'frequence_passage': None,
            'horaires_service': {'disponible': '24h/24'}
        },
        {
            'nom': 'Taxi',
            'categorie': 'prive',
            'icone': 'fas fa-taxi',
            'couleur': '#ffc107',
            'vitesse_moyenne': 25.0,
            'cout_par_km': 1.5,
            'empreinte_carbone': 150.0,
            'capacite_passagers': 4,
            'accessible_pmr': True,
            'frequence_passage': None,
            'horaires_service': {'disponible': '24h/24'}
        },
        
        # Transport Partagé
        {
            'nom': 'Vélib (Vélo Partagé)',
            'categorie': 'partage',
            'icone': 'fas fa-bicycle',
            'couleur': '#20c997',
            'vitesse_moyenne': 15.0,
            'cout_par_km': 0.05,
            'empreinte_carbone': 0.0,
            'capacite_passagers': 1,
            'accessible_pmr': False,
            'frequence_passage': None,
            'horaires_service': {'disponible': '24h/24'}
        },
        {
            'nom': 'Autolib (Voiture Partagée)',
            'categorie': 'partage',
            'icone': 'fas fa-car-side',
            'couleur': '#e83e8c',
            'vitesse_moyenne': 28.0,
            'cout_par_km': 0.25,
            'empreinte_carbone': 50.0,
            'capacite_passagers': 4,
            'accessible_pmr': True,
            'frequence_passage': None,
            'horaires_service': {'disponible': '24h/24'}
        },
        {
            'nom': 'Trottinette Électrique',
            'categorie': 'partage',
            'icone': 'fas fa-skating',
            'couleur': '#6610f2',
            'vitesse_moyenne': 20.0,
            'cout_par_km': 0.15,
            'empreinte_carbone': 5.0,
            'capacite_passagers': 1,
            'accessible_pmr': False,
            'frequence_passage': None,
            'horaires_service': {'disponible': '06:00-22:00'}
        },
        
        # Transport Actif
        {
            'nom': 'Vélo Personnel',
            'categorie': 'actif',
            'icone': 'fas fa-biking',
            'couleur': '#198754',
            'vitesse_moyenne': 18.0,
            'cout_par_km': 0.0,
            'empreinte_carbone': 0.0,
            'capacite_passagers': 1,
            'accessible_pmr': False,
            'frequence_passage': None,
            'horaires_service': {'disponible': '24h/24'}
        },
        {
            'nom': 'Marche à Pied',
            'categorie': 'actif',
            'icone': 'fas fa-walking',
            'couleur': '#795548',
            'vitesse_moyenne': 5.0,
            'cout_par_km': 0.0,
            'empreinte_carbone': 0.0,
            'capacite_passagers': 1,
            'accessible_pmr': True,
            'frequence_passage': None,
            'horaires_service': {'disponible': '24h/24'}
        },
        {
            'nom': 'Vélo Électrique',
            'categorie': 'actif',
            'icone': 'fas fa-bicycle',
            'couleur': '#0d6efd',
            'vitesse_moyenne': 25.0,
            'cout_par_km': 0.02,
            'empreinte_carbone': 2.0,
            'capacite_passagers': 1,
            'accessible_pmr': False,
            'frequence_passage': None,
            'horaires_service': {'disponible': '24h/24'}
        }
    ]
    
    created_count = 0
    for vehicule_data in vehicules_data:
        vehicule, created = TypeVehiculeIntelligent.objects.get_or_create(
            nom=vehicule_data['nom'],
            defaults=vehicule_data
        )
        if created:
            created_count += 1
            print(f"  ✅ Véhicule créé: {vehicule.nom}")
        else:
            print(f"  ⚠️  Véhicule existant: {vehicule.nom}")
    
    print(f"🎉 {created_count} nouveaux véhicules créés sur {len(vehicules_data)} total")

def initialiser_alertes_demo():
    """Initialise quelques alertes de démonstration"""
    
    print("🚨 Initialisation des alertes de démonstration...")
    
    # Supprimer les anciennes alertes de démo
    AlerteTransportTempsReel.objects.filter(source='Demo').delete()
    
    maintenant = timezone.now()
    
    alertes_data = [
        {
            'type_alerte': 'retard',
            'severite': 'attention',
            'titre': 'Retard Ligne de Bus 15',
            'description': 'Retards de 5-8 minutes dus à un accident sur l\'avenue principale.',
            'ligne_transport': 'Bus 15',
            'zone_geographique': 'Centre-ville',
            'date_debut': maintenant - timedelta(minutes=30),
            'date_fin': maintenant + timedelta(hours=1),
            'source': 'Demo'
        },
        {
            'type_alerte': 'perturbation',
            'severite': 'important',
            'titre': 'Travaux Station Métro République',
            'description': 'Station partiellement fermée, utiliser la sortie nord uniquement.',
            'ligne_transport': 'Métro Ligne 1',
            'zone_geographique': 'République',
            'date_debut': maintenant - timedelta(hours=2),
            'date_fin': maintenant + timedelta(days=3),
            'source': 'Demo'
        },
        {
            'type_alerte': 'circulation',
            'severite': 'attention',
            'titre': 'Circulation Dense - Pont Neuf',
            'description': 'Circulation ralentie due à un événement sportif.',
            'zone_geographique': 'Pont Neuf - Centre historique',
            'date_debut': maintenant - timedelta(minutes=45),
            'date_fin': maintenant + timedelta(hours=2),
            'source': 'Demo'
        },
        {
            'type_alerte': 'info',
            'severite': 'info',
            'titre': 'Nouveau service Vélib+',
            'description': 'Nouvelles stations de vélos électriques disponibles dans le quartier universitaire.',
            'zone_geographique': 'Quartier Universitaire',
            'date_debut': maintenant,
            'date_fin': maintenant + timedelta(days=7),
            'source': 'Demo'
        },
        {
            'type_alerte': 'meteo',
            'severite': 'attention',
            'titre': 'Conditions Météo Défavorables',
            'description': 'Pluie modérée prévue, trajets à vélo et à pied impactés.',
            'date_debut': maintenant + timedelta(hours=1),
            'date_fin': maintenant + timedelta(hours=4),
            'source': 'Demo'
        }
    ]
    
    for alerte_data in alertes_data:
        # Récupérer le véhicule concerné si spécifié
        vehicule = None
        if 'ligne_transport' in alerte_data:
            ligne = alerte_data['ligne_transport']
            if 'Bus' in ligne:
                vehicule = TypeVehiculeIntelligent.objects.filter(nom='Bus').first()
            elif 'Métro' in ligne:
                vehicule = TypeVehiculeIntelligent.objects.filter(nom='Métro').first()
        
        if vehicule:
            alerte_data['vehicule_concerne'] = vehicule
        
        alerte = AlerteTransportTempsReel.objects.create(**alerte_data)
        print(f"  ✅ Alerte créée: {alerte.titre}")
    
    print(f"🎉 {len(alertes_data)} alertes de démonstration créées")

def initialiser_preferences_demo():
    """Initialise les préférences pour les utilisateurs existants"""
    
    print("⚙️ Initialisation des préférences utilisateur...")
    
    users = User.objects.all()
    created_count = 0
    
    for user in users:
        preferences, created = PreferenceUtilisateurIA.objects.get_or_create(
            utilisateur=user,
            defaults={
                'priorite_defaut': 'rapidite',
                'budget_defaut': 15.0,
                'duree_max_defaut': 45,
                'recevoir_alertes': True,
                'avance_notification': 10,
                'apprentissage_actif': True,
                'lieux_favoris': [
                    {
                        'nom': 'Domicile',
                        'adresse': 'Adresse personnelle',
                        'lat': 48.8566,
                        'lng': 2.3522
                    },
                    {
                        'nom': 'Travail/Études',
                        'adresse': 'Lieu de travail',
                        'lat': 48.8606,
                        'lng': 2.3376
                    }
                ]
            }
        )
        
        if created:
            # Ajouter quelques véhicules favoris par défaut
            vehicules_favoris = TypeVehiculeIntelligent.objects.filter(
                nom__in=['Métro', 'Bus', 'Vélo Personnel']
            )
            preferences.vehicules_favoris.set(vehicules_favoris)
            
            created_count += 1
            print(f"  ✅ Préférences créées pour: {user.username}")
        else:
            print(f"  ⚠️  Préférences existantes pour: {user.username}")
    
    print(f"🎉 {created_count} nouvelles préférences créées")

def main():
    """Fonction principale d'initialisation"""
    
    print("\n" + "="*60)
    print("🚀 INITIALISATION DU PLANIFICATEUR DE TRAJETS IA")
    print("="*60)
    
    try:
        initialiser_vehicules()
        print()
        
        initialiser_alertes_demo()
        print()
        
        initialiser_preferences_demo()
        print()
        
        print("="*60)
        print("✅ INITIALISATION TERMINÉE AVEC SUCCÈS!")
        print("🎯 Le planificateur de trajets IA est maintenant prêt à utiliser")
        print()
        print("📝 Prochaines étapes:")
        print("   1. Démarrer le serveur: python manage.py runserver")
        print("   2. Accéder au planificateur: /trajets/planificateur/")
        print("   3. Tester les différents types de véhicules")
        print("   4. Explorer les fonctionnalités temps réel")
        print("="*60)
        
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)