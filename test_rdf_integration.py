#!/usr/bin/env python3
"""
Script de test pour créer un nouveau capteur et vérifier l'intégration RDF automatique
"""

import os
import django
from datetime import date

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartcity_core.settings')
django.setup()

from smartcity_app.gestion_trafic.models import CapteurTrafic, ZoneTrafic

def test_capteur_creation():
    """Test de création d'un nouveau capteur pour vérifier l'intégration RDF"""
    print("🧪 === TEST DE CRÉATION DE CAPTEUR AVEC INTÉGRATION RDF ===")
    print()
    
    try:
        # Récupérer une zone existante
        zone = ZoneTrafic.objects.first()
        if not zone:
            print("❌ Aucune zone de trafic trouvée. Créez d'abord des zones.")
            return False
        
        # Créer un nouveau capteur de test
        import time
        timestamp = int(time.time())
        capteur_test = CapteurTrafic.objects.create(
            nom=f"Capteur Test RDF {timestamp}",
            code_capteur=f"TEST-RDF-{timestamp}",
            type_capteur="radar",
            zone_trafic=zone,
            latitude=36.8000,
            longitude=10.1800,
            direction_mesure="Nord-Sud",
            statut="actif",
            frequence_mesure=30,
            precision_detection=98.5,
            vitesse_min_detection=5,
            vitesse_max_detection=80,
            date_installation=date.today(),
            fournisseur="Test RDF Integration",
            modele="RDF-TEST-2025"
        )
        
        print(f"✅ Capteur de test créé : {capteur_test.nom}")
        print(f"   ID : {capteur_test.id}")
        print(f"   Code : {capteur_test.code_capteur}")
        print()
        
        # Vérifier que le capteur a été ajouté au fichier RDF
        rdf_file_path = os.path.join(os.getcwd(), 'ontology', 'mobility_ontology_clean.rdf')
        
        with open(rdf_file_path, 'r', encoding='utf-8') as f:
            rdf_content = f.read()
        
        capteur_id = f"CapteurTrafic_{capteur_test.id}_TEST_RDF_{timestamp}"
        rdf_uri = f"http://example.org/mobility-ontology/2025/09#{capteur_id}"
        
        if rdf_uri in rdf_content:
            print("✅ Le capteur a été automatiquement ajouté au fichier RDF !")
            print(f"   URI RDF : {rdf_uri}")
            return True
        else:
            print("❌ Le capteur n'a pas été trouvé dans le fichier RDF")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test : {str(e)}")
        return False

def main():
    success = test_capteur_creation()
    
    print()
    if success:
        print("🎉 === TEST RÉUSSI ===")
        print("✅ L'intégration automatique RDF fonctionne correctement")
        print("🔄 Chaque nouveau capteur créé sera automatiquement ajouté au fichier RDF")
    else:
        print("❌ === TEST ÉCHOUÉ ===")
        print("❌ L'intégration automatique RDF ne fonctionne pas")

if __name__ == '__main__':
    main()
