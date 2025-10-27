"""
API Endpoints Utilisateur - Gestion du Trafic
Fonctionnalités pour les utilisateurs normaux:
- Données de trafic en temps réel pour la carte
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Q, Avg, Count
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import datetime, timedelta
import json

from .models import CapteurTrafic, ZoneTrafic, DonneesTrafic, FeuSignalisation, EvenementTrafic


# ============================================================================
# API ENDPOINT - DONNÉES DE TRAFIC EN TEMPS RÉEL (POUR LA CARTE)
# ============================================================================

@login_required
@require_http_methods(["GET"])
def api_trafic_temps_reel(request):
    """
    API pour récupérer les données de trafic en temps réel
    Retourne les capteurs actifs avec leurs données récentes
    Utilisée par la carte interactive
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

