#!/usr/bin/env python3
"""
Script de démonstration de l'intégration automatique RDF
Montre comment créer un capteur via l'interface et vérifier l'intégration RDF
"""

import os
import django
from datetime import date

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartcity_core.settings')
django.setup()

from smartcity_app.gestion_trafic.models import CapteurTrafic, ZoneTrafic

def demo_rdf_integration():
    """Démonstration de l'intégration automatique RDF"""
    print("🚀 === DÉMONSTRATION INTÉGRATION AUTOMATIQUE RDF ===")
    print()
    print("📋 Ce script simule la création d'un capteur via l'interface web")
    print("   et montre l'intégration automatique dans le fichier RDF")
    print()
    
    try:
        # Récupérer une zone existante
        zone = ZoneTrafic.objects.first()
        if not zone:
            print("❌ Aucune zone de trafic trouvée.")
            return False
        
        print(f"📍 Zone sélectionnée : {zone.nom}")
        print()
        
        # Simuler la création d'un capteur comme dans l'interface
        import time
        timestamp = int(time.time())
        
        print("🔄 Création du capteur...")
        capteur = CapteurTrafic.objects.create(
            nom=f"Capteur Demo {timestamp}",
            code_capteur=f"DEMO-{timestamp}",
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
            fournisseur="SmartCity Demo",
            modele="DEMO-CAM-2025"
        )
        
        print(f"✅ Capteur créé avec succès : {capteur.nom}")
        print(f"   ID : {capteur.id}")
        print(f"   Code : {capteur.code_capteur}")
        print(f"   Type : {capteur.type_capteur}")
        print(f"   Zone : {capteur.zone_trafic.nom}")
        print(f"   Coordonnées : {capteur.latitude}, {capteur.longitude}")
        print()
        
        # Vérifier l'intégration RDF
        print("🔍 Vérification de l'intégration RDF...")
        rdf_file_path = os.path.join(os.getcwd(), 'ontology', 'mobility_ontology_clean.rdf')
        
        with open(rdf_file_path, 'r', encoding='utf-8') as f:
            rdf_content = f.read()
        
        capteur_id = f"CapteurTrafic_{capteur.id}_DEMO_{timestamp}"
        rdf_uri = f"http://example.org/mobility-ontology/2025/09#{capteur_id}"
        
        if rdf_uri in rdf_content:
            print("✅ Le capteur a été automatiquement ajouté au fichier RDF !")
            print(f"   URI RDF : {rdf_uri}")
            print()
            
            # Afficher un extrait du RDF généré
            print("📄 Extrait du fichier RDF généré :")
            print("   " + "="*60)
            
            # Trouver le début de l'élément RDF pour ce capteur
            start_marker = f'<rdf:Description rdf:about="{rdf_uri}">'
            start_pos = rdf_content.find(start_marker)
            
            if start_pos != -1:
                # Trouver la fin de l'élément
                end_pos = rdf_content.find('</rdf:Description>', start_pos) + len('</rdf:Description>')
                rdf_extract = rdf_content[start_pos:end_pos]
                
                # Afficher l'extrait avec indentation
                lines = rdf_extract.split('\n')
                for line in lines:
                    if line.strip():
                        print(f"   {line}")
            
            print("   " + "="*60)
            print()
            
            return True
        else:
            print("❌ Le capteur n'a pas été trouvé dans le fichier RDF")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de la démonstration : {str(e)}")
        return False

def main():
    print("🎯 === SYSTÈME D'INTÉGRATION AUTOMATIQUE RDF ===")
    print()
    print("Ce système permet d'intégrer automatiquement chaque nouveau")
    print("capteur créé dans le fichier mobility_ontology_clean.rdf")
    print()
    print("✨ Fonctionnalités :")
    print("   • Création automatique d'entrées RDF pour les capteurs")
    print("   • Propriétés complètes (nom, type, coordonnées, etc.)")
    print("   • Intégration en temps réel via les signaux Django")
    print("   • Compatible avec les outils d'ontologie")
    print()
    
    success = demo_rdf_integration()
    
    print()
    if success:
        print("🎉 === DÉMONSTRATION RÉUSSIE ===")
        print("✅ L'intégration automatique RDF fonctionne parfaitement")
        print()
        print("🔄 Pour tester via l'interface web :")
        print("   1. Allez sur http://127.0.0.1:8000/trafic/capteurs/creer/")
        print("   2. Créez un nouveau capteur")
        print("   3. Le capteur sera automatiquement ajouté au fichier RDF")
        print()
        print("📁 Fichier RDF mis à jour : ontology/mobility_ontology_clean.rdf")
    else:
        print("❌ === DÉMONSTRATION ÉCHOUÉE ===")
        print("❌ L'intégration automatique RDF ne fonctionne pas")

if __name__ == '__main__':
    main()

