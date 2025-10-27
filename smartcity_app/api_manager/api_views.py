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
                'execute_predefined': '/api/queries/predefined/<id>/execute/',
                'add_trip': '/api/trips/add/'
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur lors de la vérification du statut: {e}")
        return Response({
            'success': False,
            'status': 'Erreur API',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def add_trip_to_ontology(request):
    """
    API endpoint pour ajouter un nouveau trajet dans l'ontologie RDF
    POST /api/trips/add/
    """
    try:
        data = request.data
        
        # Validation des champs obligatoires
        required_fields = ['pointDepart', 'pointArrivee', 'duree', 'distance', 'cout', 'mode', 'vehiculeType']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return Response({
                'success': False,
                'error': f'Champs obligatoires manquants: {", ".join(missing_fields)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Préparer les données du trajet avec validation
        trajet_data = {}
        
        # Champs textuels
        text_fields = ['nom', 'utilisateurUsername', 'pointDepart', 'pointArrivee', 'mode', 'vehiculeType', 'niveauCirculation', 'zoneGeographique', 'etapesJson']
        for field in text_fields:
            if field in data and data[field]:
                trajet_data[field] = str(data[field]).strip()
        
        # Champs numériques avec validation
        try:
            # Champs flottants
            float_fields = ['duree', 'distance', 'cout', 'empreinteCarbone', 'scoreIA', 'fiabiliteScore']
            for field in float_fields:
                if field in data and data[field] is not None:
                    value = float(data[field])
                    if value < 0:
                        return Response({
                            'success': False,
                            'error': f'Le champ {field} ne peut pas être négatif'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    trajet_data[field] = value
            
            # Champs entiers
            int_fields = ['scoreConfort']
            for field in int_fields:
                if field in data and data[field] is not None:
                    value = int(data[field])
                    if field == 'scoreConfort' and (value < 1 or value > 10):
                        return Response({
                            'success': False,
                            'error': 'Le score de confort doit être entre 1 et 10'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    trajet_data[field] = value
                    
        except (ValueError, TypeError) as e:
            return Response({
                'success': False,
                'error': f'Erreur de format numérique: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validation du JSON des étapes
        if 'etapesJson' in trajet_data:
            try:
                import json
                json.loads(trajet_data['etapesJson'])
            except json.JSONDecodeError:
                return Response({
                    'success': False,
                    'error': 'Le format JSON des étapes est invalide'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Ajouter le trajet dans l'ontologie RDF
        success, result = rdf_manager.add_trajet_to_rdf(trajet_data)
        
        if success:
            return Response({
                'success': True,
                'message': 'Trajet ajouté avec succès dans l\'ontologie',
                'trajet_uri': result,
                'data': trajet_data
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'success': False,
                'error': f'Erreur lors de l\'ajout dans l\'ontologie: {result}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"Erreur dans add_trip_to_ontology: {e}")
        return Response({
            'success': False,
            'error': 'Erreur interne du serveur'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST', 'DELETE'])
@permission_classes([AllowAny])
def delete_trip_from_ontology(request):
    """
    API endpoint pour supprimer un trajet de l'ontologie RDF
    POST /api/trips/delete/  (body JSON {"trajet_uri": "..."} )
    or
    DELETE /api/trips/delete/?trajet_uri=...
    """
    try:
        # Accept both JSON body (POST) or query param (DELETE)
        if request.method == 'POST':
            data = request.data
            trajet_uri = data.get('trajet_uri') or data.get('trajet_id')
        else:
            trajet_uri = request.GET.get('trajet_uri') or request.GET.get('trajet_id')

        if not trajet_uri:
            return Response({'success': False, 'error': 'Identifiant du trajet manquant'}, status=status.HTTP_400_BAD_REQUEST)

        # Supporter le passage d'une URI complète ou d'un identifiant local (fragment après '#')
        trajet_id = None
        if '#' in trajet_uri:
            trajet_id = trajet_uri.split('#')[-1]
        else:
            # Si l'URI contient des /, prendre la dernière partie
            if '/' in trajet_uri:
                trajet_id = trajet_uri.rstrip('/').split('/')[-1]
            else:
                trajet_id = trajet_uri

        # Appeler le manager RDF pour supprimer
        success, message = rdf_manager.delete_trajet(trajet_id)

        if success:
            return Response({'success': True, 'message': message}, status=status.HTTP_200_OK)
        else:
            return Response({'success': False, 'error': message}, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"Erreur dans delete_trip_from_ontology: {e}")
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_transport_options(request):
    """
    API endpoint pour récupérer les options de transport depuis l'ontologie RDF
    GET /api/transport/options/
    """
    try:
        # Récupérer les modes de transport et types de véhicules depuis l'ontologie
        transport_modes = rdf_manager.get_transport_modes_from_rdf()
        vehicle_types = rdf_manager.get_vehicle_types_from_rdf()
        
        # Ajouter des valeurs par défaut si aucune donnée n'est trouvée dans l'ontologie
        default_modes = [
            "Voiture Personnelle", "Autolib (Voiture Partagée)", "Moto", 
            "Vélo", "Métro", "Bus", "Vélo + Métro", "Marche"
        ]
        default_types = ["prive", "public", "partage", "multimodal"]
        
        # Fusionner avec les valeurs par défaut (sans doublons)
        all_modes = sorted(list(set(transport_modes + default_modes)))
        all_types = sorted(list(set(vehicle_types + default_types)))
        
        return Response({
            'success': True,
            'data': {
                'transport_modes': all_modes,
                'vehicle_types': all_types,
                'sources': {
                    'modes_from_ontology': len(transport_modes),
                    'types_from_ontology': len(vehicle_types),
                    'total_modes': len(all_modes),
                    'total_types': len(all_types)
                }
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des options de transport: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)