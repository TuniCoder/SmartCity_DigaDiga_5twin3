from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Avg
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import datetime, timedelta
import json
from functools import wraps

from .models import CapteurTrafic, ZoneTrafic, DonneesTrafic, FeuSignalisation, EvenementTrafic
from .rdf_integration import add_capteur_to_rdf


# ============================================================================
# DÉCORATEURS DE PERMISSION
# ============================================================================

def admin_required(view_func):
    """Décorateur pour vérifier que l'utilisateur est admin"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')

        # Vérifier si l'utilisateur est admin ou staff
        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, '❌ Accès refusé. Cette section est réservée aux administrateurs.')
            return redirect('gestion_trafic:carte_trafic_user')

        return view_func(request, *args, **kwargs)
    return wrapper


@admin_required
def index_trafic(request):
    """Page d'accueil de la gestion du trafic - ADMIN ONLY"""
    # Statistiques rapides
    total_capteurs = CapteurTrafic.objects.count()
    capteurs_actifs = CapteurTrafic.objects.filter(statut='actif').count()
    zones_trafic = ZoneTrafic.objects.count()

    # Capteurs récents
    capteurs_recents = CapteurTrafic.objects.order_by('-date_creation')[:5]

    context = {
        'page_title': 'Gestion du Trafic - SmartCity',
        'module_name': 'Gestion du Trafic',
        'module_description': 'Intelligence artificielle pour optimiser les flux de circulation urbaine',
        'total_capteurs': total_capteurs,
        'capteurs_actifs': capteurs_actifs,
        'zones_trafic': zones_trafic,
        'capteurs_recents': capteurs_recents,
    }
    return render(request, 'gestion_trafic/index_trafic.html', context)


# ============================================================================
# CRUD CAPTEURS DE TRAFIC
# ============================================================================

@admin_required
def liste_capteurs(request):
    """Liste tous les capteurs de trafic avec pagination et recherche - ADMIN ONLY"""
    capteurs = CapteurTrafic.objects.select_related('zone_trafic').all()
    
    # Recherche
    search_query = request.GET.get('search', '')
    if search_query:
        capteurs = capteurs.filter(
            Q(nom__icontains=search_query) |
            Q(code_capteur__icontains=search_query) |
            Q(zone_trafic__nom__icontains=search_query) |
            Q(direction_mesure__icontains=search_query)
        )
    
    # Filtrage par statut
    statut_filter = request.GET.get('statut', '')
    if statut_filter:
        capteurs = capteurs.filter(statut=statut_filter)
    
    # Filtrage par type
    type_filter = request.GET.get('type', '')
    if type_filter:
        capteurs = capteurs.filter(type_capteur=type_filter)
    
    # Tri
    sort_by = request.GET.get('sort', 'nom')
    capteurs = capteurs.order_by(sort_by)
    
    # Pagination
    paginator = Paginator(capteurs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_title': 'Capteurs de Trafic',
        'page_obj': page_obj,
        'search_query': search_query,
        'statut_filter': statut_filter,
        'type_filter': type_filter,
        'sort_by': sort_by,
        'statuts': CapteurTrafic.STATUTS,
        'types_capteur': CapteurTrafic.TYPES_CAPTEUR,
    }
    return render(request, 'gestion_trafic/liste_capteurs.html', context)


@admin_required
def detail_capteur(request, capteur_id):
    """Détail d'un capteur de trafic - ADMIN ONLY"""
    capteur = get_object_or_404(CapteurTrafic, id=capteur_id)
    
    # Données récentes du capteur
    donnees_recentes = DonneesTrafic.objects.filter(
        capteur=capteur
    ).order_by('-timestamp')[:10]
    
    # Statistiques du capteur
    stats = {
        'total_mesures': DonneesTrafic.objects.filter(capteur=capteur).count(),
        'derniere_mesure': DonneesTrafic.objects.filter(capteur=capteur).first(),
        'vitesse_moyenne': DonneesTrafic.objects.filter(
            capteur=capteur, 
            vitesse_moyenne__isnull=False
        ).aggregate(avg_speed=Avg('vitesse_moyenne'))['avg_speed'],
    }
    
    context = {
        'page_title': f'Capteur {capteur.nom}',
        'capteur': capteur,
        'donnees_recentes': donnees_recentes,
        'stats': stats,
    }
    return render(request, 'gestion_trafic/detail_capteur.html', context)


@admin_required
def creer_capteur(request):
    """Créer un nouveau capteur de trafic - ADMIN ONLY"""
    if request.method == 'POST':
        try:
            # Récupération des données du formulaire
            nom = request.POST.get('nom')
            code_capteur = request.POST.get('code_capteur')
            type_capteur = request.POST.get('type_capteur')
            zone_trafic_id = request.POST.get('zone_trafic')
            latitude = float(request.POST.get('latitude'))
            longitude = float(request.POST.get('longitude'))
            direction_mesure = request.POST.get('direction_mesure')
            statut = request.POST.get('statut', 'actif')
            frequence_mesure = int(request.POST.get('frequence_mesure', 60))
            precision_detection = float(request.POST.get('precision_detection', 95.0))
            vitesse_min_detection = int(request.POST.get('vitesse_min_detection', 5))
            vitesse_max_detection = int(request.POST.get('vitesse_max_detection', 200))
            date_installation = request.POST.get('date_installation')
            fournisseur = request.POST.get('fournisseur', '')
            modele = request.POST.get('modele', '')
            
            # Validation
            if not all([nom, code_capteur, type_capteur, zone_trafic_id, latitude, longitude]):
                messages.error(request, 'Tous les champs obligatoires doivent être remplis.')
                return redirect('gestion_trafic:creer_capteur')
            
            # Vérification unicité du code
            if CapteurTrafic.objects.filter(code_capteur=code_capteur).exists():
                messages.error(request, 'Un capteur avec ce code existe déjà.')
                return redirect('gestion_trafic:creer_capteur')
            
            # Création du capteur
            zone_trafic = get_object_or_404(ZoneTrafic, id=zone_trafic_id)
            capteur = CapteurTrafic.objects.create(
                nom=nom,
                code_capteur=code_capteur,
                type_capteur=type_capteur,
                zone_trafic=zone_trafic,
                latitude=latitude,
                longitude=longitude,
                direction_mesure=direction_mesure,
                statut=statut,
                frequence_mesure=frequence_mesure,
                precision_detection=precision_detection,
                vitesse_min_detection=vitesse_min_detection,
                vitesse_max_detection=vitesse_max_detection,
                date_installation=date_installation,
                fournisseur=fournisseur,
                modele=modele,
            )
            
            # Ajouter le capteur au fichier RDF automatiquement
            try:
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"Tentative d'ajout RDF pour le capteur: {capteur.nom} (ID: {capteur.id})")
                
                success = add_capteur_to_rdf(capteur)
                
                if success:
                    messages.success(request, f'Capteur "{capteur.nom}" créé avec succès et intégré dans l\'ontologie RDF.')
                    logger.info(f"Capteur {capteur.nom} ajouté au RDF avec succès")
                else:
                    messages.warning(request, f'Capteur "{capteur.nom}" créé avec succès mais l\'intégration RDF a échoué.')
                    logger.warning(f"Échec de l'ajout RDF pour le capteur {capteur.nom}")
                    
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Erreur lors de l'intégration RDF: {str(e)}", exc_info=True)
                messages.warning(request, f'Capteur créé mais erreur lors de l\'intégration RDF: {str(e)}')
            
            return redirect('gestion_trafic:detail_capteur', capteur_id=capteur.id)
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la création du capteur : {str(e)}')
            return redirect('gestion_trafic:creer_capteur')
    
    # GET - Affichage du formulaire
    zones_trafic = ZoneTrafic.objects.all()
    context = {
        'page_title': 'Créer un Capteur',
        'zones_trafic': zones_trafic,
        'statuts': CapteurTrafic.STATUTS,
        'types_capteur': CapteurTrafic.TYPES_CAPTEUR,
    }
    return render(request, 'gestion_trafic/creer_capteur.html', context)


@admin_required
def modifier_capteur(request, capteur_id):
    """Modifier un capteur de trafic existant - ADMIN ONLY"""
    capteur = get_object_or_404(CapteurTrafic, id=capteur_id)
    
    if request.method == 'POST':
        try:
            # Mise à jour des données
            capteur.nom = request.POST.get('nom')
            capteur.type_capteur = request.POST.get('type_capteur')
            zone_trafic_id = request.POST.get('zone_trafic')
            capteur.latitude = float(request.POST.get('latitude'))
            capteur.longitude = float(request.POST.get('longitude'))
            capteur.direction_mesure = request.POST.get('direction_mesure')
            capteur.statut = request.POST.get('statut')
            capteur.frequence_mesure = int(request.POST.get('frequence_mesure', 60))
            capteur.precision_detection = float(request.POST.get('precision_detection', 95.0))
            capteur.vitesse_min_detection = int(request.POST.get('vitesse_min_detection', 5))
            capteur.vitesse_max_detection = int(request.POST.get('vitesse_max_detection', 200))
            capteur.fournisseur = request.POST.get('fournisseur', '')
            capteur.modele = request.POST.get('modele', '')
            
            # Mise à jour de la zone si changée
            if zone_trafic_id:
                capteur.zone_trafic = get_object_or_404(ZoneTrafic, id=zone_trafic_id)
            
            # Mise à jour de la calibration si demandée
            if request.POST.get('recalibrer') == 'on':
                capteur.derniere_calibration = timezone.now()
            
            capteur.save()
            
            messages.success(request, f'Capteur "{capteur.nom}" modifié avec succès.')
            return redirect('gestion_trafic:detail_capteur', capteur_id=capteur.id)
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la modification : {str(e)}')
    
    # GET - Affichage du formulaire
    zones_trafic = ZoneTrafic.objects.all()
    context = {
        'page_title': f'Modifier {capteur.nom}',
        'capteur': capteur,
        'zones_trafic': zones_trafic,
        'statuts': CapteurTrafic.STATUTS,
        'types_capteur': CapteurTrafic.TYPES_CAPTEUR,
    }
    return render(request, 'gestion_trafic/modifier_capteur.html', context)


@admin_required
@require_http_methods(["POST"])
def supprimer_capteur(request, capteur_id):
    """Supprimer un capteur de trafic - ADMIN ONLY"""
    capteur = get_object_or_404(CapteurTrafic, id=capteur_id)
    
    try:
        nom_capteur = capteur.nom
        capteur.delete()
        messages.success(request, f'Capteur "{nom_capteur}" supprimé avec succès.')
    except Exception as e:
        messages.error(request, f'Erreur lors de la suppression : {str(e)}')
    
    return redirect('gestion_trafic:liste_capteurs')


# ============================================================================
# API ENDPOINTS
# ============================================================================

def api_capteurs(request):
    """API pour récupérer la liste des capteurs"""
    capteurs = CapteurTrafic.objects.select_related('zone_trafic').all()
    
    # Filtrage par statut
    statut = request.GET.get('statut')
    if statut:
        capteurs = capteurs.filter(statut=statut)
    
    # Format JSON
    data = []
    for capteur in capteurs:
        data.append({
            'id': capteur.id,
            'nom': capteur.nom,
            'code_capteur': capteur.code_capteur,
            'type_capteur': capteur.type_capteur,
            'statut': capteur.statut,
            'latitude': capteur.latitude,
            'longitude': capteur.longitude,
            'zone_trafic': capteur.zone_trafic.nom,
            'est_operationnel': capteur.est_operationnel,
        })
    
    return JsonResponse({'capteurs': data})


def api_donnees_capteur(request, capteur_id):
    """API pour récupérer les données d'un capteur"""
    capteur = get_object_or_404(CapteurTrafic, id=capteur_id)
    
    # Paramètres de filtrage
    heures = int(request.GET.get('heures', 24))
    date_debut = timezone.now() - timedelta(hours=heures)
    
    donnees = DonneesTrafic.objects.filter(
        capteur=capteur,
        timestamp__gte=date_debut
    ).order_by('timestamp')
    
    data = []
    for donnee in donnees:
        data.append({
            'timestamp': donnee.timestamp.isoformat(),
            'nombre_vehicules': donnee.nombre_vehicules,
            'vitesse_moyenne': donnee.vitesse_moyenne,
            'debit_vehicules': donnee.debit_vehicules,
            'niveau_congestion': donnee.niveau_congestion,
            'taux_occupation': donnee.taux_occupation,
        })
    
    return JsonResponse({
        'capteur': {
            'nom': capteur.nom,
            'code_capteur': capteur.code_capteur,
            'type_capteur': capteur.type_capteur,
        },
        'donnees': data
    })


# ============================================================================
# VUES EXISTANTES (maintenues pour compatibilité) - ADMIN ONLY
# ============================================================================

@admin_required
def monitoring_trafic(request):
    """Monitoring temps réel du trafic - ADMIN ONLY"""
    return redirect('gestion_trafic:liste_capteurs')

@admin_required
def predictions_trafic(request):
    """Prédictions de trafic par IA - ADMIN ONLY"""
    return redirect('gestion_trafic:index_trafic')

@admin_required
def gestion_incidents(request):
    """Gestion des incidents de circulation - ADMIN ONLY"""
    return redirect('gestion_trafic:index_trafic')

@admin_required
def gestion_feux(request):
    """Gestion et optimisation des feux tricolores - ADMIN ONLY"""
    return redirect('gestion_trafic:index_trafic')

@admin_required
def gestion_capteurs(request):
    """Gestion des capteurs de trafic - ADMIN ONLY"""
    return redirect('gestion_trafic:liste_capteurs')

@admin_required
def analytics_trafic(request):
    """Analytics et rapports de trafic - ADMIN ONLY"""
    return redirect('gestion_trafic:index_trafic')

def api_temps_reel(request):
    """API pour données de trafic temps réel"""
    return JsonResponse({
        'status': 'active',
        'message': 'API de trafic temps réel opérationnelle',
        'endpoints': {
            'capteurs': '/trafic/api/capteurs/',
            'donnees_capteur': '/trafic/api/capteur/{id}/donnees/',
        }
    })


# ============================================================================
# CARTOGRAPHIE - VUES - ADMIN ONLY
# ============================================================================

@admin_required
def carte_trafic(request):
    """Affiche la carte interactive du trafic - ADMIN ONLY"""
    zones = ZoneTrafic.objects.all()

    context = {
        'page_title': 'Carte du Trafic',
        'zones': zones,
    }
    return render(request, 'gestion_trafic/carte_trafic.html', context)
