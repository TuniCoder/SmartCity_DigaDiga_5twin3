"""
Vues Utilisateur - Gestion du Trafic
Fonctionnalités pour les utilisateurs normaux:
- Carte interactive du trafic (SEULE FONCTIONNALITÉ POUR LES USERS)
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Q, Avg, Count
from django.utils import timezone
from datetime import datetime, timedelta
import json

from .models import CapteurTrafic, ZoneTrafic, DonneesTrafic, FeuSignalisation, EvenementTrafic


# ============================================================================
# CARTE INTERACTIVE - UTILISATEUR
# ============================================================================

@login_required
def carte_trafic_user(request):
    """
    Affiche la carte interactive du trafic pour les utilisateurs normaux
    - Visualisation des capteurs en temps réel
    - Filtres par type de capteur
    - Codes couleur par niveau de congestion
    - Légende interactive
    """
    zones = ZoneTrafic.objects.all()
    capteurs = CapteurTrafic.objects.filter(statut='actif').select_related('zone_trafic')
    
    context = {
        'page_title': 'Carte du Trafic',
        'zones': zones,
        'capteurs': capteurs,
        'total_capteurs': capteurs.count(),
        'total_zones': zones.count(),
    }
    return render(request, 'gestion_trafic/user/carte_trafic_user.html', context)


# ============================================================================
# API ENDPOINTS - UTILISATEUR
# ============================================================================

@login_required
def api_trafic_temps_reel(request):
    """
    API pour récupérer les données de trafic en temps réel
    Retourne les capteurs actifs avec leurs données récentes
    """
    try:
        capteurs = CapteurTrafic.objects.filter(statut='actif').select_related('zone_trafic')
        
        data = []
        for capteur in capteurs:
            # Dernière donnée du capteur
            derniere_donnee = DonneesTrafic.objects.filter(
                capteur=capteur
            ).order_by('-timestamp').first()
            
            capteur_data = {
                'id': capteur.id,
                'nom': capteur.nom,
                'type': capteur.type_capteur,
                'latitude': float(capteur.latitude),
                'longitude': float(capteur.longitude),
                'zone': capteur.zone_trafic.nom if capteur.zone_trafic else 'N/A',
                'statut': capteur.statut,
            }
            
            if derniere_donnee:
                capteur_data.update({
                    'congestion': derniere_donnee.niveau_congestion,
                    'vehicules': derniere_donnee.nombre_vehicules,
                    'vitesse': derniere_donnee.vitesse_moyenne,
                    'timestamp': derniere_donnee.timestamp.isoformat(),
                })
            else:
                capteur_data.update({
                    'congestion': 0,
                    'vehicules': 0,
                    'vitesse': 0,
                    'timestamp': None,
                })
            
            data.append(capteur_data)
        
        return JsonResponse({
            'status': 'success',
            'count': len(data),
            'capteurs': data,
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e),
        }, status=500)


@login_required
def api_zones_trafic(request):
    """
    API pour récupérer les zones de trafic
    """
    try:
        zones = ZoneTrafic.objects.all()
        
        data = []
        for zone in zones:
            # Statistiques de la zone
            capteurs_zone = CapteurTrafic.objects.filter(zone_trafic=zone, statut='actif')
            
            if capteurs_zone.exists():
                avg_congestion = DonneesTrafic.objects.filter(
                    capteur__in=capteurs_zone
                ).aggregate(avg=Avg('niveau_congestion'))['avg'] or 0
            else:
                avg_congestion = 0
            
            zone_data = {
                'id': zone.id,
                'nom': zone.nom,
                'type': zone.type_zone,
                'latitude': float(zone.latitude),
                'longitude': float(zone.longitude),
                'capteurs_count': capteurs_zone.count(),
                'congestion_moyenne': round(avg_congestion, 2),
            }
            
            data.append(zone_data)
        
        return JsonResponse({
            'status': 'success',
            'count': len(data),
            'zones': data,
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e),
        }, status=500)


@login_required
def api_capteurs_proches(request):
    """
    API pour récupérer les capteurs proches de l'utilisateur
    Paramètres: latitude, longitude, distance (en km)
    """
    try:
        latitude = float(request.GET.get('latitude', 0))
        longitude = float(request.GET.get('longitude', 0))
        distance = float(request.GET.get('distance', 5))  # 5 km par défaut
        
        # Récupérer les capteurs actifs
        capteurs = CapteurTrafic.objects.filter(statut='actif').select_related('zone_trafic')
        
        # Filtrer par distance (approximation simple)
        capteurs_proches = []
        for capteur in capteurs:
            # Distance approximative en km
            lat_diff = abs(float(capteur.latitude) - latitude)
            lon_diff = abs(float(capteur.longitude) - longitude)
            approx_distance = (lat_diff ** 2 + lon_diff ** 2) ** 0.5 * 111  # 111 km par degré
            
            if approx_distance <= distance:
                derniere_donnee = DonneesTrafic.objects.filter(
                    capteur=capteur
                ).order_by('-timestamp').first()
                
                capteur_data = {
                    'id': capteur.id,
                    'nom': capteur.nom,
                    'type': capteur.type_capteur,
                    'latitude': float(capteur.latitude),
                    'longitude': float(capteur.longitude),
                    'distance': round(approx_distance, 2),
                    'congestion': derniere_donnee.niveau_congestion if derniere_donnee else 0,
                }
                capteurs_proches.append(capteur_data)
        
        return JsonResponse({
            'status': 'success',
            'count': len(capteurs_proches),
            'capteurs': capteurs_proches,
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e),
        }, status=500)

