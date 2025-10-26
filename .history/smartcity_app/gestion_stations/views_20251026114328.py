from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect
from django.views.decorators.http import require_http_methods
from ..ontology_manager.rdf_utils import rdf_manager
import json

@login_required
def index_stations(request):
    """Page d'accueil de la gestion des stations"""
    context = {
        'page_title': 'Gestion des Stations - SmartCity',
        'module_name': 'Gestion des Stations',
        'module_description': 'Gérez l\'infrastructure des stations de transport public',
        'coming_soon': True,
        'features_planned': [
            {
                'icon': 'bi-geo-alt-fill',
                'title': 'Inventaire des Stations',
                'description': 'Gestion complète de toutes les stations de transport',
                'status': 'planned'
            },
            {
                'icon': 'bi-tools',
                'title': 'Gestion des Équipements',
                'description': 'Suivi des ascenseurs, escalators et équipements',
                'status': 'planned'
            },
            {
                'icon': 'bi-activity',
                'title': 'Monitoring Temps Réel',
                'description': 'Capteurs IoT et affluence en direct',
                'status': 'planned'
            },
            {
                'icon': 'bi-universal-access',
                'title': 'Accessibilité PMR',
                'description': 'Services pour personnes à mobilité réduite',
                'status': 'planned'
            },
            {
                'icon': 'bi-map',
                'title': 'Cartes Interactives',
                'description': 'Visualisation géographique des stations',
                'status': 'planned'
            },
            {
                'icon': 'bi-graph-up',
                'title': 'Analytics & Prédictions',
                'description': 'IA pour optimiser les flux de passagers',
                'status': 'planned'
            }
        ],
        'team_member': 'À définir',
        'contact_info': 'Voir équipe Trajets pour coordination'
    }
    return render(request, 'coming_soon.html', context)

@login_required
def dashboard_stations(request):
    """Dashboard de gestion des stations"""
    return index_stations(request)

@login_required
def liste_stations(request):
    """Liste des stations"""
    stations = rdf_manager.get_stations()
    return render(request, 'gestion_stations/liste_stations.html', {
        'stations': stations
    })

@login_required
def ajouter_station(request):
    """Ajouter une nouvelle station"""
    if request.method == 'POST':
        # Récupérer les données du formulaire
        nom = request.POST.get('nom')
        type_station = request.POST.get('type')
        latitude = float(request.POST.get('latitude'))
        longitude = float(request.POST.get('longitude'))
        adresse = request.POST.get('adresse')
        capacite = int(request.POST.get('capacite'))
        heures_ouverture = request.POST.get('heures_ouverture')
        
        # Créer la station dans le RDF
        station_data = {
            'nom': nom,
            'type': type_station,
            'latitude': latitude,
            'longitude': longitude,
            'adresse': adresse,
            'capacite': capacite,
            'heures_ouverture': heures_ouverture
        }
        rdf_manager.add_station(station_data)
        
        messages.success(request, f'Station {nom} ajoutée avec succès !')
        return redirect('liste_stations')
        
    return render(request, 'gestion_stations/ajouter_station.html')

@login_required
def modifier_station(request, station_id):
    """Modifier une station existante"""
    return index_stations(request)

@login_required
def details_station(request, station_id):
    """Détails d'une station"""
    return index_stations(request)

@login_required
def monitoring_stations(request):
    """Monitoring temps réel des stations"""
    return index_stations(request)

@login_required
def gestion_equipements(request):
    """Gestion des équipements des stations"""
    return index_stations(request)