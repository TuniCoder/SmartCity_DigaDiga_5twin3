"""
API Endpoints pour les Utilisateurs - Gestion du Trafic
Endpoints accessibles aux utilisateurs normaux:
- Données de trafic en temps réel
- Alertes personnalisées
- Zones favorites
- Statistiques personnelles
"""

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.db.models import Avg, Count, Q
from django.utils import timezone
from datetime import timedelta
import json

from .models import CapteurTrafic, ZoneTrafic, DonneesTrafic, FeuSignalisation, EvenementTrafic


# ============================================================================
# DONNÉES TEMPS RÉEL POUR UTILISATEURS (POUR LA CARTE)
# ============================================================================

@login_required
@require_http_methods(["GET"])
def api_trafic_temps_reel(request):
    """
    API: Données de trafic temps réel pour la carte utilisateur
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
            'timestamp': timezone.now().isoformat(),
        })

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e),
        }, status=500)


# ============================================================================
# ALERTES PERSONNALISÉES
# ============================================================================

@login_required
@require_http_methods(["GET"])
def api_mes_alertes(request):
    """API: Récupérer les alertes personnalisées"""
    try:
        zones_favoris = request.session.get('zones_favoris', [])
        
        # Événements dans les zones favorites
        if zones_favoris:
            alertes = EvenementTrafic.objects.filter(
                zones_affectees__id__in=zones_favoris
            ).distinct().order_by('-date_creation')[:20]
        else:
            alertes = EvenementTrafic.objects.order_by('-date_creation')[:20]
        
        data = []
        for alerte in alertes:
            data.append({
                'id': alerte.id,
                'titre': alerte.titre,
                'type': alerte.type_evenement,
                'description': alerte.description,
                'niveau_impact': alerte.niveau_impact,
                'statut': alerte.statut,
                'date_debut': alerte.date_debut.isoformat() if alerte.date_debut else None,
                'date_fin_prevue': alerte.date_fin_prevue.isoformat() if alerte.date_fin_prevue else None,
                'date_creation': alerte.date_creation.isoformat(),
            })
        
        return JsonResponse({
            'success': True,
            'alertes': data,
            'total': len(data),
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
        }, status=500)


# ============================================================================
# ZONES FAVORITES
# ============================================================================

@login_required
@require_http_methods(["GET"])
def api_zones_favoris(request):
    """API: Récupérer les zones favorites"""
    try:
        zones_favoris = request.session.get('zones_favoris', [])
        
        zones = ZoneTrafic.objects.filter(id__in=zones_favoris)
        
        data = []
        for zone in zones:
            data.append({
                'id': zone.id,
                'nom': zone.nom,
                'type_zone': zone.get_type_zone_display(),
                'vitesse_limite': zone.vitesse_limite,
                'nombre_voies': zone.nombre_voies,
            })
        
        return JsonResponse({
            'success': True,
            'zones': data,
            'total': len(data),
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
        }, status=500)


# ============================================================================
# CAPTEURS PROCHES
# ============================================================================

@login_required
@require_http_methods(["GET"])
def api_capteurs_proches(request):
    """API: Récupérer les capteurs proches (basé sur les zones favorites)"""
    try:
        zones_favoris = request.session.get('zones_favoris', [])
        
        if zones_favoris:
            capteurs = CapteurTrafic.objects.filter(
                zone_trafic_id__in=zones_favoris,
                statut='actif'
            )
        else:
            capteurs = CapteurTrafic.objects.filter(statut='actif')[:20]
        
        data = []
        for capteur in capteurs:
            # Dernière donnée du capteur
            derniere_donnee = DonneesTrafic.objects.filter(
                capteur=capteur
            ).order_by('-timestamp').first()
            
            data.append({
                'id': capteur.id,
                'nom': capteur.nom,
                'type': capteur.get_type_capteur_display(),
                'zone': capteur.zone_trafic.nom,
                'latitude': capteur.latitude,
                'longitude': capteur.longitude,
                'statut': capteur.statut,
                'donnees_recentes': {
                    'vitesse_moyenne': derniere_donnee.vitesse_moyenne if derniere_donnee else None,
                    'nombre_vehicules': derniere_donnee.nombre_vehicules if derniere_donnee else None,
                    'niveau_congestion': derniere_donnee.niveau_congestion if derniere_donnee else None,
                    'timestamp': derniere_donnee.timestamp.isoformat() if derniere_donnee else None,
                }
            })
        
        return JsonResponse({
            'success': True,
            'capteurs': data,
            'total': len(data),
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
        }, status=500)


# ============================================================================
# STATISTIQUES PERSONNELLES
# ============================================================================

@login_required
@require_http_methods(["GET"])
def api_mes_statistiques(request):
    """API: Récupérer les statistiques personnalisées"""
    try:
        zones_favoris = request.session.get('zones_favoris', [])
        trajets = request.session.get('mes_trajets', [])
        
        # Statistiques des zones favorites
        zones_stats = []
        if zones_favoris:
            zones = ZoneTrafic.objects.filter(id__in=zones_favoris).annotate(
                avg_congestion=Avg('capteurs__donnees__niveau_congestion'),
                total_capteurs=Count('capteurs')
            )
            
            for zone in zones:
                zones_stats.append({
                    'nom': zone.nom,
                    'congestion_moyenne': round(zone.avg_congestion, 2) if zone.avg_congestion else 0,
                    'nombre_capteurs': zone.total_capteurs,
                })
        
        return JsonResponse({
            'success': True,
            'zones_favoris': len(zones_favoris),
            'nombre_trajets': len(trajets),
            'zones_stats': zones_stats,
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
        }, status=500)


# ============================================================================
# DÉTAIL ZONE POUR UTILISATEUR
# ============================================================================

@login_required
@require_http_methods(["GET"])
def api_detail_zone_user(request, zone_id):
    """API: Récupérer les détails d'une zone"""
    try:
        zone = ZoneTrafic.objects.get(id=zone_id)
        
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
        
        capteurs_data = []
        for capteur in capteurs:
            capteurs_data.append({
                'id': capteur.id,
                'nom': capteur.nom,
                'type': capteur.get_type_capteur_display(),
                'latitude': capteur.latitude,
                'longitude': capteur.longitude,
            })
        
        donnees_data = []
        for donnee in donnees_recentes:
            donnees_data.append({
                'timestamp': donnee.timestamp.isoformat(),
                'vitesse_moyenne': donnee.vitesse_moyenne,
                'nombre_vehicules': donnee.nombre_vehicules,
                'niveau_congestion': donnee.niveau_congestion,
            })
        
        evenements_data = []
        for evt in evenements:
            evenements_data.append({
                'type': evt.type_evenement,
                'description': evt.description,
                'niveau_impact': evt.niveau_impact,
                'date': evt.date_creation.isoformat(),
            })
        
        return JsonResponse({
            'success': True,
            'zone': {
                'id': zone.id,
                'nom': zone.nom,
                'type_zone': zone.get_type_zone_display(),
                'vitesse_limite': zone.vitesse_limite,
                'nombre_voies': zone.nombre_voies,
                'coordonnees': zone.coordonnees_zone,
            },
            'capteurs': capteurs_data,
            'donnees_recentes': donnees_data,
            'evenements': evenements_data,
        })
    
    except ZoneTrafic.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Zone non trouvée',
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
        }, status=500)
