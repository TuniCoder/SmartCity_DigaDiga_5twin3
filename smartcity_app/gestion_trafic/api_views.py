"""
API Views pour la Gestion du Trafic
Endpoints REST pour capteurs, données de trafic, feux et événements
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q, Count, Avg, Max, Min
from django.utils import timezone
from datetime import timedelta
import logging

from .models import CapteurTrafic, DonneesTrafic, FeuSignalisation, EvenementTrafic, ZoneTrafic
from .rdf_integration import add_capteur_to_rdf
from .external_apis.maps_service import (
    GoogleMapsService,
    OpenStreetMapService,
    MapVisualizationService
)

logger = logging.getLogger(__name__)


# ============================================================================
# CAPTEURS DE TRAFIC - ENDPOINTS
# ============================================================================

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def api_capteurs(request):
    """
    GET: Liste tous les capteurs avec filtrage optionnel
    POST: Crée un nouveau capteur

    Filtres disponibles:
    - statut: actif, inactif, maintenance, defaillant
    - type_capteur: boucle_magnetique, camera_ia, radar, lidar, etc.
    - zone_id: ID de la zone de trafic
    - precision_min: Précision minimale (%)
    """

    if request.method == 'GET':
        capteurs = CapteurTrafic.objects.select_related('zone_trafic').all()

        # Filtrage
        statut = request.GET.get('statut')
        if statut:
            capteurs = capteurs.filter(statut=statut)

        type_capteur = request.GET.get('type_capteur')
        if type_capteur:
            capteurs = capteurs.filter(type_capteur=type_capteur)

        zone_id = request.GET.get('zone_id')
        if zone_id:
            capteurs = capteurs.filter(zone_trafic_id=zone_id)

        precision_min = request.GET.get('precision_min')
        if precision_min:
            capteurs = capteurs.filter(precision_detection__gte=float(precision_min))

        # Sérialisation
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
                'zone_id': capteur.zone_trafic.id,
                'direction_mesure': capteur.direction_mesure,
                'frequence_mesure': capteur.frequence_mesure,
                'precision_detection': capteur.precision_detection,
                'vitesse_min_detection': capteur.vitesse_min_detection,
                'vitesse_max_detection': capteur.vitesse_max_detection,
                'fournisseur': capteur.fournisseur,
                'modele': capteur.modele,
                'date_installation': capteur.date_installation.isoformat(),
                'est_operationnel': capteur.est_operationnel
            })

        return Response({
            'success': True,
            'count': len(data),
            'capteurs': data
        }, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        try:
            data = request.data

            # Validation
            required_fields = ['nom', 'code_capteur', 'type_capteur', 'zone_id',
                             'latitude', 'longitude', 'direction_mesure', 'date_installation']
            missing = [f for f in required_fields if not data.get(f)]
            if missing:
                return Response({
                    'success': False,
                    'error': f'Champs manquants: {", ".join(missing)}'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Créer le capteur
            zone = ZoneTrafic.objects.get(id=data['zone_id'])
            capteur = CapteurTrafic.objects.create(
                nom=data['nom'],
                code_capteur=data['code_capteur'],
                type_capteur=data['type_capteur'],
                zone_trafic=zone,
                latitude=float(data['latitude']),
                longitude=float(data['longitude']),
                direction_mesure=data['direction_mesure'],
                date_installation=data['date_installation'],
                frequence_mesure=int(data.get('frequence_mesure', 60)),
                precision_detection=float(data.get('precision_detection', 95.0)),
                vitesse_min_detection=int(data.get('vitesse_min_detection', 5)),
                vitesse_max_detection=int(data.get('vitesse_max_detection', 200)),
                fournisseur=data.get('fournisseur', ''),
                modele=data.get('modele', ''),
                statut=data.get('statut', 'actif')
            )

            # Ajouter au RDF
            add_capteur_to_rdf(capteur)

            return Response({
                'success': True,
                'message': 'Capteur créé avec succès',
                'capteur_id': capteur.id,
                'capteur': {
                    'id': capteur.id,
                    'nom': capteur.nom,
                    'code_capteur': capteur.code_capteur
                }
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Erreur création capteur: {str(e)}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([AllowAny])
def api_capteur_detail(request, capteur_id):
    """
    GET: Détails d'un capteur
    PUT: Modifier un capteur
    DELETE: Supprimer un capteur
    """

    try:
        capteur = CapteurTrafic.objects.get(id=capteur_id)
    except CapteurTrafic.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Capteur non trouvé'
        }, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response({
            'success': True,
            'capteur': {
                'id': capteur.id,
                'nom': capteur.nom,
                'code_capteur': capteur.code_capteur,
                'type_capteur': capteur.type_capteur,
                'statut': capteur.statut,
                'latitude': capteur.latitude,
                'longitude': capteur.longitude,
                'zone_trafic': capteur.zone_trafic.nom,
                'direction_mesure': capteur.direction_mesure,
                'frequence_mesure': capteur.frequence_mesure,
                'precision_detection': capteur.precision_detection,
                'vitesse_min_detection': capteur.vitesse_min_detection,
                'vitesse_max_detection': capteur.vitesse_max_detection,
                'fournisseur': capteur.fournisseur,
                'modele': capteur.modele,
                'date_installation': capteur.date_installation.isoformat(),
                'derniere_calibration': capteur.derniere_calibration.isoformat() if capteur.derniere_calibration else None,
                'prochaine_maintenance': capteur.prochaine_maintenance.isoformat() if capteur.prochaine_maintenance else None,
                'est_operationnel': capteur.est_operationnel
            }
        }, status=status.HTTP_200_OK)

    elif request.method == 'PUT':
        try:
            data = request.data

            # Mise à jour des champs
            if 'nom' in data:
                capteur.nom = data['nom']
            if 'statut' in data:
                capteur.statut = data['statut']
            if 'precision_detection' in data:
                capteur.precision_detection = float(data['precision_detection'])
            if 'frequence_mesure' in data:
                capteur.frequence_mesure = int(data['frequence_mesure'])

            capteur.save()

            return Response({
                'success': True,
                'message': 'Capteur mis à jour avec succès',
                'capteur_id': capteur.id
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        capteur.delete()
        return Response({
            'success': True,
            'message': 'Capteur supprimé avec succès'
        }, status=status.HTTP_204_NO_CONTENT)


# ============================================================================
# DONNÉES DE TRAFIC - ENDPOINTS
# ============================================================================

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def api_donnees_trafic(request):
    """
    GET: Récupère les données de trafic récentes
    POST: Enregistre de nouvelles données de trafic

    Filtres GET:
    - capteur_id: ID du capteur
    - zone_id: ID de la zone
    - heures: Nombre d'heures à récupérer (défaut: 24)
    - niveau_congestion: fluide, dense, ralenti, bouchon, bloque
    """

    if request.method == 'GET':
        heures = int(request.GET.get('heures', 24))
        depuis = timezone.now() - timedelta(hours=heures)

        donnees = DonneesTrafic.objects.filter(timestamp__gte=depuis)

        capteur_id = request.GET.get('capteur_id')
        if capteur_id:
            donnees = donnees.filter(capteur_id=capteur_id)

        zone_id = request.GET.get('zone_id')
        if zone_id:
            donnees = donnees.filter(capteur__zone_trafic_id=zone_id)

        niveau = request.GET.get('niveau_congestion')
        if niveau:
            donnees = donnees.filter(niveau_congestion=niveau)

        donnees = donnees.select_related('capteur').order_by('-timestamp')[:1000]

        data = []
        for d in donnees:
            data.append({
                'id': d.id,
                'capteur': d.capteur.nom,
                'capteur_id': d.capteur.id,
                'timestamp': d.timestamp.isoformat(),
                'nombre_vehicules': d.nombre_vehicules,
                'vitesse_moyenne': d.vitesse_moyenne,
                'vitesse_mediane': d.vitesse_mediane,
                'debit_vehicules': d.debit_vehicules,
                'niveau_congestion': d.niveau_congestion,
                'taux_occupation': d.taux_occupation,
                'vehicules_legers': d.vehicules_legers,
                'vehicules_lourds': d.vehicules_lourds,
                'deux_roues': d.deux_roues,
                'transports_publics': d.transports_publics,
                'incident_detecte': d.incident_detecte,
                'type_incident': d.type_incident,
                'conditions_meteo': d.conditions_meteo,
                'temperature': d.temperature
            })

        return Response({
            'success': True,
            'count': len(data),
            'donnees': data
        }, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        try:
            data = request.data

            required = ['capteur_id', 'timestamp', 'nombre_vehicules', 'niveau_congestion', 'taux_occupation']
            missing = [f for f in required if not data.get(f)]
            if missing:
                return Response({
                    'success': False,
                    'error': f'Champs manquants: {", ".join(missing)}'
                }, status=status.HTTP_400_BAD_REQUEST)

            capteur = CapteurTrafic.objects.get(id=data['capteur_id'])

            donnee = DonneesTrafic.objects.create(
                capteur=capteur,
                timestamp=data['timestamp'],
                nombre_vehicules=int(data['nombre_vehicules']),
                vitesse_moyenne=float(data.get('vitesse_moyenne', 0)) or None,
                vitesse_mediane=float(data.get('vitesse_mediane', 0)) or None,
                debit_vehicules=float(data.get('debit_vehicules', 0)) or None,
                vehicules_legers=int(data.get('vehicules_legers', 0)),
                vehicules_lourds=int(data.get('vehicules_lourds', 0)),
                deux_roues=int(data.get('deux_roues', 0)),
                transports_publics=int(data.get('transports_publics', 0)),
                niveau_congestion=data['niveau_congestion'],
                taux_occupation=float(data['taux_occupation']),
                conditions_meteo=data.get('conditions_meteo', ''),
                visibilite=int(data.get('visibilite', 0)) or None,
                temperature=float(data.get('temperature', 0)) or None,
                incident_detecte=data.get('incident_detecte', False),
                type_incident=data.get('type_incident', '')
            )

            return Response({
                'success': True,
                'message': 'Données enregistrées avec succès',
                'donnee_id': donnee.id
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Erreur enregistrement données: {str(e)}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ============================================================================
# STATISTIQUES ET ANALYTICS
# ============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def api_statistiques_trafic(request):
    """
    Récupère les statistiques de trafic

    Paramètres:
    - zone_id: Filtrer par zone
    - heures: Nombre d'heures à analyser (défaut: 24)
    """

    heures = int(request.GET.get('heures', 24))
    depuis = timezone.now() - timedelta(hours=heures)

    donnees = DonneesTrafic.objects.filter(timestamp__gte=depuis)

    zone_id = request.GET.get('zone_id')
    if zone_id:
        donnees = donnees.filter(capteur__zone_trafic_id=zone_id)

    stats = {
        'total_mesures': donnees.count(),
        'vitesse_moyenne_globale': donnees.aggregate(Avg('vitesse_moyenne'))['vitesse_moyenne__avg'],
        'vitesse_max': donnees.aggregate(Max('vitesse_moyenne'))['vitesse_moyenne__max'],
        'vitesse_min': donnees.aggregate(Min('vitesse_moyenne'))['vitesse_moyenne__min'],
        'taux_occupation_moyen': donnees.aggregate(Avg('taux_occupation'))['taux_occupation__avg'],
        'incidents_detectes': donnees.filter(incident_detecte=True).count(),
        'distribution_congestion': dict(donnees.values('niveau_congestion').annotate(count=Count('id')).values_list('niveau_congestion', 'count')),
        'capteurs_actifs': CapteurTrafic.objects.filter(statut='actif').count(),
        'capteurs_total': CapteurTrafic.objects.count()
    }

    return Response({
        'success': True,
        'periode_heures': heures,
        'statistiques': stats
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def api_zones_trafic(request):
    """Liste toutes les zones de trafic avec statistiques"""

    zones = ZoneTrafic.objects.all()

    data = []
    for zone in zones:
        capteurs = zone.capteurs.all()
        data.append({
            'id': zone.id,
            'nom': zone.nom,
            'type_zone': zone.type_zone,
            'vitesse_limite': zone.vitesse_limite,
            'nombre_voies': zone.nombre_voies,
            'nombre_capteurs': capteurs.count(),
            'capteurs_actifs': capteurs.filter(statut='actif').count(),
            'zone_pietons': zone.zone_pietons
        })

    return Response({
        'success': True,
        'count': len(data),
        'zones': data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def api_feux_signalisation(request):
    """Liste tous les feux de signalisation"""

    feux = FeuSignalisation.objects.select_related('zone_trafic').all()

    zone_id = request.GET.get('zone_id')
    if zone_id:
        feux = feux.filter(zone_trafic_id=zone_id)

    data = []
    for feu in feux:
        data.append({
            'id': feu.id,
            'nom': feu.nom,
            'code_feu': feu.code_feu,
            'type_feu': feu.type_feu,
            'carrefour': feu.carrefour,
            'latitude': feu.latitude,
            'longitude': feu.longitude,
            'zone_trafic': feu.zone_trafic.nom,
            'mode_fonctionnement': feu.mode_fonctionnement,
            'phase_actuelle': feu.phase_actuelle,
            'statut': feu.statut,
            'priorite_pietons': feu.priorite_pietons,
            'priorite_transports': feu.priorite_transports
        })

    return Response({
        'success': True,
        'count': len(data),
        'feux': data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def api_evenements_trafic(request):
    """Liste les événements de trafic"""

    statut = request.GET.get('statut', 'en_cours')
    evenements = EvenementTrafic.objects.filter(statut=statut).prefetch_related('zones_affectees')

    data = []
    for evt in evenements:
        data.append({
            'id': evt.id,
            'titre': evt.titre,
            'type_evenement': evt.type_evenement,
            'description': evt.description,
            'niveau_impact': evt.niveau_impact,
            'date_debut': evt.date_debut.isoformat(),
            'date_fin_prevue': evt.date_fin_prevue.isoformat(),
            'statut': evt.statut,
            'zones_affectees': [z.nom for z in evt.zones_affectees.all()],
            'deviations_proposees': evt.deviations_proposees,
            'recommandations': evt.recommandations
        })

    return Response({
        'success': True,
        'count': len(data),
        'evenements': data
    }, status=status.HTTP_200_OK)



# ============================================================================
# CARTOGRAPHIE - ENDPOINTS (Google Maps & OpenStreetMap)
# ============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def api_maps_capteurs(request):
    """
    Récupère les capteurs formatés pour affichage sur carte (GeoJSON)

    Paramètres:
    - zone_id: Filtrer par zone
    - statut: Filtrer par statut (actif, inactif, etc.)
    - type_capteur: Filtrer par type

    Retourne: GeoJSON FeatureCollection
    """
    try:
        capteurs = CapteurTrafic.objects.select_related('zone_trafic').all()

        # Filtrage
        zone_id = request.GET.get('zone_id')
        if zone_id:
            capteurs = capteurs.filter(zone_trafic_id=zone_id)

        statut = request.GET.get('statut')
        if statut:
            capteurs = capteurs.filter(statut=statut)

        type_capteur = request.GET.get('type_capteur')
        if type_capteur:
            capteurs = capteurs.filter(type_capteur=type_capteur)

        # Formater pour GeoJSON
        geojson = MapVisualizationService.format_capteurs_for_map(capteurs)

        return Response({
            'success': True,
            'count': len(geojson['features']),
            'data': geojson
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error in api_maps_capteurs: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def api_maps_zones(request):
    """
    Récupère les zones de trafic formatées pour affichage sur carte

    Retourne: GeoJSON FeatureCollection
    """
    try:
        zones = ZoneTrafic.objects.all()

        # Formater pour GeoJSON
        geojson = MapVisualizationService.format_zones_for_map(zones)

        return Response({
            'success': True,
            'count': len(geojson['features']),
            'data': geojson
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error in api_maps_zones: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def api_maps_directions(request):
    """
    Calcule les directions entre deux points via Google Maps

    Body JSON:
    {
        "origin": [latitude, longitude] ou "adresse",
        "destination": [latitude, longitude] ou "adresse",
        "mode": "driving" (optionnel)
    }

    Retourne: Directions avec distance, durée, polyline
    """
    try:
        origin = request.data.get('origin')
        destination = request.data.get('destination')
        mode = request.data.get('mode', 'driving')

        if not origin or not destination:
            return Response({
                'success': False,
                'error': 'origin et destination sont requis'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Convertir les adresses en coordonnées si nécessaire
        osm_service = OpenStreetMapService()

        if isinstance(origin, str):
            origin_result = osm_service.get_geocoding(origin)
            if origin_result['success']:
                origin = (origin_result['latitude'], origin_result['longitude'])
            else:
                return Response({
                    'success': False,
                    'error': f"Impossible de géocoder l'origine: {origin}"
                }, status=status.HTTP_400_BAD_REQUEST)

        if isinstance(destination, str):
            dest_result = osm_service.get_geocoding(destination)
            if dest_result['success']:
                destination = (dest_result['latitude'], dest_result['longitude'])
            else:
                return Response({
                    'success': False,
                    'error': f"Impossible de géocoder la destination: {destination}"
                }, status=status.HTTP_400_BAD_REQUEST)

        # Obtenir les directions
        maps_service = GoogleMapsService()
        directions = maps_service.get_directions(origin, destination, mode)

        return Response({
            'success': directions.get('success', False),
            'data': directions
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error in api_maps_directions: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def api_maps_heatmap(request):
    """
    Récupère les données de trafic pour affichage en heatmap

    Paramètres:
    - zone_id: Filtrer par zone
    - heures: Nombre d'heures à récupérer (défaut: 1)

    Retourne: Points pour heatmap avec intensité
    """
    try:
        heures = int(request.GET.get('heures', 1))
        depuis = timezone.now() - timedelta(hours=heures)

        donnees = DonneesTrafic.objects.filter(
            timestamp__gte=depuis
        ).select_related('capteur').order_by('-timestamp')

        zone_id = request.GET.get('zone_id')
        if zone_id:
            donnees = donnees.filter(capteur__zone_trafic_id=zone_id)

        # Formater pour heatmap
        heatmap_data = MapVisualizationService.format_heatmap_data(donnees)

        return Response({
            'success': True,
            'count': len(heatmap_data),
            'data': heatmap_data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error in api_maps_heatmap: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def api_maps_geocoding(request):
    """
    Convertit une adresse en coordonnées (géocodage)

    Body JSON:
    {
        "address": "adresse à géocoder"
    }

    Retourne: Coordonnées (latitude, longitude)
    """
    try:
        address = request.data.get('address')

        if not address:
            return Response({
                'success': False,
                'error': 'address est requis'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Essayer avec OpenStreetMap d'abord (gratuit)
        osm_service = OpenStreetMapService()
        result = osm_service.get_geocoding(address)

        if result['success']:
            return Response({
                'success': True,
                'data': result
            }, status=status.HTTP_200_OK)

        # Sinon essayer avec Google Maps
        maps_service = GoogleMapsService()
        result = maps_service.get_geocoding(address)

        return Response({
            'success': result.get('success', False),
            'data': result
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error in api_maps_geocoding: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def api_maps_reverse_geocoding(request):
    """
    Convertit des coordonnées en adresse (géocodage inverse)

    Body JSON:
    {
        "latitude": 36.8070,
        "longitude": 10.1820
    }

    Retourne: Adresse
    """
    try:
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')

        if latitude is None or longitude is None:
            return Response({
                'success': False,
                'error': 'latitude et longitude sont requis'
            }, status=status.HTTP_400_BAD_REQUEST)

        osm_service = OpenStreetMapService()
        result = osm_service.get_reverse_geocoding(latitude, longitude)

        return Response({
            'success': result.get('success', False),
            'data': result
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error in api_maps_reverse_geocoding: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)