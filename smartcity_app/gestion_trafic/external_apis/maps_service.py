"""
Service de Cartographie - Intégration Google Maps et OpenStreetMap
Gère la visualisation des capteurs, zones et itinéraires sur carte
"""

import requests
import logging
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class GoogleMapsService:
    """Service pour intégrer Google Maps API"""
    
    def __init__(self):
        self.api_key = getattr(settings, 'GOOGLE_MAPS_API_KEY', None)
        self.base_url = "https://maps.googleapis.com/maps/api"
        
        if not self.api_key:
            logger.warning("GOOGLE_MAPS_API_KEY not configured in settings")
    
    def get_directions(self, origin, destination, mode='driving'):
        """
        Obtenir les directions entre deux points
        
        Args:
            origin: Tuple (lat, lon) ou adresse
            destination: Tuple (lat, lon) ou adresse
            mode: 'driving', 'walking', 'bicycling', 'transit'
        
        Returns:
            dict: Directions avec distance, durée, polyline
        """
        if not self.api_key:
            return {'error': 'Google Maps API key not configured'}
        
        try:
            # Formater les coordonnées
            if isinstance(origin, tuple):
                origin_str = f"{origin[0]},{origin[1]}"
            else:
                origin_str = origin
            
            if isinstance(destination, tuple):
                dest_str = f"{destination[0]},{destination[1]}"
            else:
                dest_str = destination
            
            url = f"{self.base_url}/directions/json"
            params = {
                'origin': origin_str,
                'destination': dest_str,
                'mode': mode,
                'key': self.api_key,
                'departure_time': 'now'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] == 'OK':
                route = data['routes'][0]
                return {
                    'success': True,
                    'distance': route['legs'][0]['distance']['text'],
                    'distance_value': route['legs'][0]['distance']['value'],
                    'duration': route['legs'][0]['duration']['text'],
                    'duration_value': route['legs'][0]['duration']['value'],
                    'polyline': route['overview_polyline']['points'],
                    'steps': len(route['legs'][0]['steps'])
                }
            else:
                return {'success': False, 'error': data['status']}
        
        except Exception as e:
            logger.error(f"Error getting directions: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_distance_matrix(self, origins, destinations):
        """
        Obtenir la matrice de distances entre plusieurs points
        
        Args:
            origins: Liste de tuples (lat, lon)
            destinations: Liste de tuples (lat, lon)
        
        Returns:
            dict: Matrice de distances
        """
        if not self.api_key:
            return {'error': 'Google Maps API key not configured'}
        
        try:
            origins_str = '|'.join([f"{o[0]},{o[1]}" for o in origins])
            dests_str = '|'.join([f"{d[0]},{d[1]}" for d in destinations])
            
            url = f"{self.base_url}/distancematrix/json"
            params = {
                'origins': origins_str,
                'destinations': dests_str,
                'key': self.api_key,
                'mode': 'driving'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] == 'OK':
                return {
                    'success': True,
                    'rows': data['rows'],
                    'origin_addresses': data['origin_addresses'],
                    'destination_addresses': data['destination_addresses']
                }
            else:
                return {'success': False, 'error': data['status']}
        
        except Exception as e:
            logger.error(f"Error getting distance matrix: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_geocoding(self, address):
        """
        Convertir une adresse en coordonnées
        
        Args:
            address: Adresse à géocoder
        
        Returns:
            dict: Coordonnées (lat, lon)
        """
        if not self.api_key:
            return {'error': 'Google Maps API key not configured'}
        
        try:
            url = f"{self.base_url}/geocode/json"
            params = {
                'address': address,
                'key': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] == 'OK':
                location = data['results'][0]['geometry']['location']
                return {
                    'success': True,
                    'latitude': location['lat'],
                    'longitude': location['lng'],
                    'formatted_address': data['results'][0]['formatted_address']
                }
            else:
                return {'success': False, 'error': data['status']}
        
        except Exception as e:
            logger.error(f"Error geocoding: {str(e)}")
            return {'success': False, 'error': str(e)}


class OpenStreetMapService:
    """Service pour intégrer OpenStreetMap (Nominatim, Overpass)"""
    
    def __init__(self):
        self.nominatim_url = "https://nominatim.openstreetmap.org"
        self.overpass_url = "https://overpass-api.de/api/interpreter"
    
    def get_geocoding(self, address):
        """
        Convertir une adresse en coordonnées via Nominatim
        
        Args:
            address: Adresse à géocoder
        
        Returns:
            dict: Coordonnées (lat, lon)
        """
        try:
            url = f"{self.nominatim_url}/search"
            params = {
                'q': address,
                'format': 'json',
                'limit': 1
            }
            
            headers = {'User-Agent': 'SmartCity-App/1.0'}
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data:
                result = data[0]
                return {
                    'success': True,
                    'latitude': float(result['lat']),
                    'longitude': float(result['lon']),
                    'display_name': result['display_name']
                }
            else:
                return {'success': False, 'error': 'Address not found'}
        
        except Exception as e:
            logger.error(f"Error geocoding with OSM: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_reverse_geocoding(self, latitude, longitude):
        """
        Convertir des coordonnées en adresse
        
        Args:
            latitude: Latitude
            longitude: Longitude
        
        Returns:
            dict: Adresse
        """
        try:
            url = f"{self.nominatim_url}/reverse"
            params = {
                'lat': latitude,
                'lon': longitude,
                'format': 'json'
            }
            
            headers = {'User-Agent': 'SmartCity-App/1.0'}
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                'success': True,
                'address': data.get('address', {}),
                'display_name': data.get('display_name', '')
            }
        
        except Exception as e:
            logger.error(f"Error reverse geocoding: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_nearby_roads(self, latitude, longitude, radius=1000):
        """
        Obtenir les routes à proximité via Overpass API
        
        Args:
            latitude: Latitude
            longitude: Longitude
            radius: Rayon de recherche en mètres
        
        Returns:
            dict: Routes trouvées
        """
        try:
            # Requête Overpass pour les routes
            query = f"""
            [bbox:{latitude-0.01},{longitude-0.01},{latitude+0.01},{longitude+0.01}];
            (
              way["highway"~"motorway|trunk|primary|secondary|tertiary"];
            );
            out geom;
            """
            
            response = requests.post(
                self.overpass_url,
                data=query,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            
            roads = []
            for way in data.get('elements', []):
                if way['type'] == 'way':
                    roads.append({
                        'id': way['id'],
                        'tags': way.get('tags', {}),
                        'geometry': way.get('geometry', [])
                    })
            
            return {
                'success': True,
                'roads': roads,
                'count': len(roads)
            }
        
        except Exception as e:
            logger.error(f"Error getting nearby roads: {str(e)}")
            return {'success': False, 'error': str(e)}


class MapVisualizationService:
    """Service pour générer les données de visualisation sur carte"""
    
    @staticmethod
    def format_capteurs_for_map(capteurs):
        """
        Formater les capteurs pour affichage sur carte
        
        Args:
            capteurs: QuerySet de CapteurTrafic
        
        Returns:
            list: Données formatées pour GeoJSON
        """
        features = []
        
        for capteur in capteurs:
            feature = {
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [capteur.longitude, capteur.latitude]
                },
                'properties': {
                    'id': capteur.id,
                    'nom': capteur.nom,
                    'type': capteur.type_capteur,
                    'statut': capteur.statut,
                    'zone': capteur.zone_trafic.nom,
                    'precision': capteur.precision_detection,
                    'icon': f'sensor-{capteur.type_capteur}',
                    'color': 'green' if capteur.statut == 'actif' else 'red'
                }
            }
            features.append(feature)
        
        return {
            'type': 'FeatureCollection',
            'features': features
        }
    
    @staticmethod
    def format_zones_for_map(zones):
        """
        Formater les zones pour affichage sur carte
        
        Args:
            zones: QuerySet de ZoneTrafic
        
        Returns:
            list: Données formatées pour GeoJSON
        """
        features = []
        
        for zone in zones:
            feature = {
                'type': 'Feature',
                'properties': {
                    'id': zone.id,
                    'nom': zone.nom,
                    'type': zone.type_zone,
                    'vitesse_limite': zone.vitesse_limite,
                    'nombre_voies': zone.nombre_voies,
                    'color': 'blue'
                }
            }
            features.append(feature)
        
        return {
            'type': 'FeatureCollection',
            'features': features
        }
    
    @staticmethod
    def format_heatmap_data(donnees_trafic):
        """
        Formater les données de trafic pour heatmap
        
        Args:
            donnees_trafic: QuerySet de DonneesTrafic
        
        Returns:
            list: Points pour heatmap
        """
        heatmap_points = []
        
        for donnee in donnees_trafic:
            # Convertir le niveau de congestion en intensité (0-1)
            intensite_map = {
                'fluide': 0.2,
                'dense': 0.4,
                'ralenti': 0.6,
                'bouchon': 0.8,
                'bloque': 1.0
            }
            
            intensity = intensite_map.get(donnee.niveau_congestion, 0.5)
            
            heatmap_points.append({
                'latitude': donnee.capteur.latitude,
                'longitude': donnee.capteur.longitude,
                'intensity': intensity,
                'timestamp': donnee.timestamp.isoformat(),
                'congestion': donnee.niveau_congestion
            })
        
        return heatmap_points

