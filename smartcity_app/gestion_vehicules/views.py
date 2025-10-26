"""
Vues pour la gestion des véhicules avec intégration RDF
CRUD complet avec synchronisation automatique vers l'ontologie
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
import json
import logging
import time

from .models import Vehicule, TypeVehicule, MaintenanceVehicule, UtilisationVehicule, ChatMessage, AIAssistant
from ..ontology_manager.vehicle_rdf_manager import vehicle_rdf_manager

logger = logging.getLogger(__name__)


@login_required
def index_vehicules(request):
    """Page d'accueil de la gestion des véhicules"""
    try:
        # Calculer les statistiques depuis la base de données Django
        total_vehicles = Vehicule.objects.count()
        active_vehicles = Vehicule.objects.filter(statut='actif').count()
        electric_vehicles = Vehicule.objects.filter(niveau_batterie__isnull=False).count()
        maintenance_vehicles_count = Vehicule.objects.filter(statut='maintenance').count()
        accessible_vehicles = Vehicule.objects.filter(type_vehicule__accessible_pmr=True).count()
        
        # Statistiques par type
        vehicles_by_type = {}
        for vehicle_type in TypeVehicule.objects.all():
            vehicles_by_type[vehicle_type.nom] = Vehicule.objects.filter(type_vehicule=vehicle_type).count()
        
        # Statistiques par statut
        vehicles_by_status = {}
        for status_code, status_label in Vehicule.STATUTS:
            vehicles_by_status[status_code] = Vehicule.objects.filter(statut=status_code).count()
        
        stats = {
            'total_vehicles': total_vehicles,
            'vehicles_by_status': vehicles_by_status,
            'vehicles_by_type': vehicles_by_type,
            'electric_vehicles': electric_vehicles,
            'accessible_vehicles': accessible_vehicles,
            'active_vehicles': active_vehicles,
            'maintenance_vehicles': maintenance_vehicles_count,
        }
        
        # Récupérer les derniers véhicules ajoutés
        recent_vehicles = Vehicule.objects.select_related('type_vehicule').order_by('-date_mise_en_service')[:5]
        
        # Récupérer les véhicules nécessitant une maintenance
        maintenance_vehicles = Vehicule.objects.filter(
            Q(statut='maintenance') | 
            Q(prochaine_maintenance__isnull=False)
        ).select_related('type_vehicule')[:5]
        
        # Vérifier si l'utilisateur est admin
        is_admin = request.user.is_staff or request.user.is_superuser
        
        context = {
            'page_title': 'Gestion des Véhicules - SmartCity',
            'module_name': 'Gestion des Véhicules',
            'module_description': 'Optimisation et monitoring intelligent des flottes urbaines',
            'stats': stats,
            'recent_vehicles': recent_vehicles,
            'maintenance_vehicles': maintenance_vehicles,
            'vehicle_types': TypeVehicule.objects.all(),
            'is_admin': is_admin,
        }
        return render(request, 'gestion_vehicules/index.html', context)
        
    except Exception as e:
        logger.error(f"Erreur dans index_vehicules: {e}")
        messages.error(request, f"Erreur lors du chargement de la page: {e}")
        return render(request, 'gestion_vehicules/index.html', {
            'page_title': 'Gestion des Véhicules - SmartCity',
            'module_name': 'Gestion des Véhicules',
            'module_description': 'Optimisation et monitoring intelligent des flottes urbaines',
            'stats': {},
            'recent_vehicles': [],
            'maintenance_vehicles': [],
            'vehicle_types': [],
        })


@login_required
def liste_vehicules(request):
    """Liste tous les véhicules avec pagination et filtres"""
    try:
        # Récupérer les paramètres de filtrage
        search_query = request.GET.get('search', '')
        vehicle_type = request.GET.get('type', '')
        status_filter = request.GET.get('status', '')
        
        # Construire la requête
        vehicles_query = Vehicule.objects.select_related('type_vehicule')
        
        if search_query:
            vehicles_query = vehicles_query.filter(
                Q(numero_identification__icontains=search_query) |
                Q(immatriculation__icontains=search_query) |
                Q(localisation_actuelle__icontains=search_query)
            )
        
        if vehicle_type:
            vehicles_query = vehicles_query.filter(type_vehicule__id=vehicle_type)
        
        if status_filter:
            vehicles_query = vehicles_query.filter(statut=status_filter)
        
        # Pagination
        paginator = Paginator(vehicles_query.order_by('-date_mise_en_service'), 20)
        page_number = request.GET.get('page')
        vehicles = paginator.get_page(page_number)
        
        # Récupérer les types de véhicules pour le filtre
        vehicle_types = TypeVehicule.objects.all()
        
        context = {
            'page_title': 'Liste des Véhicules',
            'vehicles': vehicles,
            'vehicle_types': vehicle_types,
            'search_query': search_query,
            'selected_type': vehicle_type,
            'selected_status': status_filter,
            'status_choices': Vehicule.STATUTS,
        }
        return render(request, 'gestion_vehicules/liste_vehicules.html', context)
        
    except Exception as e:
        logger.error(f"Erreur dans liste_vehicules: {e}")
        messages.error(request, f"Erreur lors du chargement de la liste: {e}")
        return render(request, 'gestion_vehicules/liste_vehicules.html', {
            'page_title': 'Liste des Véhicules',
            'vehicles': [],
            'vehicle_types': [],
            'search_query': '',
            'selected_type': '',
            'selected_status': '',
            'status_choices': Vehicule.STATUTS,
        })


@login_required
def detail_vehicule(request, vehicule_id):
    """Détail d'un véhicule spécifique"""
    try:
        vehicule = get_object_or_404(Vehicule, id=vehicule_id)
        
        # Récupérer les maintenances
        maintenances = MaintenanceVehicule.objects.filter(vehicule=vehicule).order_by('-date_planifiee')
        
        # Récupérer les utilisations récentes
        utilisations = UtilisationVehicule.objects.filter(vehicule=vehicule).order_by('-heure_debut')[:10]
        
        # Récupérer les données RDF
        rdf_data = vehicle_rdf_manager.get_vehicle_by_id(f"Vehicule_{vehicule_id}")
        
        context = {
            'page_title': f'Détail - {vehicule}',
            'vehicule': vehicule,
            'maintenances': maintenances,
            'utilisations': utilisations,
            'rdf_data': rdf_data,
        }
        return render(request, 'gestion_vehicules/detail_vehicule.html', context)
        
    except Exception as e:
        logger.error(f"Erreur dans detail_vehicule: {e}")
        messages.error(request, f"Erreur lors du chargement du véhicule: {e}")
        return redirect('gestion_vehicules:liste_vehicules')


@login_required
def creer_vehicule(request):
    """Créer un nouveau véhicule"""
    if request.method == 'POST':
        try:
            # Récupérer les données du formulaire
            type_vehicule_id = request.POST.get('type_vehicule')
            numero_identification = request.POST.get('numero_identification')
            immatriculation = request.POST.get('immatriculation', '')
            localisation_actuelle = request.POST.get('localisation_actuelle', '')
            latitude = request.POST.get('latitude')
            longitude = request.POST.get('longitude')
            statut = request.POST.get('statut', 'actif')
            annee_fabrication = request.POST.get('annee_fabrication')
            kilometrage = request.POST.get('kilometrage', 0)
            niveau_batterie = request.POST.get('niveau_batterie')
            
            # Validation
            if not type_vehicule_id or not numero_identification:
                messages.error(request, "Le type de véhicule et le numéro d'identification sont obligatoires.")
                return redirect('gestion_vehicules:creer_vehicule')
            
            # Vérifier l'unicité du numéro d'identification
            if Vehicule.objects.filter(numero_identification=numero_identification).exists():
                messages.error(request, "Un véhicule avec ce numéro d'identification existe déjà.")
                return redirect('gestion_vehicules:creer_vehicule')
            
            # Récupérer le type de véhicule
            type_vehicule = get_object_or_404(TypeVehicule, id=type_vehicule_id)
            
            # Créer le véhicule
            vehicule = Vehicule.objects.create(
                type_vehicule=type_vehicule,
                numero_identification=numero_identification,
                immatriculation=immatriculation,
                localisation_actuelle=localisation_actuelle,
                latitude=float(latitude) if latitude else None,
                longitude=float(longitude) if longitude else None,
                statut=statut,
                annee_fabrication=int(annee_fabrication) if annee_fabrication else None,
                kilometrage=float(kilometrage) if kilometrage else 0,
                niveau_batterie=int(niveau_batterie) if niveau_batterie else None,
            )
            
            messages.success(request, f"Véhicule {vehicule} créé avec succès et synchronisé avec l'ontologie RDF.")
            return redirect('gestion_vehicules:detail_vehicule', vehicule_id=vehicule.id)
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du véhicule: {e}")
            messages.error(request, f"Erreur lors de la création du véhicule: {e}")
    
    # GET - Afficher le formulaire
    context = {
        'page_title': 'Créer un Véhicule',
        'vehicle_types': TypeVehicule.objects.all(),
        'status_choices': Vehicule.STATUTS,
    }
    return render(request, 'gestion_vehicules/creer_vehicule.html', context)


@login_required
def modifier_vehicule(request, vehicule_id):
    """Modifier un véhicule existant"""
    vehicule = get_object_or_404(Vehicule, id=vehicule_id)
    
    if request.method == 'POST':
        try:
            # Récupérer les données du formulaire
            type_vehicule_id = request.POST.get('type_vehicule')
            numero_identification = request.POST.get('numero_identification')
            immatriculation = request.POST.get('immatriculation', '')
            localisation_actuelle = request.POST.get('localisation_actuelle', '')
            latitude = request.POST.get('latitude')
            longitude = request.POST.get('longitude')
            statut = request.POST.get('statut')
            annee_fabrication = request.POST.get('annee_fabrication')
            kilometrage = request.POST.get('kilometrage')
            niveau_batterie = request.POST.get('niveau_batterie')
            
            # Validation
            if not type_vehicule_id or not numero_identification:
                messages.error(request, "Le type de véhicule et le numéro d'identification sont obligatoires.")
                return redirect('gestion_vehicules:modifier_vehicule', vehicule_id=vehicule_id)
            
            # Vérifier l'unicité du numéro d'identification (sauf pour le véhicule actuel)
            if Vehicule.objects.filter(numero_identification=numero_identification).exclude(id=vehicule_id).exists():
                messages.error(request, "Un autre véhicule avec ce numéro d'identification existe déjà.")
                return redirect('gestion_vehicules:modifier_vehicule', vehicule_id=vehicule_id)
            
            # Récupérer le type de véhicule
            type_vehicule = get_object_or_404(TypeVehicule, id=type_vehicule_id)
            
            # Mettre à jour le véhicule
            vehicule.type_vehicule = type_vehicule
            vehicule.numero_identification = numero_identification
            vehicule.immatriculation = immatriculation
            vehicule.localisation_actuelle = localisation_actuelle
            vehicule.latitude = float(latitude) if latitude else None
            vehicule.longitude = float(longitude) if longitude else None
            vehicule.statut = statut
            vehicule.annee_fabrication = int(annee_fabrication) if annee_fabrication else None
            vehicule.kilometrage = float(kilometrage) if kilometrage else 0
            vehicule.niveau_batterie = int(niveau_batterie) if niveau_batterie else None
            vehicule.save()
            
            messages.success(request, f"Véhicule {vehicule} modifié avec succès et synchronisé avec l'ontologie RDF.")
            return redirect('gestion_vehicules:detail_vehicule', vehicule_id=vehicule.id)
            
        except Exception as e:
            logger.error(f"Erreur lors de la modification du véhicule: {e}")
            messages.error(request, f"Erreur lors de la modification du véhicule: {e}")
    
    # GET - Afficher le formulaire pré-rempli
    context = {
        'page_title': f'Modifier - {vehicule}',
        'vehicule': vehicule,
        'vehicle_types': TypeVehicule.objects.all(),
        'status_choices': Vehicule.STATUTS,
    }
    return render(request, 'gestion_vehicules/modifier_vehicule.html', context)


@login_required
def supprimer_vehicule(request, vehicule_id):
    """Supprimer un véhicule"""
    vehicule = get_object_or_404(Vehicule, id=vehicule_id)
    
    if request.method == 'POST':
        try:
            vehicule_name = str(vehicule)
            vehicule.delete()  # La synchronisation RDF se fait automatiquement via le signal
            
            messages.success(request, f"Véhicule {vehicule_name} supprimé avec succès de la base de données et de l'ontologie RDF.")
            return redirect('gestion_vehicules:liste_vehicules')
            
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du véhicule: {e}")
            messages.error(request, f"Erreur lors de la suppression du véhicule: {e}")
    
    # GET - Afficher la confirmation
    context = {
        'page_title': f'Supprimer - {vehicule}',
        'vehicule': vehicule,
    }
    return render(request, 'gestion_vehicules/supprimer_vehicule.html', context)


@login_required
def gestion_flotte(request):
    """Gestion de la flotte de véhicules"""
    try:
        # Récupérer les statistiques détaillées
        stats = vehicle_rdf_manager.get_vehicle_statistics()
        
        # Récupérer les véhicules par type
        vehicles_by_type = {}
        for vehicle_type in TypeVehicule.objects.all():
            vehicles_by_type[vehicle_type.nom] = Vehicule.objects.filter(type_vehicule=vehicle_type)
        
        # Récupérer les véhicules par statut
        vehicles_by_status = {}
        for status_code, status_label in Vehicule.STATUTS:
            vehicles_by_status[status_label] = Vehicule.objects.filter(statut=status_code)
        
        context = {
            'page_title': 'Gestion de Flotte',
            'stats': stats,
            'vehicles_by_type': vehicles_by_type,
            'vehicles_by_status': vehicles_by_status,
            'vehicle_types': TypeVehicule.objects.all(),
        }
        return render(request, 'gestion_vehicules/gestion_flotte.html', context)
        
    except Exception as e:
        logger.error(f"Erreur dans gestion_flotte: {e}")
        messages.error(request, f"Erreur lors du chargement de la gestion de flotte: {e}")
        return render(request, 'gestion_vehicules/gestion_flotte.html', {
            'page_title': 'Gestion de Flotte',
            'stats': {},
            'vehicles_by_type': {},
            'vehicles_by_status': {},
            'vehicle_types': [],
        })


@login_required
def tracking_vehicules(request):
    """Tracking GPS temps réel des véhicules"""
    try:
        # Récupérer tous les véhicules avec leurs positions
        vehicles = Vehicule.objects.filter(
            latitude__isnull=False,
            longitude__isnull=False
        ).select_related('type_vehicule')
        
        # Préparer les données pour la carte
        vehicles_data = []
        for vehicle in vehicles:
            vehicles_data.append({
                'id': vehicle.id,
                'numero': vehicle.numero_identification,
                'type': vehicle.type_vehicule.nom,
                'statut': vehicle.get_statut_display(),
                'localisation': vehicle.localisation_actuelle,
                'latitude': float(vehicle.latitude),
                'longitude': float(vehicle.longitude),
                'niveau_batterie': vehicle.niveau_batterie,
            })
        
        context = {
            'page_title': 'Tracking Véhicules',
            'vehicles': vehicles,
            'vehicles_data': json.dumps(vehicles_data),
        }
        return render(request, 'gestion_vehicules/tracking_vehicules.html', context)
        
    except Exception as e:
        logger.error(f"Erreur dans tracking_vehicules: {e}")
        messages.error(request, f"Erreur lors du chargement du tracking: {e}")
        return render(request, 'gestion_vehicules/tracking_vehicules.html', {
            'page_title': 'Tracking Véhicules',
            'vehicles': [],
            'vehicles_data': '[]',
        })


@login_required
def gestion_maintenance(request):
    """Gestion et prédiction de maintenance"""
    try:
        # Récupérer les maintenances planifiées
        maintenances_planifiees = MaintenanceVehicule.objects.filter(
            statut='planifiee'
        ).select_related('vehicule__type_vehicule').order_by('date_planifiee')
        
        # Récupérer les maintenances en cours
        maintenances_en_cours = MaintenanceVehicule.objects.filter(
            statut='en_cours'
        ).select_related('vehicule__type_vehicule')
        
        # Récupérer les véhicules nécessitant une maintenance
        vehicules_maintenance = Vehicule.objects.filter(
            Q(statut='maintenance') | 
            Q(prochaine_maintenance__isnull=False)
        ).select_related('type_vehicule')
        
        context = {
            'page_title': 'Gestion Maintenance',
            'maintenances_planifiees': maintenances_planifiees,
            'maintenances_en_cours': maintenances_en_cours,
            'vehicules_maintenance': vehicules_maintenance,
        }
        return render(request, 'gestion_vehicules/gestion_maintenance.html', context)
        
    except Exception as e:
        logger.error(f"Erreur dans gestion_maintenance: {e}")
        messages.error(request, f"Erreur lors du chargement de la maintenance: {e}")
        return render(request, 'gestion_vehicules/gestion_maintenance.html', {
            'page_title': 'Gestion Maintenance',
            'maintenances_planifiees': [],
            'maintenances_en_cours': [],
            'vehicules_maintenance': [],
        })


@login_required
def vehicules_partages(request):
    """Gestion des véhicules partagés"""
    try:
        # Récupérer les véhicules partagés (vélos, voitures partagées, etc.)
        vehicules_partages = Vehicule.objects.filter(
            type_vehicule__categorie='vehicule_partage'
        ).select_related('type_vehicule')
        
        # Statistiques spécifiques aux véhicules partagés
        stats_partages = {
            'total': vehicules_partages.count(),
            'disponibles': vehicules_partages.filter(statut='actif').count(),
            'en_maintenance': vehicules_partages.filter(statut='maintenance').count(),
            'hors_service': vehicules_partages.filter(statut='hors_service').count(),
        }
        
        context = {
            'page_title': 'Véhicules Partagés',
            'vehicules_partages': vehicules_partages,
            'stats_partages': stats_partages,
        }
        return render(request, 'gestion_vehicules/vehicules_partages.html', context)
        
    except Exception as e:
        logger.error(f"Erreur dans vehicules_partages: {e}")
        messages.error(request, f"Erreur lors du chargement des véhicules partagés: {e}")
        return render(request, 'gestion_vehicules/vehicules_partages.html', {
            'page_title': 'Véhicules Partagés',
            'vehicules_partages': [],
            'stats_partages': {'total': 0, 'disponibles': 0, 'en_maintenance': 0, 'hors_service': 0},
        })


@login_required
def analytics_vehicules(request):
    """Analytics et rapports sur les véhicules"""
    try:
        # Récupérer les statistiques RDF
        rdf_stats = vehicle_rdf_manager.get_vehicle_statistics()
        
        # Récupérer les statistiques Django
        django_stats = {
            'total_vehicles': Vehicule.objects.count(),
            'vehicles_by_type': {},
            'vehicles_by_status': {},
            'maintenance_needed': Vehicule.objects.filter(statut='maintenance').count(),
            'electric_vehicles': Vehicule.objects.filter(niveau_batterie__isnull=False).count(),
        }
        
        # Statistiques par type
        for vehicle_type in TypeVehicule.objects.all():
            django_stats['vehicles_by_type'][vehicle_type.nom] = Vehicule.objects.filter(
                type_vehicule=vehicle_type
            ).count()
        
        # Statistiques par statut
        for status_code, status_label in Vehicule.STATUTS:
            django_stats['vehicles_by_status'][status_label] = Vehicule.objects.filter(
                statut=status_code
            ).count()
        
        context = {
            'page_title': 'Analytics Véhicules',
            'rdf_stats': rdf_stats,
            'django_stats': django_stats,
        }
        return render(request, 'gestion_vehicules/analytics_vehicules.html', context)
        
    except Exception as e:
        logger.error(f"Erreur dans analytics_vehicules: {e}")
        messages.error(request, f"Erreur lors du chargement des analytics: {e}")
        return render(request, 'gestion_vehicules/analytics_vehicules.html', {
            'page_title': 'Analytics Véhicules',
            'rdf_stats': {},
            'django_stats': {},
        })


# API Views pour AJAX
@login_required
@require_http_methods(["GET"])
def api_vehicles_data(request):
    """API pour récupérer les données des véhicules en JSON"""
    try:
        vehicles = Vehicule.objects.select_related('type_vehicule').all()
        vehicles_data = []
        
        for vehicle in vehicles:
            vehicles_data.append({
                'id': vehicle.id,
                'numero_identification': vehicle.numero_identification,
                'type_vehicule': vehicle.type_vehicule.nom,
                'statut': vehicle.get_statut_display(),
                'localisation': vehicle.localisation_actuelle,
                'latitude': vehicle.latitude,
                'longitude': vehicle.longitude,
                'niveau_batterie': vehicle.niveau_batterie,
                'date_mise_en_service': vehicle.date_mise_en_service.isoformat(),
            })
        
        return JsonResponse({
            'status': 'success',
            'data': vehicles_data,
            'count': len(vehicles_data)
        })
        
    except Exception as e:
        logger.error(f"Erreur dans api_vehicles_data: {e}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def api_vehicle_rdf_data(request, vehicule_id):
    """API pour récupérer les données RDF d'un véhicule"""
    try:
        rdf_data = vehicle_rdf_manager.get_vehicle_by_id(f"Vehicule_{vehicule_id}")
        
        if rdf_data:
            return JsonResponse({
                'status': 'success',
                'data': rdf_data
            })
        else:
            return JsonResponse({
                'status': 'not_found',
                'message': 'Véhicule non trouvé dans l\'ontologie RDF'
            }, status=404)
            
    except Exception as e:
        logger.error(f"Erreur dans api_vehicle_rdf_data: {e}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def api_sync_vehicle_to_rdf(request, vehicule_id):
    """API pour synchroniser manuellement un véhicule avec le RDF"""
    try:
        vehicule = get_object_or_404(Vehicule, id=vehicule_id)
        vehicule.sync_to_rdf()
        
        return JsonResponse({
            'status': 'success',
            'message': f'Véhicule {vehicule} synchronisé avec l\'ontologie RDF'
        })
        
    except Exception as e:
        logger.error(f"Erreur dans api_sync_vehicle_to_rdf: {e}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def api_vehicle_statistics(request):
    """API pour récupérer les statistiques des véhicules"""
    try:
        rdf_stats = vehicle_rdf_manager.get_vehicle_statistics()
        
        return JsonResponse({
            'status': 'success',
            'data': rdf_stats
        })
        
    except Exception as e:
        logger.error(f"Erreur dans api_vehicle_statistics: {e}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


def api_positions(request):
    """API pour positions GPS des véhicules (legacy)"""
    try:
        vehicles = Vehicule.objects.filter(
            latitude__isnull=False,
            longitude__isnull=False
        ).select_related('type_vehicule')
        
        positions = []
        for vehicle in vehicles:
            positions.append({
                'id': vehicle.id,
                'numero': vehicle.numero_identification,
                'type': vehicle.type_vehicule.nom,
                'statut': vehicle.statut,
                'latitude': float(vehicle.latitude),
                'longitude': float(vehicle.longitude),
                'localisation': vehicle.localisation_actuelle,
            })
        
        return JsonResponse({
            'status': 'success',
            'data': positions,
            'count': len(positions)
        })
        
    except Exception as e:
        logger.error(f"Erreur dans api_positions: {e}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required
def tracking_vehicules(request):
    """Page de suivi GPS des véhicules"""
    try:
        # Récupérer les véhicules avec coordonnées GPS
        vehicles = Vehicule.objects.filter(
            latitude__isnull=False,
            longitude__isnull=False
        ).select_related('type_vehicule')
        
        # Préparer les données pour la carte
        vehicles_data = []
        for vehicle in vehicles:
            vehicles_data.append({
                'id': vehicle.id,
                'numero': vehicle.numero_identification,
                'type': vehicle.type_vehicule.nom,
                'statut': vehicle.statut,
                'localisation': vehicle.localisation_actuelle,
                'latitude': float(vehicle.latitude),
                'longitude': float(vehicle.longitude),
                'niveau_batterie': vehicle.niveau_batterie,
            })
        
        context = {
            'page_title': 'Suivi GPS - SmartCity',
            'vehicles': vehicles,
            'vehicles_data': json.dumps(vehicles_data),
        }
        return render(request, 'gestion_vehicules/tracking.html', context)
        
    except Exception as e:
        logger.error(f"Erreur dans tracking_vehicules: {e}")
        messages.error(request, f"Erreur lors du chargement du suivi GPS: {e}")
        return render(request, 'gestion_vehicules/tracking.html', {
            'page_title': 'Suivi GPS - SmartCity',
            'vehicles': [],
            'vehicles_data': '[]',
        })


@login_required
def gestion_maintenance(request):
    """Page de gestion de la maintenance"""
    try:
        # Récupérer les maintenances planifiées
        maintenances_planifiees = MaintenanceVehicule.objects.filter(
            statut='planifiee'
        ).select_related('vehicule__type_vehicule').order_by('date_planifiee')
        
        # Récupérer les maintenances en cours
        maintenances_en_cours = MaintenanceVehicule.objects.filter(
            statut='en_cours'
        ).select_related('vehicule__type_vehicule')
        
        # Récupérer les véhicules nécessitant une maintenance
        vehicules_maintenance = Vehicule.objects.filter(
            Q(statut='maintenance') | 
            Q(prochaine_maintenance__isnull=False)
        ).select_related('type_vehicule')
        
        context = {
            'page_title': 'Gestion Maintenance - SmartCity',
            'maintenances_planifiees': maintenances_planifiees,
            'maintenances_en_cours': maintenances_en_cours,
            'vehicules_maintenance': vehicules_maintenance,
        }
        return render(request, 'gestion_vehicules/maintenance.html', context)
        
    except Exception as e:
        logger.error(f"Erreur dans gestion_maintenance: {e}")
        messages.error(request, f"Erreur lors du chargement de la maintenance: {e}")
        return render(request, 'gestion_vehicules/maintenance.html', {
            'page_title': 'Gestion Maintenance - SmartCity',
            'maintenances_planifiees': [],
            'maintenances_en_cours': [],
            'vehicules_maintenance': [],
        })


@login_required
def analytics_vehicules(request):
    """Page d'analytics des véhicules"""
    try:
        # Calculer les statistiques
        total_vehicles = Vehicule.objects.count()
        active_vehicles = Vehicule.objects.filter(statut='actif').count()
        electric_vehicles = Vehicule.objects.filter(niveau_batterie__isnull=False).count()
        maintenance_vehicles = Vehicule.objects.filter(statut='maintenance').count()
        
        stats = {
            'total_vehicles': total_vehicles,
            'active_vehicles': active_vehicles,
            'electric_vehicles': electric_vehicles,
            'maintenance_vehicles': maintenance_vehicles,
        }
        
        context = {
            'page_title': 'Analytics Véhicules - SmartCity',
            'stats': stats,
        }
        return render(request, 'gestion_vehicules/analytics.html', context)
        
    except Exception as e:
        logger.error(f"Erreur dans analytics_vehicules: {e}")
        messages.error(request, f"Erreur lors du chargement des analytics: {e}")
        return render(request, 'gestion_vehicules/analytics.html', {
            'page_title': 'Analytics Véhicules - SmartCity',
            'stats': {},
        })


@login_required
def api_sync_from_rdf(request):
    """API pour synchroniser les véhicules depuis l'ontologie RDF"""
    if request.method == 'POST':
        try:
            # Récupérer tous les véhicules depuis l'ontologie RDF
            success, vehicles_data = vehicle_rdf_manager.get_all_vehicles()
            
            if not success:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Erreur lors de la récupération des données RDF'
                })
            
            synced_count = 0
            errors = []
            
            for vehicle_data in vehicles_data:
                try:
                    # Vérifier si le véhicule existe déjà
                    vehicle_id = vehicle_data.get('id', '').replace('Vehicule_', '')
                    if vehicle_id.isdigit():
                        vehicle_id = int(vehicle_id)
                        if Vehicule.objects.filter(id=vehicle_id).exists():
                            continue
                    
                    # Créer le type de véhicule s'il n'existe pas
                    type_vehicule, created = TypeVehicule.objects.get_or_create(
                        nom=vehicle_data.get('type_vehicule', 'Inconnu'),
                        defaults={
                            'capacite_passagers': vehicle_data.get('capacite_passagers', 4),
                            'emission_co2': vehicle_data.get('emission_co2', 0.0),
                            'accessible_pmr': vehicle_data.get('accessible_pmr', False),
                        }
                    )
                    
                    # Créer le véhicule
                    vehicule = Vehicule.objects.create(
                        numero_identification=vehicle_data.get('numero', f'RDF_{int(time.time())}'),
                        type_vehicule=type_vehicule,
                        statut=vehicle_data.get('statut', 'actif'),
                        localisation_actuelle=vehicle_data.get('localisation', ''),
                        latitude=vehicle_data.get('latitude'),
                        longitude=vehicle_data.get('longitude'),
                        niveau_batterie=vehicle_data.get('niveau_batterie'),
                    )
                    
                    synced_count += 1
                    
                except Exception as e:
                    errors.append(f"Erreur lors de la création du véhicule: {str(e)}")
            
            if errors:
                return JsonResponse({
                    'status': 'partial_success',
                    'message': f'{synced_count} véhicules synchronisés depuis RDF, {len(errors)} erreurs',
                    'errors': errors
                })
            else:
                return JsonResponse({
                    'status': 'success',
                    'message': f'{synced_count} véhicules synchronisés depuis RDF avec succès'
                })
                
        except Exception as e:
            logger.error(f"Erreur lors de la synchronisation depuis RDF: {e}")
    return JsonResponse({
                'status': 'error',
                'message': f'Erreur lors de la synchronisation depuis RDF: {str(e)}'
    })
    
    return JsonResponse({'status': 'error', 'message': 'Méthode non autorisée'})


@login_required
def ai_assistant(request):
    """Page de l'assistant IA pour les véhicules"""
    try:
        # Récupérer l'historique des messages de l'utilisateur
        chat_messages = ChatMessage.objects.filter(user=request.user)[:20]
        
        # Récupérer ou créer l'assistant IA
        assistant, created = AIAssistant.objects.get_or_create(
            is_active=True,
            defaults={
                'name': 'Assistant Véhicules SmartCity',
                'system_prompt': 'Tu es un assistant spécialisé dans la gestion de véhicules et la maintenance automobile. Tu peux aider avec les diagnostics, les conseils de maintenance, les réparations et toutes questions liées aux véhicules. Réponds en français de manière claire et professionnelle.'
            }
        )
        
        context = {
            'page_title': 'Assistant IA - SmartCity',
            'chat_messages': chat_messages,
            'assistant': assistant,
        }
        return render(request, 'gestion_vehicules/ai_assistant.html', context)
        
    except Exception as e:
        logger.error(f"Erreur dans ai_assistant: {e}")
        messages.error(request, f"Erreur lors du chargement de l'assistant IA: {e}")
        return render(request, 'gestion_vehicules/ai_assistant.html', {
            'page_title': 'Assistant IA - SmartCity',
            'chat_messages': [],
            'assistant': None,
        })


@login_required
@require_http_methods(["POST"])
def api_chat_with_ai(request):
    """API pour chatter avec l'assistant IA"""
    try:
        from django.conf import settings
        import openai
        
        # Configuration OpenAI
        openai.api_key = settings.OPENAI_API_KEY
        
        # Récupérer le message de l'utilisateur
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        message_type = data.get('type', 'question')
        
        if not user_message:
            return JsonResponse({
                'status': 'error',
                'message': 'Le message ne peut pas être vide'
            })
        
        # Récupérer l'assistant IA
        try:
            assistant = AIAssistant.objects.get(is_active=True)
            system_prompt = assistant.system_prompt
        except AIAssistant.DoesNotExist:
            system_prompt = "Tu es un assistant spécialisé dans la gestion de véhicules et la maintenance automobile."
        
        # Récupérer l'historique récent pour le contexte
        recent_messages = ChatMessage.objects.filter(user=request.user)[:5]
        
        # Construire le contexte de conversation
        messages = [{"role": "system", "content": system_prompt}]
        
        for msg in reversed(recent_messages):
            messages.append({"role": "user", "content": msg.message})
            messages.append({"role": "assistant", "content": msg.response})
        
        messages.append({"role": "user", "content": user_message})
        
        # Appel à l'API OpenAI
        response = openai.ChatCompletion.create(
            model=settings.OPENAI_MODEL,
            messages=messages,
            max_tokens=500,
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content.strip()
        
        # Sauvegarder la conversation
        chat_message = ChatMessage.objects.create(
            user=request.user,
            message=user_message,
            response=ai_response,
            message_type=message_type
        )
        
        return JsonResponse({
            'status': 'success',
            'response': ai_response,
            'message_id': chat_message.id,
            'timestamp': chat_message.timestamp.isoformat()
        })
        
    except openai.error.OpenAIError as e:
        logger.error(f"Erreur OpenAI: {e}")
        return JsonResponse({
            'status': 'error',
            'message': f'Erreur de l\'assistant IA: {str(e)}'
        })
    except Exception as e:
        logger.error(f"Erreur dans api_chat_with_ai: {e}")
        return JsonResponse({
            'status': 'error',
            'message': f'Erreur lors de la communication avec l\'IA: {str(e)}'
        })


@login_required
@require_http_methods(["GET"])
def api_chat_history(request):
    """API pour récupérer l'historique des conversations"""
    try:
        messages = ChatMessage.objects.filter(user=request.user)[:50]
        
        messages_data = []
        for msg in messages:
            messages_data.append({
                'id': msg.id,
                'message': msg.message,
                'response': msg.response,
                'timestamp': msg.timestamp.isoformat(),
                'type': msg.message_type
            })
        
        return JsonResponse({
            'status': 'success',
            'messages': messages_data
        })
        
    except Exception as e:
        logger.error(f"Erreur dans api_chat_history: {e}")
        return JsonResponse({
            'status': 'error',
            'message': f'Erreur lors de la récupération de l\'historique: {str(e)}'
        })


@login_required
@require_http_methods(["DELETE"])
def api_clear_chat_history(request):
    """API pour effacer l'historique des conversations"""
    try:
        ChatMessage.objects.filter(user=request.user).delete()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Historique effacé avec succès'
        })
        
    except Exception as e:
        logger.error(f"Erreur dans api_clear_chat_history: {e}")
        return JsonResponse({
            'status': 'error',
            'message': f'Erreur lors de l\'effacement de l\'historique: {str(e)}'
    })