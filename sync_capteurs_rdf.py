#!/usr/bin/env python3
"""
Script de synchronisation des capteurs existants avec le fichier RDF
"""

import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartcity_core.settings')
django.setup()

from smartcity_app.gestion_trafic.rdf_integration import sync_existing_capteurs_to_rdf

def main():
    print("🚀 === SYNCHRONISATION DES CAPTEURS AVEC LE FICHIER RDF ===")
    print()
    
    try:
        added_count = sync_existing_capteurs_to_rdf()
        print()
        print("✅ === SYNCHRONISATION TERMINÉE ===")
        print(f"📊 {added_count} capteurs synchronisés avec le fichier RDF")
        print()
        print("🔄 Désormais, chaque nouveau capteur créé sera automatiquement")
        print("   ajouté au fichier mobility_ontology_clean.rdf")
        
    except Exception as e:
        print(f"❌ Erreur lors de la synchronisation : {str(e)}")

if __name__ == '__main__':
    main()

