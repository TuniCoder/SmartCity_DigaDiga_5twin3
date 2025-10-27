#!/usr/bin/env python3
"""
Script d'initialisation pour le module Gestion de Location - SmartCity
Domaine : 🚗 Location de Véhicules Intelligente

Ce script initialise :
- Les types de véhicules disponibles
- Des véhicules d'exemple
- Les options et services
- Les données de test
"""

import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartcity_core.settings')
django.setup()

from django.contrib.auth.models import User
from smartcity_app.gestion_location.models import (
    TypeLocation,
    VehiculeLocation,
    OptionLocation,
    ServiceLocation,
    Location
)
from smartcity_app.gestion_utilisateurs.models import ProfilUtilisateur


def creer_types_location():
    """Crée les types de véhicules disponibles"""
    print("[VEHICULES] Creation des types de vehicules...")
    
    types_data = [
        {
            'nom': 'Voiture Économique',
            'categorie': 'voiture',
            'description': 'Voiture compacte idéale pour la ville',
            'icone': 'fas fa-car',
            'couleur': '#28a745',
            'capacite_passagers': 4,
            'capacite_bagages': 2,
            'vitesse_maximale': 120,
            'autonomie_km': 500,
            'prix_heure': Decimal('8.50'),
            'prix_jour': Decimal('45.00'),
            'prix_km': Decimal('0.15'),
            'caution_requise': Decimal('200.00'),
            'accessible_pmr': False,
            'permis_requis': 'B',
            'age_minimum': 21,
            'equipements': ['climatisation', 'radio', 'bluetooth'],
            'emission_co2_par_km': 120,
            'consommation_moyenne': 6.5,
            'nombre_total': 15,
        },
        {
            'nom': 'Voiture Électrique',
            'categorie': 'voiture',
            'description': 'Véhicule électrique écologique',
            'icone': 'fas fa-car',
            'couleur': '#17a2b8',
            'capacite_passagers': 5,
            'capacite_bagages': 3,
            'vitesse_maximale': 140,
            'autonomie_km': 300,
            'prix_heure': Decimal('12.00'),
            'prix_jour': Decimal('65.00'),
            'prix_km': Decimal('0.20'),
            'caution_requise': Decimal('300.00'),
            'accessible_pmr': False,
            'permis_requis': 'B',
            'age_minimum': 21,
            'equipements': ['climatisation', 'gps', 'bluetooth', 'chargeur'],
            'emission_co2_par_km': 0,
            'consommation_moyenne': 0,
            'nombre_total': 8,
        },
        {
            'nom': 'Vélo Électrique',
            'categorie': 'velo',
            'description': 'Vélo à assistance électrique',
            'icone': 'fas fa-bicycle',
            'couleur': '#6f42c1',
            'capacite_passagers': 1,
            'capacite_bagages': 1,
            'vitesse_maximale': 25,
            'autonomie_km': 60,
            'prix_heure': Decimal('3.00'),
            'prix_jour': Decimal('15.00'),
            'prix_km': Decimal('0.05'),
            'caution_requise': Decimal('50.00'),
            'accessible_pmr': False,
            'permis_requis': 'Aucun',
            'age_minimum': 16,
            'equipements': ['casque', 'antivol', 'panier'],
            'emission_co2_par_km': 0,
            'consommation_moyenne': 0,
            'nombre_total': 25,
        },
        {
            'nom': 'Trottinette Électrique',
            'categorie': 'trottinette',
            'description': 'Trottinette électrique urbaine',
            'icone': 'fas fa-scooter',
            'couleur': '#fd7e14',
            'capacite_passagers': 1,
            'capacite_bagages': 0,
            'vitesse_maximale': 20,
            'autonomie_km': 25,
            'prix_heure': Decimal('2.50'),
            'prix_jour': Decimal('12.00'),
            'prix_km': Decimal('0.10'),
            'caution_requise': Decimal('30.00'),
            'accessible_pmr': False,
            'permis_requis': 'Aucun',
            'age_minimum': 14,
            'equipements': ['casque', 'antivol'],
            'emission_co2_par_km': 0,
            'consommation_moyenne': 0,
            'nombre_total': 30,
        },
        {
            'nom': 'Scooter 125cc',
            'categorie': 'scooter',
            'description': 'Scooter urbain pratique',
            'icone': 'fas fa-motorcycle',
            'couleur': '#dc3545',
            'capacite_passagers': 2,
            'capacite_bagages': 1,
            'vitesse_maximale': 90,
            'autonomie_km': 200,
            'prix_heure': Decimal('6.00'),
            'prix_jour': Decimal('35.00'),
            'prix_km': Decimal('0.12'),
            'caution_requise': Decimal('150.00'),
            'accessible_pmr': False,
            'permis_requis': 'A1',
            'age_minimum': 18,
            'equipements': ['casque', 'gants', 'topcase'],
            'emission_co2_par_km': 80,
            'consommation_moyenne': 3.5,
            'nombre_total': 12,
        },
        {
            'nom': 'Voiture de Luxe',
            'categorie': 'luxe',
            'description': 'Véhicule haut de gamme',
            'icone': 'fas fa-car',
            'couleur': '#6c757d',
            'capacite_passagers': 5,
            'capacite_bagages': 4,
            'vitesse_maximale': 200,
            'autonomie_km': 600,
            'prix_heure': Decimal('25.00'),
            'prix_jour': Decimal('150.00'),
            'prix_km': Decimal('0.30'),
            'caution_requise': Decimal('500.00'),
            'accessible_pmr': False,
            'permis_requis': 'B',
            'age_minimum': 25,
            'equipements': ['climatisation', 'gps', 'bluetooth', 'cuir', 'toit ouvrant'],
            'emission_co2_par_km': 180,
            'consommation_moyenne': 8.5,
            'nombre_total': 5,
        },
    ]
    
    types_crees = []
    for type_data in types_data:
        type_location, created = TypeLocation.objects.get_or_create(
            nom=type_data['nom'],
            defaults=type_data
        )
        if created:
            print(f"  [OK] {type_location.nom} cree")
        else:
            print(f"  [EXISTE] {type_location.nom} existe deja")
        types_crees.append(type_location)
    
    return types_crees

def creer_vehicules_exemple(types_location):
    """Crée des véhicules d'exemple pour chaque type"""
    print("[VEHICULES] Creation des vehicules d'exemple...")
    
    stations = [
        'Station Centre-Ville',
        'Station Aéroport',
        'Station Gare Centrale',
        'Station Université',
        'Station Shopping Mall',
        'Station Parc Central',
    ]
    
    vehicules_crees = []
    for i, type_location in enumerate(types_location):
        for j in range(min(3, type_location.nombre_total)):  # Max 3 véhicules par type
            numero_id = f"{type_location.categorie.upper()}{i+1:02d}{j+1:02d}"
            
            vehicule_data = {
                'type_location': type_location,
                'numero_identification': numero_id,
                'immatriculation': f"SM{numero_id}",
                'station_location': stations[j % len(stations)],
                'latitude': 36.8065 + (j * 0.01),
                'longitude': 10.1815 + (j * 0.01),
                'adresse_complete': f"{stations[j % len(stations)]}, Tunis, Tunisie",
                'statut': 'disponible',
                'niveau_carburant': 85 + (j * 5),
                'kilometrage_total': 15000 + (j * 2000),
                'annee_fabrication': 2020 + (j % 3),
                'couleur': ['Blanc', 'Noir', 'Gris', 'Rouge', 'Bleu'][j % 5],
                'numero_serie': f"SN{numero_id}",
                'derniere_maintenance': datetime.now() - timedelta(days=30 + j * 10),
                'prochaine_maintenance': datetime.now() + timedelta(days=60 + j * 15),
                'numero_assurance': f"ASS{numero_id}",
                'date_expiration_assurance': datetime.now() + timedelta(days=365),
                'controle_technique': datetime.now() + timedelta(days=180),
            }
            
            vehicule, created = VehiculeLocation.objects.get_or_create(
                numero_identification=numero_id,
                defaults=vehicule_data
            )
            
            if created:
                print(f"  [OK] {vehicule.numero_identification} - {vehicule.type_location.nom}")
            else:
                print(f"  [EXISTE] {vehicule.numero_identification} existe deja")
            
            vehicules_crees.append(vehicule)
    
    return vehicules_crees

def creer_options_services():
    """Crée les options et services disponibles"""
    print("[OPTIONS] Creation des options et services...")
    
    # Options
    options_data = [
        {
            'nom': 'GPS Navigation',
            'categorie': 'navigation',
            'description': 'Système de navigation GPS intégré',
            'prix_unitaire': Decimal('5.00'),
            'unite_tarification': 'location',
            'icone': 'fas fa-map-marked-alt',
            'couleur': '#17a2b8',
        },
        {
            'nom': 'Siège Bébé',
            'categorie': 'confort',
            'description': 'Siège auto pour enfant (0-4 ans)',
            'prix_unitaire': Decimal('8.00'),
            'unite_tarification': 'location',
            'icone': 'fas fa-baby',
            'couleur': '#28a745',
        },
        {
            'nom': 'Rehausseur',
            'categorie': 'confort',
            'description': 'Rehausseur pour enfant (4-12 ans)',
            'prix_unitaire': Decimal('5.00'),
            'unite_tarification': 'location',
            'icone': 'fas fa-child',
            'couleur': '#ffc107',
        },
        {
            'nom': 'Chaîne Neige',
            'categorie': 'securite',
            'description': 'Chaînes à neige pour conditions hivernales',
            'prix_unitaire': Decimal('15.00'),
            'unite_tarification': 'location',
            'icone': 'fas fa-snowflake',
            'couleur': '#6c757d',
        },
        {
            'nom': 'Coffre de Toit',
            'categorie': 'bagages',
            'description': 'Coffre de toit pour bagages supplémentaires',
            'prix_unitaire': Decimal('12.00'),
            'unite_tarification': 'jour',
            'icone': 'fas fa-box',
            'couleur': '#fd7e14',
        },
        {
            'nom': 'Conducteur Additionnel',
            'categorie': 'confort',
            'description': "Ajout d'un conducteur supplémentaire",
            'prix_unitaire': Decimal('10.00'),
            'unite_tarification': 'location',
            'icone': 'fas fa-user-plus',
            'couleur': '#6f42c1',
        },
    ]
    
    options_crees = []
    for option_data in options_data:
        option, created = OptionLocation.objects.get_or_create(
            nom=option_data['nom'],
            defaults=option_data
        )
        if created:
            print(f"  [OK] Option: {option.nom}")
        else:
            print(f"  [EXISTE] Option: {option.nom} existe deja")
        options_crees.append(option)
    
    # Services
    services_data = [
        {
            'nom': 'Livraison à Domicile',
            'description': 'Livraison du véhicule à votre adresse',
            'prix_fixe': Decimal('15.00'),
            'prix_variable': Decimal('0.50'),
            'unite_variable': 'km',
            'conditions_particulieres': 'Minimum 5km, maximum 20km du centre',
        },
        {
            'nom': 'Récupération Véhicule',
            'description': 'Récupération du véhicule à votre adresse',
            'prix_fixe': Decimal('12.00'),
            'prix_variable': Decimal('0.40'),
            'unite_variable': 'km',
            'conditions_particulieres': 'Minimum 5km, maximum 20km du centre',
        },
        {
            'nom': 'Nettoyage Intérieur',
            'description': "Nettoyage complet de l'intérieur du véhicule",
            'prix_fixe': Decimal('25.00'),
            'conditions_particulieres': 'Service disponible uniquement au retour',
        },
        {
            'nom': "Plein d'Essence",
            'description': "Plein d'essence avant la location",
            'prix_fixe': Decimal('0.00'),
            'prix_variable': Decimal('1.20'),
            'unite_variable': 'L',
            'conditions_particulieres': 'Prix au litre en vigueur',
        },
        {
            'nom': 'Assurance Premium',
            'description': 'Assurance tous risques avec franchise réduite',
            'prix_fixe': Decimal('20.00'),
            'conditions_particulieres': 'Franchise réduite à 200€',
        },
    ]
    
    services_crees = []
    for service_data in services_data:
        service, created = ServiceLocation.objects.get_or_create(
            nom=service_data['nom'],
            defaults=service_data
        )
        if created:
            print(f"  [OK] Service: {service.nom}")
        else:
            print(f"  [EXISTE] Service: {service.nom} existe deja")
        services_crees.append(service)
    
    return options_crees, services_crees

def creer_reservations_exemple(vehicules_crees):
    """Crée quelques réservations d'exemple"""
    print("[RESERVATIONS] Creation des reservations d'exemple...")
    
    # Récupérer ou créer un utilisateur de test
    try:
        user = User.objects.get(username='user')
    except User.DoesNotExist:
        user = User.objects.create_user(
            username='user',
            email='user@smartcity.com',
            password='password123',
            first_name='Utilisateur',
            last_name='Test'
        )
        print(f"  [OK] Utilisateur de test cree: {user.username}")
    
    # Créer quelques réservations
    reservations_data = [
        {
            'vehicule': vehicules_crees[0],
            'date_debut': datetime.now() + timedelta(days=1),
            'date_fin': datetime.now() + timedelta(days=1, hours=4),
            'lieu_prise': 'Station Centre-Ville',
            'lieu_retour': 'Station Centre-Ville',
            'conducteur_principal': f'{user.first_name} {user.last_name}',
            'statut': 'en_attente',
        },
        {
            'vehicule': vehicules_crees[1],
            'date_debut': datetime.now() - timedelta(days=2),
            'date_fin': datetime.now() - timedelta(days=1),
            'lieu_prise': 'Station Aéroport',
            'lieu_retour': 'Station Aéroport',
            'conducteur_principal': f'{user.first_name} {user.last_name}',
            'statut': 'terminee',
            'note_experience': 5,
        },
        {
            'vehicule': vehicules_crees[2],
            'date_debut': datetime.now() + timedelta(days=3),
            'date_fin': datetime.now() + timedelta(days=5),
            'lieu_prise': 'Station Université',
            'lieu_retour': 'Station Université',
            'conducteur_principal': f'{user.first_name} {user.last_name}',
            'statut': 'confirmee',
        },
    ]
    
    reservations_crees = []
    for i, res_data in enumerate(reservations_data):
        numero_location = f"LOC{datetime.now().strftime('%Y%m%d')}{i+1:03d}"
        
        reservation_data = {
            'utilisateur': user,
            'numero_location': numero_location,
            'type_location': 'ponctuelle',
            'prix_heure': res_data['vehicule'].type_location.prix_heure,
            'prix_total_calcule': float(res_data['vehicule'].type_location.prix_heure) * 4,
            'prix_total_final': float(res_data['vehicule'].type_location.prix_heure) * 4,
            'caution_payee': res_data['vehicule'].type_location.caution_requise,
            'assurance_comprise': True,
            'franchise_assurance': 500.0,
            'cree_par_admin': False,
            **res_data
        }
        
        reservation, created = Location.objects.get_or_create(
            numero_location=numero_location,
            defaults=reservation_data
        )
        
        if created:
            print(f"  [OK] Reservation: {reservation.numero_location}")
        else:
            print(f"  [EXISTE] Reservation: {reservation.numero_location} existe deja")
        
        reservations_crees.append(reservation)
    
    return reservations_crees

def main():
    """Fonction principale d'initialisation"""
    print("=== INITIALISATION MODULE GESTION DE LOCATION - SMARTCITY ===")
    print("=" * 60)
    
    try:
        # Créer les types de véhicules
        types_location = creer_types_location()
        print()
        
        # Créer les véhicules d'exemple
        vehicules_crees = creer_vehicules_exemple(types_location)
        print()
        
        # Créer les options et services
        options_crees, services_crees = creer_options_services()
        print()
        
        # Créer les réservations d'exemple
        reservations_crees = creer_reservations_exemple(vehicules_crees)
        print()
        
        # Résumé
        print("[RESUME] Resume de l'initialisation:")
        print(f"  • {len(types_location)} types de vehicules")
        print(f"  • {len(vehicules_crees)} vehicules crees")
        print(f"  • {len(options_crees)} options disponibles")
        print(f"  • {len(services_crees)} services disponibles")
        print(f"  • {len(reservations_crees)} reservations d'exemple")
        print()
        print("[SUCCES] Initialisation terminee avec succes!")
        print()
        print("[ACCES] Acces au module:")
        print("  • Dashboard: http://localhost:8000/location/")
        print("  • Recherche: http://localhost:8000/location/rechercher/")
        print("  • Admin: http://localhost:8000/location/admin/")
        
    except Exception as e:
        print(f"[ERREUR] Erreur lors de l'initialisation: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)