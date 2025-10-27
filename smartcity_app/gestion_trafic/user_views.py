"""
Vues Utilisateur - Gestion du Trafic
Fonctionnalités pour les utilisateurs normaux:
- Tableau de bord personnel
- Carte interactive du trafic
- Alertes personnalisées
- Gestion des trajets
- Planification de trajets
- Statistiques personnelles
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Q, Avg, Count, Max
from django.utils import timezone
from datetime import datetime, timedelta
import json

from .models import CapteurTrafic, ZoneTrafic, DonneesTrafic, FeuSignalisation, EvenementTrafic


# ============================================================================
# TABLEAU DE BORD PERSONNEL
# ============================================================================

@login_required
def dashboard_trafic(request):
    """
    Tableau de bord personnel du trafic
    Affiche un aperçu personnalisé:
    - Statistiques en temps réel
    - Zones congestionnées
    - Événements récents
    - Capteurs proches
    """
    # Statistiques globales
    capteurs_actifs = CapteurTrafic.objects.filter(statut='actif').count()
    zones_actives_count = ZoneTrafic.objects.annotate(
        capteurs_count=Count('capteurs')
    ).filter(capteurs_count__gt=0).count()
    
    # Zones favorites de l'utilisateur
    zones_favoris_ids = request.session.get('zones_favoris', [])
    zones_favoris = ZoneTrafic.objects.filter(id__in=zones_favoris_ids)
    
    # Zones avec activité récente (avec capteurs actifs)
    zones_congestionnees = ZoneTrafic.objects.annotate(
        capteurs_count=Count('capteurs', filter=Q(capteurs__statut='actif'))
    ).filter(capteurs_count__gt=0).order_by('-capteurs_count')[:5]
    
    # Événements récents
    evenements_recents = EvenementTrafic.objects.filter(
        statut='en_cours'
    ).prefetch_related('zones_affectees').order_by('-date_creation')[:5]
    
    # Alertes personnalisées (basées sur zones favorites)
    alertes = []
    if zones_favoris_ids:
        alertes = EvenementTrafic.objects.filter(
            zones_affectees__id__in=zones_favoris_ids,
            statut='en_cours'
        ).prefetch_related('zones_affectees').distinct().order_by('-date_creation')[:5]
    
    # Capteurs proches (basés sur zones favorites)
    if zones_favoris_ids:
        capteurs_proches = CapteurTrafic.objects.filter(
            zone_trafic__id__in=zones_favoris_ids,
            statut='actif'
        ).select_related('zone_trafic')[:10]
    else:
        # Si pas de favoris, afficher les premiers capteurs actifs
        capteurs_proches = CapteurTrafic.objects.filter(statut='actif').select_related('zone_trafic')[:10]
    
    context = {
        'page_title': 'Mon Tableau de Bord - Trafic',
        'total_capteurs': capteurs_actifs,
        'zones_actives': zones_actives_count,
        'zones_congestionnees': zones_congestionnees,
        'zones_denses': zones_congestionnees,  # Alias pour le template
        'evenements_recents': evenements_recents,
        'alertes': alertes,
        'zones_favoris': zones_favoris,
        'capteurs_proches': capteurs_proches,
    }
    
    return render(request, 'gestion_trafic/user/dashboard_trafic.html', context)


# ============================================================================
# CARTE INTERACTIVE
# ============================================================================

@login_required
def carte_trafic_user(request):
    """
    Carte interactive du trafic pour les utilisateurs normaux
    - Visualisation des capteurs en temps réel
    - Filtres par type de capteur
    - Codes couleur par niveau de congestion
    - Légende interactive
    """
    zones = ZoneTrafic.objects.all()
    capteurs = CapteurTrafic.objects.filter(statut='actif').select_related('zone_trafic')
    
    # Zones favorites
    zones_favoris_ids = request.session.get('zones_favoris', [])
    
    context = {
        'page_title': 'Carte du Trafic',
        'zones': zones,
        'capteurs': capteurs,
        'total_capteurs': capteurs.count(),
        'total_zones': zones.count(),
        'zones_favoris_ids': zones_favoris_ids,
    }
    
    return render(request, 'gestion_trafic/user/carte_trafic_user.html', context)


# ============================================================================
# MES ALERTES
# ============================================================================

@login_required
def mes_alertes(request):
    """
    Affiche les alertes personnalisées de l'utilisateur
    Filtrées par zones favorites
    """
    zones_favoris_ids = request.session.get('zones_favoris', [])
    
    # Alertes pour zones favorites
    if zones_favoris_ids:
        alertes = EvenementTrafic.objects.filter(
            zones_affectees__id__in=zones_favoris_ids
        ).distinct().order_by('-date_creation')
    else:
        # Si pas de zones favorites, afficher toutes les alertes
        alertes = EvenementTrafic.objects.all().order_by('-date_creation')
    
    # Filtres
    filter_severite = request.GET.get('severite', '')
    filter_type = request.GET.get('type', '')
    filter_statut = request.GET.get('statut', '')
    
    if filter_severite:
        alertes = alertes.filter(niveau_impact=filter_severite)
    if filter_type:
        alertes = alertes.filter(type_evenement=filter_type)
    if filter_statut:
        alertes = alertes.filter(statut=filter_statut)
    
    context = {
        'page_title': 'Mes Alertes - Trafic',
        'alertes': alertes,
        'zones_favoris_count': len(zones_favoris_ids),
    }
    
    return render(request, 'gestion_trafic/user/mes_alertes.html', context)


# ============================================================================
# MES TRAJETS
# ============================================================================

@login_required
def mes_trajets(request):
    """
    Affiche les trajets de l'utilisateur
    """
    # Récupérer les trajets de la session
    trajets = request.session.get('mes_trajets', [])
    
    context = {
        'page_title': 'Mes Trajets - Trafic',
        'trajets': trajets,
        'trajets_count': len(trajets),
    }
    
    return render(request, 'gestion_trafic/user/mes_trajets.html', context)


# ============================================================================
# PLANIFIER UN TRAJET
# ============================================================================

@login_required
def planifier_trajet(request):
    """
    Permet de planifier un trajet
    """
    if request.method == 'POST':
        lieu_depart = request.POST.get('lieu_depart')
        lieu_arrivee = request.POST.get('lieu_arrivee')
        date_heure = request.POST.get('date_heure')
        criteres = request.POST.getlist('criteres')
        
        if lieu_depart and lieu_arrivee:
            # Ajouter le trajet à la session
            mes_trajets = request.session.get('mes_trajets', [])
            trajet = {
                'id': len(mes_trajets) + 1,
                'lieu_depart': lieu_depart,
                'lieu_arrivee': lieu_arrivee,
                'date_heure': date_heure,
                'criteres': criteres,
                'statut': 'planifie',
                'date_creation': timezone.now().isoformat(),
            }
            mes_trajets.append(trajet)
            request.session['mes_trajets'] = mes_trajets
            
            messages.success(request, 'Trajet planifié avec succès!')
            return redirect('gestion_trafic:mes_trajets')
        else:
            messages.error(request, 'Veuillez remplir tous les champs obligatoires.')
    
    context = {
        'page_title': 'Planifier un Trajet - Trafic',
    }
    
    return render(request, 'gestion_trafic/user/planifier_trajet.html', context)


# ============================================================================
# MES STATISTIQUES
# ============================================================================

@login_required
def mes_statistiques(request):
    """
    Affiche les statistiques personnelles de l'utilisateur
    """
    zones_favoris_ids = request.session.get('zones_favoris', [])
    trajets = request.session.get('mes_trajets', [])
    
    # Statistiques des zones favorites
    zones_stats = []
    if zones_favoris_ids:
        zones = ZoneTrafic.objects.filter(id__in=zones_favoris_ids).annotate(
            avg_congestion=Avg('capteurs__donnees__niveau_congestion'),
            total_capteurs=Count('capteurs')
        )
        
        for zone in zones:
            zones_stats.append({
                'nom': zone.nom,
                'congestion_moyenne': zone.avg_congestion or 0,
                'nombre_capteurs': zone.total_capteurs,
            })
    
    context = {
        'page_title': 'Mes Statistiques - Trafic',
        'zones_stats': zones_stats,
        'trajets_count': len(trajets),
        'zones_favoris_count': len(zones_favoris_ids),
    }
    
    return render(request, 'gestion_trafic/user/mes_statistiques.html', context)


# ============================================================================
# DÉTAIL ZONE
# ============================================================================

@login_required
def detail_zone_user(request, zone_id):
    """
    Affiche les détails d'une zone de trafic
    """
    zone = get_object_or_404(ZoneTrafic, id=zone_id)
    
    # Capteurs de la zone
    capteurs = zone.capteurs.filter(statut='actif')
    
    # Données récentes
    donnees_recentes = DonneesTrafic.objects.filter(
        capteur__zone_trafic=zone
    ).order_by('-timestamp')[:10]
    
    # Événements récents
    evenements = EvenementTrafic.objects.filter(
        zones_affectees=zone
    ).order_by('-date_creation')[:5]
    
    # Vérifier si zone favorite
    zones_favoris_ids = request.session.get('zones_favoris', [])
    est_favorite = zone.id in zones_favoris_ids
    
    context = {
        'page_title': f'{zone.nom} - Détails',
        'zone': zone,
        'capteurs': capteurs,
        'donnees_recentes': donnees_recentes,
        'evenements': evenements,
        'est_favorite': est_favorite,
    }
    
    return render(request, 'gestion_trafic/user/detail_zone_user.html', context)


# ============================================================================
# ZONES FAVORITES
# ============================================================================

@login_required
def ajouter_zone_favorite(request, zone_id):
    """
    Ajouter une zone aux favoris
    """
    zone = get_object_or_404(ZoneTrafic, id=zone_id)
    
    zones_favoris = request.session.get('zones_favoris', [])
    if zone.id not in zones_favoris:
        zones_favoris.append(zone.id)
        request.session['zones_favoris'] = zones_favoris
        messages.success(request, f'Zone "{zone.nom}" ajoutée aux favoris.')
    else:
        messages.info(request, f'Zone "{zone.nom}" est déjà dans vos favoris.')
    
    return redirect('gestion_trafic:detail_zone_user', zone_id=zone.id)


@login_required
def retirer_zone_favorite(request, zone_id):
    """
    Retirer une zone des favoris
    """
    zone = get_object_or_404(ZoneTrafic, id=zone_id)
    
    zones_favoris = request.session.get('zones_favoris', [])
    if zone.id in zones_favoris:
        zones_favoris.remove(zone.id)
        request.session['zones_favoris'] = zones_favoris
        messages.success(request, f'Zone "{zone.nom}" retirée des favoris.')
    else:
        messages.info(request, f'Zone "{zone.nom}" n\'est pas dans vos favoris.')
    
    return redirect('gestion_trafic:detail_zone_user', zone_id=zone.id)
