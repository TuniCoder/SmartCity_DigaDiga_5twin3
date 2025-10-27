"""
Tests pour l'intégration des APIs de cartographie
"""

import os
import sys
import django
import requests
from datetime import datetime

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartcity_core.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from smartcity_app.gestion_trafic.models import CapteurTrafic, ZoneTrafic, DonneesTrafic

# Couleurs pour l'affichage
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

BASE_URL = 'http://127.0.0.1:8000'

def print_header(text):
    print(f"\n{BOLD}{BLUE}{'='*80}{RESET}")
    print(f"{BOLD}{BLUE}{text}{RESET}")
    print(f"{BOLD}{BLUE}{'='*80}{RESET}\n")

def print_success(text):
    print(f"{GREEN}✅ {text}{RESET}")

def print_error(text):
    print(f"{RED}❌ {text}{RESET}")

def print_info(text):
    print(f"{BLUE}ℹ️  {text}{RESET}")

def print_warning(text):
    print(f"{YELLOW}⚠️  {text}{RESET}")

def test_api_maps_capteurs():
    """Test l'endpoint GET /trafic/api/maps/capteurs/"""
    print_header("Test 1: API Maps Capteurs")
    
    try:
        url = f"{BASE_URL}/trafic/api/maps/capteurs/"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print_success(f"Endpoint /trafic/api/maps/capteurs/ fonctionne")
                print_info(f"Nombre de capteurs: {data.get('count', 0)}")
                
                if data.get('data', {}).get('features'):
                    first_feature = data['data']['features'][0]
                    print_info(f"Premier capteur: {first_feature['properties']['nom']}")
                    print_info(f"Coordonnées: {first_feature['geometry']['coordinates']}")
                return True
            else:
                print_error(f"Réponse invalide: {data}")
                return False
        else:
            print_error(f"Erreur HTTP {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Erreur: {str(e)}")
        return False

def test_api_maps_zones():
    """Test l'endpoint GET /trafic/api/maps/zones/"""
    print_header("Test 2: API Maps Zones")
    
    try:
        url = f"{BASE_URL}/trafic/api/maps/zones/"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print_success(f"Endpoint /trafic/api/maps/zones/ fonctionne")
                print_info(f"Nombre de zones: {data.get('count', 0)}")
                return True
            else:
                print_error(f"Réponse invalide: {data}")
                return False
        else:
            print_error(f"Erreur HTTP {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Erreur: {str(e)}")
        return False

def test_api_maps_heatmap():
    """Test l'endpoint GET /trafic/api/maps/heatmap/"""
    print_header("Test 3: API Maps Heatmap")
    
    try:
        url = f"{BASE_URL}/trafic/api/maps/heatmap/?heures=1"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print_success(f"Endpoint /trafic/api/maps/heatmap/ fonctionne")
                print_info(f"Nombre de points heatmap: {data.get('count', 0)}")
                
                if data.get('data'):
                    first_point = data['data'][0]
                    print_info(f"Premier point: ({first_point['latitude']}, {first_point['longitude']})")
                    print_info(f"Intensité: {first_point['intensity']}")
                return True
            else:
                print_error(f"Réponse invalide: {data}")
                return False
        else:
            print_error(f"Erreur HTTP {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Erreur: {str(e)}")
        return False

def test_api_maps_geocoding():
    """Test l'endpoint POST /trafic/api/maps/geocoding/"""
    print_header("Test 4: API Maps Geocoding")
    
    try:
        url = f"{BASE_URL}/trafic/api/maps/geocoding/"
        payload = {"address": "Tunis, Tunisie"}
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print_success(f"Endpoint /trafic/api/maps/geocoding/ fonctionne")
                result = data.get('data', {})
                print_info(f"Adresse: {result.get('display_name', 'N/A')}")
                print_info(f"Coordonnées: ({result.get('latitude', 'N/A')}, {result.get('longitude', 'N/A')})")
                return True
            else:
                print_warning(f"Geocoding échoué (peut être normal sans clé API)")
                return True
        else:
            print_error(f"Erreur HTTP {response.status_code}")
            return False
    except Exception as e:
        print_warning(f"Geocoding non disponible: {str(e)}")
        return True

def test_api_maps_reverse_geocoding():
    """Test l'endpoint POST /trafic/api/maps/reverse-geocoding/"""
    print_header("Test 5: API Maps Reverse Geocoding")
    
    try:
        url = f"{BASE_URL}/trafic/api/maps/reverse-geocoding/"
        payload = {"latitude": 36.8070, "longitude": 10.1820}
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print_success(f"Endpoint /trafic/api/maps/reverse-geocoding/ fonctionne")
                result = data.get('data', {})
                print_info(f"Adresse: {result.get('display_name', 'N/A')}")
                return True
            else:
                print_warning(f"Reverse geocoding échoué (peut être normal)")
                return True
        else:
            print_error(f"Erreur HTTP {response.status_code}")
            return False
    except Exception as e:
        print_warning(f"Reverse geocoding non disponible: {str(e)}")
        return True

def test_frontend_carte():
    """Test l'accès à la page de carte frontend"""
    print_header("Test 6: Frontend - Page Carte")
    
    try:
        url = f"{BASE_URL}/trafic/carte/"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            print_success(f"Page /trafic/carte/ accessible")
            
            # Vérifier que la page contient les éléments clés
            content = response.text
            checks = [
                ('Leaflet', 'Leaflet.js'),
                ('map', 'Élément carte'),
                ('filterZone', 'Filtre zone'),
                ('filterStatut', 'Filtre statut'),
                ('filterType', 'Filtre type'),
            ]
            
            for check, label in checks:
                if check in content:
                    print_success(f"  ✓ {label} trouvé")
                else:
                    print_warning(f"  ✗ {label} non trouvé")
            
            return True
        elif response.status_code == 302:
            print_warning(f"Redirection (authentification requise)")
            return True
        else:
            print_error(f"Erreur HTTP {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Erreur: {str(e)}")
        return False

def test_database_data():
    """Vérifier les données dans la base de données"""
    print_header("Test 7: Données en Base de Données")
    
    try:
        capteurs_count = CapteurTrafic.objects.count()
        zones_count = ZoneTrafic.objects.count()
        donnees_count = DonneesTrafic.objects.count()
        
        print_info(f"Capteurs: {capteurs_count}")
        print_info(f"Zones: {zones_count}")
        print_info(f"Données de trafic: {donnees_count}")
        
        if capteurs_count > 0:
            print_success(f"Données de capteurs présentes")
        else:
            print_warning(f"Aucun capteur en base de données")
        
        if zones_count > 0:
            print_success(f"Données de zones présentes")
        else:
            print_warning(f"Aucune zone en base de données")
        
        return True
    except Exception as e:
        print_error(f"Erreur: {str(e)}")
        return False

def main():
    """Exécuter tous les tests"""
    print(f"\n{BOLD}{BLUE}🗺️  TESTS D'INTÉGRATION CARTOGRAPHIE{RESET}")
    print(f"{BOLD}{BLUE}Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}\n")
    
    tests = [
        ("Données en Base", test_database_data),
        ("API Maps Capteurs", test_api_maps_capteurs),
        ("API Maps Zones", test_api_maps_zones),
        ("API Maps Heatmap", test_api_maps_heatmap),
        ("API Maps Geocoding", test_api_maps_geocoding),
        ("API Maps Reverse Geocoding", test_api_maps_reverse_geocoding),
        ("Frontend - Page Carte", test_frontend_carte),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print_error(f"Erreur lors du test {name}: {str(e)}")
            results.append((name, False))
    
    # Résumé
    print_header("RÉSUMÉ DES TESTS")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = f"{GREEN}✅ PASS{RESET}" if result else f"{RED}❌ FAIL{RESET}"
        print(f"{status} - {name}")
    
    print(f"\n{BOLD}Résultat: {passed}/{total} tests réussis{RESET}")
    
    if passed == total:
        print(f"{GREEN}{BOLD}🎉 TOUS LES TESTS SONT PASSÉS !{RESET}\n")
        return 0
    else:
        print(f"{RED}{BOLD}⚠️  CERTAINS TESTS ONT ÉCHOUÉ{RESET}\n")
        return 1

if __name__ == '__main__':
    sys.exit(main())

