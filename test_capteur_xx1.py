"""
Script de test pour diagnostiquer l'échec du capteur xx1
"""
import os
import django
from datetime import date

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartcity_core.settings')
django.setup()

from smartcity_app.gestion_trafic.models import CapteurTrafic, ZoneTrafic
from smartcity_app.gestion_trafic.rdf_integration import add_capteur_to_rdf

def test_capteur_xx1():
    """Test avec un capteur similaire à xx1"""
    print("=" * 70)
    print("🔍 DIAGNOSTIC DU PROBLÈME CAPTEUR xx1")
    print("=" * 70)
    print()
    
    try:
        # Récupérer une zone existante
        zone = ZoneTrafic.objects.first()
        if not zone:
            print("❌ Aucune zone de trafic trouvée.")
            return False
        
        print(f"📍 Zone sélectionnée : {zone.nom}")
        print()
        
        # Créer un capteur avec un nom simple comme "xx1"
        print("🔄 Création du capteur 'xx1'...")
        capteur = CapteurTrafic.objects.create(
            nom="xx1",
            code_capteur="XX1-TEST",
            type_capteur="camera_ia",
            zone_trafic=zone,
            latitude=36.8065,
            longitude=10.1815,
            direction_mesure="Nord-Sud",
            statut="actif",
            frequence_mesure=60,
            precision_detection=95.0,
            vitesse_min_detection=5,
            vitesse_max_detection=200,
            date_installation=date.today(),
            fournisseur="Test",
            modele="XX1"
        )
        
        print(f"✅ Capteur créé : {capteur.nom} (ID: {capteur.id})")
        print()
        
        # Vérifier dans le fichier RDF
        print("🔍 Vérification dans le fichier RDF...")
        from django.conf import settings
        rdf_file = os.path.join(settings.BASE_DIR, 'ontology', 'mobility_ontology_clean.rdf')
        
        with open(rdf_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        capteur_id = f"CapteurTrafic_{capteur.id}_{capteur.code_capteur.replace('-', '_')}"
        
        if capteur_id in content:
            print(f"✅ Capteur trouvé dans le RDF !")
            print(f"   URI: http://example.org/mobility-ontology/2025/09#{capteur_id}")
            print()
            print("=" * 70)
            print("🎉 SUCCÈS - Le capteur a été ajouté correctement")
            print("=" * 70)
            return True
        else:
            print(f"❌ Capteur NON trouvé dans le RDF")
            print(f"   Recherché : {capteur_id}")
            print()
            
            # Afficher les dernières lignes du fichier RDF
            print("📄 Dernières lignes du fichier RDF :")
            print("-" * 70)
            lines = content.split('\n')
            for line in lines[-10:]:
                print(line)
            print("-" * 70)
            print()
            
            # Vérifier les logs
            log_file = os.path.join(settings.BASE_DIR, 'smartcity.log')
            if os.path.exists(log_file):
                print("📋 Dernières lignes du fichier de log :")
                print("-" * 70)
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    log_lines = f.readlines()
                    for line in log_lines[-20:]:
                        if 'xx1' in line.lower() or 'capteur' in line.lower():
                            print(line.strip())
                print("-" * 70)
            
            print()
            print("=" * 70)
            print("❌ ÉCHEC - Vérifiez les logs ci-dessus")
            print("=" * 70)
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test : {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_capteur_xx1()

