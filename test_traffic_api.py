#!/usr/bin/env python
"""
Script de test pour les API REST de gestion du trafic
Teste tous les endpoints disponibles
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://127.0.0.1:8000/trafic/api"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_test(name, success, response=None):
    """Affiche le résultat d'un test"""
    status = f"{Colors.GREEN}✅ PASS{Colors.END}" if success else f"{Colors.RED}❌ FAIL{Colors.END}"
    print(f"{status} - {name}")
    if response and not success:
        print(f"  Erreur: {response}")

def test_api():
    """Teste tous les endpoints API"""
    
    print(f"\n{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BLUE}🚗 TEST DES API REST - GESTION DU TRAFIC{Colors.END}")
    print(f"{Colors.BLUE}{'='*80}{Colors.END}\n")
    
    tests_passed = 0
    tests_failed = 0
    
    # ========================================================================
    # TEST 1: Lister les capteurs
    # ========================================================================
    print(f"\n{Colors.YELLOW}📋 TEST 1: Lister les capteurs{Colors.END}")
    try:
        response = requests.get(f"{BASE_URL}/capteurs/")
        success = response.status_code == 200
        print_test("GET /capteurs/", success, response.text if not success else None)
        
        if success:
            data = response.json()
            print(f"  ✓ Nombre de capteurs: {data['count']}")
            tests_passed += 1
        else:
            tests_failed += 1
    except Exception as e:
        print_test("GET /capteurs/", False, str(e))
        tests_failed += 1
    
    # ========================================================================
    # TEST 2: Filtrer les capteurs par statut
    # ========================================================================
    print(f"\n{Colors.YELLOW}📋 TEST 2: Filtrer les capteurs par statut{Colors.END}")
    try:
        response = requests.get(f"{BASE_URL}/capteurs/?statut=actif")
        success = response.status_code == 200
        print_test("GET /capteurs/?statut=actif", success)
        
        if success:
            data = response.json()
            print(f"  ✓ Capteurs actifs: {data['count']}")
            tests_passed += 1
        else:
            tests_failed += 1
    except Exception as e:
        print_test("GET /capteurs/?statut=actif", False, str(e))
        tests_failed += 1
    
    # ========================================================================
    # TEST 3: Créer un nouveau capteur
    # ========================================================================
    print(f"\n{Colors.YELLOW}📋 TEST 3: Créer un nouveau capteur{Colors.END}")
    try:
        capteur_data = {
            "nom": "Capteur Test API",
            "code_capteur": f"API-TEST-{datetime.now().timestamp()}",
            "type_capteur": "camera_ia",
            "zone_id": 1,
            "latitude": 36.8070,
            "longitude": 10.1820,
            "direction_mesure": "Est-Ouest",
            "date_installation": "2025-10-27",
            "frequence_mesure": 60,
            "precision_detection": 97.5,
            "fournisseur": "SmartCity API",
            "modele": "SC-API-2025"
        }
        
        response = requests.post(f"{BASE_URL}/capteurs/", json=capteur_data)
        success = response.status_code == 201
        print_test("POST /capteurs/", success, response.text if not success else None)
        
        if success:
            data = response.json()
            capteur_id = data['capteur_id']
            print(f"  ✓ Capteur créé avec ID: {capteur_id}")
            tests_passed += 1
        else:
            tests_failed += 1
            capteur_id = None
    except Exception as e:
        print_test("POST /capteurs/", False, str(e))
        tests_failed += 1
        capteur_id = None
    
    # ========================================================================
    # TEST 4: Récupérer les détails d'un capteur
    # ========================================================================
    if capteur_id:
        print(f"\n{Colors.YELLOW}📋 TEST 4: Récupérer les détails d'un capteur{Colors.END}")
        try:
            response = requests.get(f"{BASE_URL}/capteurs/{capteur_id}/")
            success = response.status_code == 200
            print_test(f"GET /capteurs/{capteur_id}/", success)
            
            if success:
                data = response.json()
                print(f"  ✓ Capteur: {data['capteur']['nom']}")
                tests_passed += 1
            else:
                tests_failed += 1
        except Exception as e:
            print_test(f"GET /capteurs/{capteur_id}/", False, str(e))
            tests_failed += 1
    
    # ========================================================================
    # TEST 5: Modifier un capteur
    # ========================================================================
    if capteur_id:
        print(f"\n{Colors.YELLOW}📋 TEST 5: Modifier un capteur{Colors.END}")
        try:
            update_data = {
                "statut": "maintenance",
                "precision_detection": 92.5
            }
            
            response = requests.put(f"{BASE_URL}/capteurs/{capteur_id}/", json=update_data)
            success = response.status_code == 200
            print_test(f"PUT /capteurs/{capteur_id}/", success)
            
            if success:
                tests_passed += 1
            else:
                tests_failed += 1
        except Exception as e:
            print_test(f"PUT /capteurs/{capteur_id}/", False, str(e))
            tests_failed += 1
    
    # ========================================================================
    # TEST 6: Récupérer les données de trafic
    # ========================================================================
    print(f"\n{Colors.YELLOW}📋 TEST 6: Récupérer les données de trafic{Colors.END}")
    try:
        response = requests.get(f"{BASE_URL}/donnees/?heures=24")
        success = response.status_code == 200
        print_test("GET /donnees/?heures=24", success)
        
        if success:
            data = response.json()
            print(f"  ✓ Nombre de mesures: {data['count']}")
            tests_passed += 1
        else:
            tests_failed += 1
    except Exception as e:
        print_test("GET /donnees/?heures=24", False, str(e))
        tests_failed += 1
    
    # ========================================================================
    # TEST 7: Enregistrer de nouvelles données
    # ========================================================================
    print(f"\n{Colors.YELLOW}📋 TEST 7: Enregistrer de nouvelles données{Colors.END}")
    try:
        # Récupérer le premier capteur disponible
        response_capteurs = requests.get(f"{BASE_URL}/capteurs/")
        if response_capteurs.status_code == 200:
            capteurs = response_capteurs.json()['capteurs']
            if capteurs:
                capteur_id_for_data = capteurs[0]['id']

                donnee_data = {
                    "capteur_id": capteur_id_for_data,
                    "timestamp": datetime.now().isoformat() + "Z",
                    "nombre_vehicules": 52,
                    "vitesse_moyenne": 38.5,
                    "vitesse_mediane": 40.0,
                    "debit_vehicules": 3120,
                    "vehicules_legers": 45,
                    "vehicules_lourds": 4,
                    "deux_roues": 3,
                    "transports_publics": 0,
                    "niveau_congestion": "dense",
                    "taux_occupation": 82.0,
                    "conditions_meteo": "Ensoleillé",
                    "temperature": 23.0,
                    "incident_detecte": False
                }

                response = requests.post(f"{BASE_URL}/donnees/", json=donnee_data)
                success = response.status_code == 201
                print_test("POST /donnees/", success, response.text if not success else None)

                if success:
                    tests_passed += 1
                else:
                    tests_failed += 1
            else:
                print_test("POST /donnees/", False, "Aucun capteur disponible")
                tests_failed += 1
        else:
            print_test("POST /donnees/", False, "Impossible de récupérer les capteurs")
            tests_failed += 1
    except Exception as e:
        print_test("POST /donnees/", False, str(e))
        tests_failed += 1
    
    # ========================================================================
    # TEST 8: Récupérer les zones
    # ========================================================================
    print(f"\n{Colors.YELLOW}📋 TEST 8: Récupérer les zones{Colors.END}")
    try:
        response = requests.get(f"{BASE_URL}/zones/")
        success = response.status_code == 200
        print_test("GET /zones/", success)
        
        if success:
            data = response.json()
            print(f"  ✓ Nombre de zones: {data['count']}")
            tests_passed += 1
        else:
            tests_failed += 1
    except Exception as e:
        print_test("GET /zones/", False, str(e))
        tests_failed += 1
    
    # ========================================================================
    # TEST 9: Récupérer les feux
    # ========================================================================
    print(f"\n{Colors.YELLOW}📋 TEST 9: Récupérer les feux{Colors.END}")
    try:
        response = requests.get(f"{BASE_URL}/feux/")
        success = response.status_code == 200
        print_test("GET /feux/", success)
        
        if success:
            data = response.json()
            print(f"  ✓ Nombre de feux: {data['count']}")
            tests_passed += 1
        else:
            tests_failed += 1
    except Exception as e:
        print_test("GET /feux/", False, str(e))
        tests_failed += 1
    
    # ========================================================================
    # TEST 10: Récupérer les événements
    # ========================================================================
    print(f"\n{Colors.YELLOW}📋 TEST 10: Récupérer les événements{Colors.END}")
    try:
        response = requests.get(f"{BASE_URL}/evenements/?statut=en_cours")
        success = response.status_code == 200
        print_test("GET /evenements/?statut=en_cours", success)
        
        if success:
            data = response.json()
            print(f"  ✓ Nombre d'événements: {data['count']}")
            tests_passed += 1
        else:
            tests_failed += 1
    except Exception as e:
        print_test("GET /evenements/?statut=en_cours", False, str(e))
        tests_failed += 1
    
    # ========================================================================
    # TEST 11: Récupérer les statistiques
    # ========================================================================
    print(f"\n{Colors.YELLOW}📋 TEST 11: Récupérer les statistiques{Colors.END}")
    try:
        response = requests.get(f"{BASE_URL}/statistiques/?heures=24")
        success = response.status_code == 200
        print_test("GET /statistiques/?heures=24", success)
        
        if success:
            data = response.json()
            stats = data['statistiques']
            print(f"  ✓ Vitesse moyenne: {stats['vitesse_moyenne_globale']:.1f} km/h")
            print(f"  ✓ Taux occupation: {stats['taux_occupation_moyen']:.1f}%")
            print(f"  ✓ Incidents: {stats['incidents_detectes']}")
            tests_passed += 1
        else:
            tests_failed += 1
    except Exception as e:
        print_test("GET /statistiques/?heures=24", False, str(e))
        tests_failed += 1
    
    # ========================================================================
    # TEST 12: Supprimer un capteur
    # ========================================================================
    if capteur_id:
        print(f"\n{Colors.YELLOW}📋 TEST 12: Supprimer un capteur{Colors.END}")
        try:
            response = requests.delete(f"{BASE_URL}/capteurs/{capteur_id}/")
            success = response.status_code == 204
            print_test(f"DELETE /capteurs/{capteur_id}/", success)
            
            if success:
                tests_passed += 1
            else:
                tests_failed += 1
        except Exception as e:
            print_test(f"DELETE /capteurs/{capteur_id}/", False, str(e))
            tests_failed += 1
    
    # ========================================================================
    # RÉSUMÉ
    # ========================================================================
    print(f"\n{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BLUE}📊 RÉSUMÉ DES TESTS{Colors.END}")
    print(f"{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.GREEN}✅ Tests réussis: {tests_passed}{Colors.END}")
    print(f"{Colors.RED}❌ Tests échoués: {tests_failed}{Colors.END}")
    print(f"Total: {tests_passed + tests_failed} tests\n")
    
    return tests_failed == 0

if __name__ == '__main__':
    import sys
    success = test_api()
    sys.exit(0 if success else 1)

