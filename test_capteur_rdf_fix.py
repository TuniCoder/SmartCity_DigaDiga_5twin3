"""
Script de test pour vérifier la correction de l'intégration RDF des capteurs
"""
import os
import django
from datetime import date

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartcity_core.settings')
django.setup()

from smartcity_app.gestion_trafic.models import CapteurTrafic, ZoneTrafic
from smartcity_app.gestion_trafic.rdf_integration import add_capteur_to_rdf

def test_rdf_fix():
    """Test de l'intégration RDF après correction"""
    print("=" * 70)
    print("🧪 TEST DE L'INTÉGRATION RDF DES CAPTEURS")
    print("=" * 70)
    print()
    
    try:
        # Récupérer une zone existante
        zone = ZoneTrafic.objects.first()
        if not zone:
            print("❌ Aucune zone de trafic trouvée.")
            print("💡 Créez d'abord une zone de trafic via l'interface.")
            return False
        
        print(f"📍 Zone sélectionnée : {zone.nom}")
        print()
        
        # Créer un capteur de test
        import time
        timestamp = int(time.time())
        
        print("🔄 Création du capteur de test...")
        capteur = CapteurTrafic.objects.create(
            nom=f"Test RDF Fix {timestamp}",
            code_capteur=f"TEST-FIX-{timestamp}",
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
            fournisseur="Test RDF",
            modele="FIX-2025"
        )
        
        print(f"✅ Capteur créé : {capteur.nom} (ID: {capteur.id})")
        print()
        
        # Vérifier l'ajout au RDF
        print("🔍 Vérification de l'intégration RDF...")
        
        # Lire le fichier RDF
        from django.conf import settings
        rdf_file = os.path.join(settings.BASE_DIR, 'ontology', 'mobility_ontology_clean.rdf')
        
        with open(rdf_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Vérifier si le capteur est dans le RDF
        capteur_id = f"CapteurTrafic_{capteur.id}_{capteur.code_capteur.replace('-', '_')}"
        
        if capteur_id in content:
            print(f"✅ Capteur trouvé dans le fichier RDF !")
            print(f"   URI: http://example.org/mobility-ontology/2025/09#{capteur_id}")
            print()
            
            # Vérifier les propriétés
            if f"<mobility:nomCapteur" in content and capteur.nom in content:
                print(f"✅ Propriété 'nomCapteur' présente")
            if f"<mobility:codeCapteur" in content and capteur.code_capteur in content:
                print(f"✅ Propriété 'codeCapteur' présente")
            if f"<mobility:typeCapteur" in content:
                print(f"✅ Propriété 'typeCapteur' présente")
            
            print()
            print("=" * 70)
            print("🎉 TEST RÉUSSI !")
            print("=" * 70)
            print("✅ L'intégration RDF fonctionne correctement")
            print("✅ Les capteurs sont automatiquement ajoutés au fichier RDF")
            print()
            return True
        else:
            print(f"❌ Capteur NON trouvé dans le fichier RDF")
            print(f"   Recherché : {capteur_id}")
            print()
            print("=" * 70)
            print("❌ TEST ÉCHOUÉ")
            print("=" * 70)
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test : {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_rdf_fix()

