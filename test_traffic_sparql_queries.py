#!/usr/bin/env python
"""
Script de test pour les requêtes SPARQL de gestion du trafic
Teste toutes les requêtes prédéfinies liées au trafic
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartcity_core.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from smartcity_app.ia_manager.ai_api import AIQueryProcessor, SampleQueries
from smartcity_app.ontology_manager.rdf_utils import RDFManager
import time

def test_traffic_sparql_queries():
    """Teste toutes les requêtes SPARQL de gestion du trafic"""
    
    print("\n" + "="*80)
    print("🚗 TEST DES REQUÊTES SPARQL - GESTION DU TRAFIC")
    print("="*80 + "\n")
    
    # Initialiser les gestionnaires
    ai_processor = AIQueryProcessor()
    rdf_manager = RDFManager()

    # Récupérer les requêtes prédéfinies
    predefined_queries = SampleQueries.get_predefined_queries()
    
    # Filtrer les requêtes de gestion du trafic
    traffic_queries = {
        k: v for k, v in predefined_queries.items() 
        if v.get('category') == 'Gestion Trafic'
    }
    
    print(f"📊 Nombre de requêtes de gestion du trafic trouvées: {len(traffic_queries)}\n")
    
    if not traffic_queries:
        print("❌ Aucune requête de gestion du trafic trouvée!")
        return False
    
    # Tester chaque requête
    results_summary = []
    total_time = 0
    
    for query_id, query_info in traffic_queries.items():
        print(f"\n{'─'*80}")
        print(f"🔍 Requête: {query_info['name']}")
        print(f"   ID: {query_id}")
        print(f"   Description: {query_info['description']}")
        print(f"{'─'*80}")
        
        try:
            # Exécuter la requête
            start_time = time.time()
            results = rdf_manager.execute_sparql_query(query_info['query'])
            execution_time = time.time() - start_time
            total_time += execution_time
            
            # Afficher les résultats
            print(f"✅ Succès!")
            print(f"   Résultats: {len(results)} ligne(s)")
            print(f"   Temps d'exécution: {execution_time:.3f}s")
            
            # Afficher les premiers résultats
            if results:
                print(f"\n   Premiers résultats:")
                for i, result in enumerate(results[:3]):
                    print(f"   [{i+1}] {result}")
                if len(results) > 3:
                    print(f"   ... et {len(results) - 3} autres résultats")
            else:
                print(f"   ⚠️  Aucun résultat trouvé")
            
            results_summary.append({
                'name': query_info['name'],
                'status': '✅ OK',
                'results': len(results),
                'time': execution_time
            })
            
        except Exception as e:
            print(f"❌ Erreur lors de l'exécution:")
            print(f"   {str(e)}")
            results_summary.append({
                'name': query_info['name'],
                'status': '❌ ERREUR',
                'results': 0,
                'time': 0
            })
    
    # Résumé final
    print(f"\n\n{'='*80}")
    print("📋 RÉSUMÉ DES TESTS")
    print(f"{'='*80}\n")
    
    print(f"{'Requête':<40} {'Statut':<15} {'Résultats':<12} {'Temps':<10}")
    print(f"{'-'*80}")
    
    successful = 0
    for summary in results_summary:
        status_icon = summary['status']
        print(f"{summary['name']:<40} {status_icon:<15} {summary['results']:<12} {summary['time']:.3f}s")
        if '✅' in status_icon:
            successful += 1
    
    print(f"{'-'*80}")
    print(f"Total: {successful}/{len(results_summary)} requêtes réussies")
    print(f"Temps total d'exécution: {total_time:.3f}s\n")
    
    # Test des requêtes en langage naturel
    print(f"\n{'='*80}")
    print("🤖 TEST DES REQUÊTES EN LANGAGE NATUREL")
    print(f"{'='*80}\n")
    
    natural_language_tests = [
        "Affiche tous les capteurs de trafic",
        "Combien de capteurs par zone?",
        "Quels sont les capteurs actifs?",
        "Liste les capteurs haute précision",
        "Capteurs par fournisseur",
        "Détails des capteurs de trafic"
    ]
    
    for question in natural_language_tests:
        print(f"\n❓ Question: {question}")
        try:
            result = ai_processor.process_natural_language_query(question)
            if result['success']:
                print(f"✅ Entité détectée: {result['detected_entity']}")
                print(f"   Action: {result['detected_action']}")
                print(f"   Propriétés: {result['detected_properties']}")
                print(f"   SPARQL généré: {result['sparql_query'][:100]}...")
            else:
                print(f"⚠️  Erreur: {result.get('error', 'Erreur inconnue')}")
        except Exception as e:
            print(f"❌ Erreur: {str(e)}")
    
    print(f"\n\n{'='*80}")
    print("✅ TESTS TERMINÉS")
    print(f"{'='*80}\n")
    
    return successful == len(results_summary)

if __name__ == '__main__':
    success = test_traffic_sparql_queries()
    sys.exit(0 if success else 1)

