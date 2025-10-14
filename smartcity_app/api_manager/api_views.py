"""
Vues API REST pour le projet SmartCity
Fournit des endpoints pour interagir avec l'ontologie RDF et l'IA
"""

import logging
from typing import Dict, Any
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json

from ..ontology_manager.rdf_utils import rdf_manager
from ..ia_manager.ai_api import ai_processor, SampleQueries

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([AllowAny])
def ask_ai_question(request):
    """
    API endpoint pour traiter une question en langage naturel
    POST /api/ask/
    """
    try:
        data = request.data
        question = data.get('question', '').strip()
        
        if not question:
            return Response({
                'success': False,
                'error': 'Question vide. Veuillez poser une question.',
                'examples': ai_processor._get_example_questions()
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Traitement IA de la question
        ai_result = ai_processor.process_natural_language_query(question)
        
        if ai_result['success']:
            # Exécution de la requête SPARQL générée
            try:
                query_results = rdf_manager.execute_sparql_query(ai_result['sparql_query'])
                
                return Response({
                    'success': True,
                    'question': question,
                    'explanation': ai_result['explanation'],
                    'sparql_query': ai_result['sparql_query'],
                    'results': query_results,
                    'results_count': len(query_results),
                    'detected_info': {
                        'entity': ai_result['detected_entity'],
                        'action': ai_result['detected_action'],
                        'properties': ai_result['detected_properties'],
                        'filters': ai_result['detected_filters']
                    }
                }, status=status.HTTP_200_OK)
                
            except Exception as e:
                logger.error(f"Erreur lors de l'exécution SPARQL: {e}")
                return Response({
                    'success': False,
                    'error': f'Erreur lors de l\'exécution de la requête: {str(e)}',
                    'sparql_query': ai_result['sparql_query'],
                    'suggestion': 'Vérifiez la syntaxe de votre question.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({
                'success': False,
                'error': ai_result['error'],
                'suggestions': ai_result.get('suggestion', [])
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Erreur dans ask_ai_question: {e}")
        return Response({
            'success': False,
            'error': 'Erreur interne du serveur'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def execute_sparql_query(request):
    """
    API endpoint pour exécuter directement une requête SPARQL
    POST /api/sparql/
    """
    try:
        data = request.data
        sparql_query = data.get('query', '').strip()
        
        if not sparql_query:
            return Response({
                'success': False,
                'error': 'Requête SPARQL vide'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Exécution de la requête
        results = rdf_manager.execute_sparql_query(sparql_query)
        
        return Response({
            'success': True,
            'query': sparql_query,
            'results': results,
            'results_count': len(results)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution SPARQL: {e}")
        return Response({
            'success': False,
            'error': f'Erreur lors de l\'exécution: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_ontology_info(request):
    """
    API endpoint pour récupérer les informations générales de l'ontologie
    GET /api/ontology/info/
    """
    try:
        info = {
            'classes': rdf_manager.get_classes(),
            'properties': rdf_manager.get_properties(),
            'individuals': rdf_manager.get_individuals(),
            'statistics': rdf_manager.get_statistics()
        }
        
        return Response({
            'success': True,
            'data': info
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des infos ontologie: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_entities_by_type(request, entity_type):
    """
    API endpoint pour récupérer les entités par type
    GET /api/entities/<entity_type>/
    """
    try:
        entity_methods = {
            'users': rdf_manager.get_user_data,
            'vehicles': rdf_manager.get_vehicles_data,
            'stations': rdf_manager.get_stations_data,
            'trips': rdf_manager.get_trips_data,
            'traffic': rdf_manager.get_traffic_data
        }
        
        if entity_type not in entity_methods:
            return Response({
                'success': False,
                'error': f'Type d\'entité non supporté: {entity_type}',
                'supported_types': list(entity_methods.keys())
            }, status=status.HTTP_400_BAD_REQUEST)
        
        data = entity_methods[entity_type]()
        
        return Response({
            'success': True,
            'entity_type': entity_type,
            'data': data,
            'count': len(data)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des entités {entity_type}: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def search_entities(request):
    """
    API endpoint pour rechercher des entités par mot-clé
    GET /api/search/?q=keyword
    """
    try:
        keyword = request.GET.get('q', '').strip()
        
        if not keyword:
            return Response({
                'success': False,
                'error': 'Paramètre de recherche \'q\' manquant'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if len(keyword) < 2:
            return Response({
                'success': False,
                'error': 'Le mot-clé doit contenir au moins 2 caractères'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        results = rdf_manager.search_by_keyword(keyword)
        
        return Response({
            'success': True,
            'keyword': keyword,
            'results': results,
            'count': len(results)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur lors de la recherche: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_predefined_queries(request):
    """
    API endpoint pour récupérer les requêtes SPARQL prédéfinies
    GET /api/queries/predefined/
    """
    try:
        queries = SampleQueries.get_predefined_queries()
        
        # Organiser par catégorie
        categories = {}
        for query_id, query_info in queries.items():
            category = query_info.get('category', 'Général')
            if category not in categories:
                categories[category] = []
            categories[category].append({
                'id': query_id,
                'name': query_info['name'],
                'description': query_info['description'],
                'query': query_info['query']
            })
        
        return Response({
            'success': True,
            'categories': categories,
            'total_queries': len(queries)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des requêtes prédéfinies: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def execute_predefined_query(request, query_id):
    """
    API endpoint pour exécuter une requête prédéfinie
    POST /api/queries/predefined/<query_id>/execute/
    """
    try:
        predefined_queries = SampleQueries.get_predefined_queries()
        
        if query_id not in predefined_queries:
            return Response({
                'success': False,
                'error': f'Requête prédéfinie non trouvée: {query_id}',
                'available_queries': list(predefined_queries.keys())
            }, status=status.HTTP_404_NOT_FOUND)
        
        query_info = predefined_queries[query_id]
        results = rdf_manager.execute_sparql_query(query_info['query'])
        
        return Response({
            'success': True,
            'query_info': {
                'id': query_id,
                'name': query_info['name'],
                'description': query_info['description']
            },
            'sparql_query': query_info['query'],
            'results': results,
            'results_count': len(results)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution de la requête prédéfinie {query_id}: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_api_status(request):
    """
    API endpoint pour vérifier le statut de l'API
    GET /api/status/
    """
    try:
        # Vérifier le chargement de l'ontologie
        stats = rdf_manager.get_statistics()
        
        return Response({
            'success': True,
            'status': 'API opérationnelle',
            'ontology_loaded': stats['total_triples'] > 0,
            'statistics': stats,
            'endpoints': {
                'ask_ai': '/api/ask/',
                'sparql': '/api/sparql/',
                'ontology_info': '/api/ontology/info/',
                'entities': '/api/entities/<type>/',
                'search': '/api/search/?q=<keyword>',
                'predefined_queries': '/api/queries/predefined/',
                'execute_predefined': '/api/queries/predefined/<id>/execute/'
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur lors de la vérification du statut: {e}")
        return Response({
            'success': False,
            'status': 'Erreur API',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)