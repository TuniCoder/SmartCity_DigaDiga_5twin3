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
        'module_description': 'Gérez l\'infrastructure des stations de transport public de manière intelligente et efficace.'
    }
    return render(request, 'gestion_stations/index.html', context)

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
    """Interface pour ajouter une station"""
    if request.method == 'POST':
        try:
            # Récupérer les données du formulaire
            nom = request.POST.get('nom')
            type_station = request.POST.get('type', 'bus')
            latitude = float(request.POST.get('latitude', '36.8065').replace(',', '.'))
            longitude = float(request.POST.get('longitude', '10.1815').replace(',', '.'))
            adresse = request.POST.get('adresse', '')
            capacite = int(request.POST.get('capacite', '50'))
            heures_ouverture = request.POST.get('heures_ouverture', '6h-22h')
            
            # Validation des données
            if not nom:
                messages.error(request, 'Le nom de la station est obligatoire.')
                return render(request, 'gestion_stations/ajouter_station.html')
            
            if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
                messages.error(request, 'Les coordonnées GPS sont invalides.')
                return render(request, 'gestion_stations/ajouter_station.html')
            
            # Préparer les données pour le gestionnaire RDF
            station_data = {
                'nom': nom,
                'type': type_station,
                'latitude': latitude,
                'longitude': longitude,
                'adresse': adresse,
                'capacité': capacite,
                'heures_ouverture': heures_ouverture
            }
            
            # Ajouter la station via RDF
            success, message = rdf_manager.add_station(station_data)
            
            if success:
                messages.success(request, f'Station "{nom}" ajoutée avec succès!')
                return redirect('gestion_stations:liste')
            else:
                messages.error(request, f'Erreur lors de l\'ajout : {message}')
                
        except (ValueError, TypeError) as e:
            messages.error(request, f'Erreur de validation : {str(e)}')
        except Exception as e:
            messages.error(request, f'Erreur inattendue : {str(e)}')
    
    # Afficher le formulaire d'ajout
    return render(request, 'gestion_stations/ajouter_station.html')

@login_required
def modifier_station(request, station_id):
    """Modifier une station existante"""
    # Construire l'ID au format RDF si c'est un entier
    if isinstance(station_id, int) or str(station_id).isdigit():
        rdf_station_id = f"Station_{station_id}"
    else:
        rdf_station_id = station_id
        
    station = rdf_manager.get_station_by_id(rdf_station_id)
    if not station:
        messages.error(request, 'Station non trouvée.')
        return redirect('gestion_stations:liste')
        
    if request.method == 'POST':
        # Récupérer les données du formulaire
        station_data = {
            'nom': request.POST.get('nom'),
            'type': request.POST.get('type'),
            'latitude': float(request.POST.get('latitude')),
            'longitude': float(request.POST.get('longitude')),
            'adresse': request.POST.get('adresse'),
            'capacite': int(request.POST.get('capacite')),
            'heures_ouverture': request.POST.get('heures_ouverture')
        }
        
        success, message = rdf_manager.update_station(station_id, station_data)
        if success:
            messages.success(request, f'Station {station_data["nom"]} mise à jour avec succès !')
            return redirect('gestion_stations:details', station_id=station_id)
        else:
            messages.error(request, f'Erreur lors de la mise à jour : {message}')
    
    return render(request, 'gestion_stations/modifier_station.html', {
        'station': station
    })

@login_required
def details_station(request, station_id):
    """Détails d'une station"""
    # Construire l'ID au format RDF si c'est un entier
    if isinstance(station_id, int) or str(station_id).isdigit():
        rdf_station_id = f"Station_{station_id}"
    else:
        rdf_station_id = station_id
        
    station = rdf_manager.get_station_by_id(rdf_station_id)
    if not station:
        messages.error(request, 'Station non trouvée.')
        return redirect('gestion_stations:liste')
    
    # Ajouter l'ID numérique pour les URLs
    station['numeric_id'] = station_id
    
    # Récupérer les équipements de la station
    equipements = [
        {
            'nom': 'Ascenseur Nord',
            'statut': 'Opérationnel',
            'derniere_maintenance': '2023-12-01'
        },
        {
            'nom': 'Escalator Principal',
            'statut': 'En maintenance',
            'derniere_maintenance': '2023-11-15'
        },
        {
            'nom': 'Caméra de surveillance',
            'statut': 'Opérationnel',
            'derniere_maintenance': '2023-11-30'
        }
    ]
    
    # Simuler des données de statistiques
    from random import randint, uniform
    statistiques = {
        'affluence_moyenne': f'{randint(50, 200)} personnes/heure',
        'taux_occupation': f'{randint(20, 95)}%',
        'nombre_passages': f'{randint(1000, 5000)}'
    }
    
    # Configuration de l'API Google Maps
    from django.conf import settings
    context = {
        'station': station,
        'equipements': equipements,
        'statistiques': statistiques,
        'google_maps_api_key': getattr(settings, 'GOOGLE_MAPS_API_KEY', '')
    }
    
    return render(request, 'gestion_stations/details_station.html', context)

@login_required
def monitoring_stations(request):
    """Monitoring temps réel des stations"""
    stations = rdf_manager.get_stations()
    
    # Ajouter des données de monitoring simulées pour chaque station et extraire l'ID
    for station in stations:
        # Extraire l'ID numérique de l'URI (par exemple: "Station_1698156734" -> "1698156734")
        station_uri = station.get('station', '')
        try:
            # Extraire l'ID à partir de l'URI (format: .../Station_ID ou Station_ID)
            if 'Station_' in station_uri:
                station_id = station_uri.split('Station_')[-1]
                # Vérifier que c'est bien un nombre
                if station_id.isdigit():
                    station['id'] = int(station_id)
                else:
                    station['id'] = None
            else:
                station['id'] = None
        except (ValueError, AttributeError):
            station['id'] = None
            
        station['monitoring'] = {
            'affluence_actuelle': 'Normale',
            'taux_occupation': '65%',
            'temperature': '22°C',
            'derniere_mise_a_jour': '2 minutes',
            'statut_equipements': 'Opérationnel'
        }
    
    return render(request, 'gestion_stations/monitoring.html', {
        'stations': stations
    })

@login_required
def gestion_equipements(request):
    """Gestion des équipements des stations"""
    stations = rdf_manager.get_stations()
    
    # Ajouter des informations sur les équipements pour chaque station
    for station in stations:
        station['equipements'] = {
            'ascenseurs': [
                {'id': 1, 'statut': 'Opérationnel', 'derniere_maintenance': '2025-10-01'},
                {'id': 2, 'statut': 'En maintenance', 'derniere_maintenance': '2025-10-15'}
            ],
            'escalators': [
                {'id': 1, 'statut': 'Opérationnel', 'derniere_maintenance': '2025-09-30'}
            ],
            'cameras': [
                {'id': 1, 'statut': 'Actif', 'zone': 'Entrée principale'},
                {'id': 2, 'statut': 'Actif', 'zone': 'Quais'}
            ]
        }
    
    return render(request, 'gestion_stations/equipements.html', {
        'stations': stations
    })

@login_required
def preferences_stations(request):
    """Gestion des préférences utilisateur pour les stations"""
    if request.method == 'POST':
        try:
            # Valider les données d'entrée et normaliser les virgules en points
            distance_max = request.POST.get('distance_max', '5.0').replace(',', '.')
            latitude = request.POST.get('latitude', '36.8065').replace(',', '.')
            longitude = request.POST.get('longitude', '10.1815').replace(',', '.')
            
            # Récupérer les préférences
            preferences = {
                'type_station': request.POST.get('type_station', 'all'),
                'distance_max': float(distance_max),
                'equipements': request.POST.getlist('equipements') or [],
                'accessibilite': request.POST.get('accessibilite') == 'on',
                'notification': request.POST.get('notification') == 'on',
                'latitude': float(latitude),
                'longitude': float(longitude)
            }
            
            # Validation des coordonnées
            if not (-90 <= preferences['latitude'] <= 90):
                raise ValueError("Latitude invalide")
            if not (-180 <= preferences['longitude'] <= 180):
                raise ValueError("Longitude invalide")
            if preferences['distance_max'] <= 0:
                raise ValueError("Distance maximale invalide")
            
            # Sauvegarder les préférences dans le RDF
            success = rdf_manager.save_user_station_preferences(request.user.id, preferences)
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                if success:
                    return JsonResponse({
                        'success': True,
                        'message': 'Préférences enregistrées avec succès'
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'message': 'Erreur lors de l\'enregistrement des préférences dans la base de données'
                    }, status=400)
            
            if success:
                messages.success(request, 'Vos préférences ont été enregistrées avec succès !')
            else:
                messages.error(request, 'Erreur lors de l\'enregistrement des préférences')
            return redirect('gestion_stations:preferences')
            
        except (ValueError, TypeError) as e:
            error_message = f'Erreur de validation : {str(e)}'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': error_message
                }, status=400)
            messages.error(request, error_message)
            return redirect('gestion_stations:preferences')
        except Exception as e:
            error_message = f'Erreur inattendue : {str(e)}'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': error_message
                }, status=500)
            messages.error(request, error_message)
            return redirect('gestion_stations:preferences')

    # Récupérer les préférences existantes
    try:
        user_preferences = rdf_manager.get_user_station_preferences(request.user.id)
    except Exception as e:
        user_preferences = {}
        messages.warning(request, 'Impossible de récupérer vos préférences existantes')
    
    return render(request, 'gestion_stations/preferences_stations.html', {
        'preferences': user_preferences
    })

@login_required
def recommandations_stations(request):
    """Obtenir des recommandations de stations personnalisées"""
    # Récupérer les préférences de l'utilisateur
    preferences = rdf_manager.get_user_station_preferences(request.user.id)
    
    # Obtenir la position de l'utilisateur depuis les préférences ou utiliser une position par défaut
    user_lat = float(request.GET.get('latitude', preferences.get('latitude', 36.8065)))
    user_lon = float(request.GET.get('longitude', preferences.get('longitude', 10.1815)))
    
    # Obtenir les recommandations basées sur les préférences
    stations_recommandees = rdf_manager.get_recommended_stations(
        user_lat=user_lat,
        user_lon=user_lon,
        max_distance=preferences.get('distance_max', 5.0),
        station_type=preferences.get('type_station', 'all'),
        accessibility=preferences.get('accessibilite', False)
    )
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'stations': stations_recommandees,
            'preferences': preferences
        })
    
    # Configuration de l'API Google Maps
    from django.conf import settings
    context = {
        'stations': stations_recommandees,
        'preferences': preferences,
        'google_maps_api_key': getattr(settings, 'GOOGLE_MAPS_API_KEY', ''),
        'user_position': {
            'lat': user_lat,
            'lng': user_lon
        }
    }
    
    return render(request, 'gestion_stations/recommandations.html', context)

@login_required
@require_http_methods(["GET"])
def api_stations_list(request):
    """API endpoint pour obtenir la liste des stations en JSON"""
    stations = rdf_manager.get_stations()
    return JsonResponse({'stations': stations})

@login_required
@require_http_methods(["GET"])
def api_station_detail(request, station_id):
    """API endpoint pour obtenir les détails d'une station en JSON"""
    station = rdf_manager.get_station_by_id(station_id)
    if station:
        return JsonResponse(station)
    return HttpResponse(status=404)
