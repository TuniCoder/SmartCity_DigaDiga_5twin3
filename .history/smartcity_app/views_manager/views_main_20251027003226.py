"""
Vues principales pour l'interface web SmartCity
"""

import logging
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from django.db import transaction
import json
import re

from ..ontology_manager.rdf_utils import rdf_manager
from ..ia_manager.ai_api import ai_processor, SampleQueries
from ..gestion_utilisateurs.models import ProfilUtilisateur, RoleUtilisateur

logger = logging.getLogger(__name__)

# Fonction utilitaire pour vérifier les permissions
def est_administrateur(user):
    """Vérifie si l'utilisateur est administrateur"""
    if not user.is_authenticated:
        return False
    try:
        profil = ProfilUtilisateur.objects.get(user=user)
        return profil.est_administrateur
    except ProfilUtilisateur.DoesNotExist:
        return False

def peut_voir_ontologie(user):
    """Vérifie si l'utilisateur peut voir l'ontologie"""
    if not user.is_authenticated:
        return False
    try:
        profil = ProfilUtilisateur.objects.get(user=user)
        return profil.peut_acceder_ontologie
    except ProfilUtilisateur.DoesNotExist:
        return False

def index_view(request):
    """Vue principale d'accueil - Redirige vers connexion si non authentifié"""
    # Vérifier si l'utilisateur est connecté
    if not request.user.is_authenticated:
        return redirect('gestion_utilisateurs:connexion')
    
    try:
        # Redirection selon le rôle de l'utilisateur
        profil = ProfilUtilisateur.objects.get(user=request.user)
        
        if profil.est_administrateur:
            return redirect('gestion_utilisateurs:dashboard_admin')
        else:
            return redirect('gestion_utilisateurs:dashboard_user')
            
    except ProfilUtilisateur.DoesNotExist:
        # Si le profil n'existe pas, rediriger vers la connexion
        return redirect('gestion_utilisateurs:connexion')
    except Exception as e:
        logger.error(f"Erreur dans index_view: {e}")
        messages.error(request, "Erreur lors du chargement de la page d'accueil")
        return redirect('gestion_utilisateurs:connexion')


@login_required
def ontology_view(request):
    """Vue pour visualiser l'ontologie - Admin uniquement"""
    # Vérifier les permissions d'accès à l'ontologie
    if not peut_voir_ontologie(request.user):
        messages.error(request, "Accès refusé : Vous n'avez pas les permissions pour accéder à l'ontologie.")
        if est_administrateur(request.user):
            return redirect('gestion_utilisateurs:dashboard_admin')
        else:
            return redirect('gestion_utilisateurs:dashboard_user')
    
    try:
        # Récupération des informations de l'ontologie
        classes = rdf_manager.get_classes()
        properties = rdf_manager.get_properties()
        individuals = rdf_manager.get_individuals()
        stats = rdf_manager.get_statistics()
        
        # Pagination des individus
        paginator = Paginator(individuals, 20)  # 20 individus par page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'page_title': 'Ontologie de Mobilité',
            'classes': classes,
            'properties': properties,
            'individuals': page_obj,
            'statistics': stats,
            'total_classes': len(classes),
            'total_properties': len(properties),
            'total_individuals': len(individuals),
        }
        
        return render(request, 'ontology_view.html', context)
        
    except Exception as e:
        logger.error(f"Erreur dans ontology_view: {e}")
        messages.error(request, f"Erreur lors du chargement de l'ontologie: {str(e)}")
        context = {
            'page_title': 'Ontologie - Erreur',
            'error': str(e)
        }
        return render(request, 'ontology_view.html', context)


@login_required
def query_view(request):
    """Vue pour les requêtes SPARQL et IA - Admin uniquement"""
    # Vérifier les permissions d'accès aux requêtes SPARQL
    if not peut_voir_ontologie(request.user):
        messages.error(request, "Accès refusé : Vous n'avez pas les permissions pour exécuter des requêtes SPARQL.")
        if est_administrateur(request.user):
            return redirect('gestion_utilisateurs:dashboard_admin')
        else:
            return redirect('gestion_utilisateurs:dashboard_user')
    
    # Organiser les requêtes prédéfinies par catégorie
    all_queries = SampleQueries.get_predefined_queries()
    queries_by_category = {}
    for query_id, query_info in all_queries.items():
        category = query_info.get('category', 'Général')
        if category not in queries_by_category:
            queries_by_category[category] = {}
        queries_by_category[category][query_id] = query_info
    
    context = {
        'page_title': 'Interrogation Sémantique',
        'predefined_queries': queries_by_category,
        'all_predefined_queries': all_queries,  # Pour la logique de traitement
        'example_questions': ai_processor._get_example_questions(),
    }
    
    if request.method == 'POST':
        try:
            query_type = request.POST.get('query_type', 'natural')
            logger.info(f"Type de requête reçu: {query_type}")
            
            if query_type == 'natural':
                # Question en langage naturel
                question = request.POST.get('question', '').strip()
                logger.info(f"Question naturelle: {question}")
                
                if question:
                    ai_result = ai_processor.process_natural_language_query(question)
                    
                    if ai_result['success']:
                        # Exécuter la requête SPARQL générée
                        query_results = rdf_manager.execute_sparql_query(ai_result['sparql_query'])
                        
                        context.update({
                            'query_executed': True,
                            'query_type': 'natural',
                            'original_question': question,
                            'ai_explanation': ai_result['explanation'],
                            'generated_sparql': ai_result['sparql_query'],
                            'results': query_results,
                            'results_count': len(query_results),
                            'detected_info': {
                                'entity': ai_result['detected_entity'],
                                'action': ai_result['detected_action'],
                                'properties': ai_result['detected_properties'],
                                'filters': ai_result['detected_filters']
                            }
                        })
                        messages.success(request, f"Question traitée avec succès! {len(query_results)} résultat(s) trouvé(s).")
                    else:
                        context.update({
                            'query_error': True,
                            'error_message': ai_result['error'],
                            'suggestions': ai_result.get('suggestion', [])
                        })
                        messages.error(request, f"Erreur lors du traitement de la question: {ai_result['error']}")
                else:
                    messages.error(request, "Veuillez saisir une question.")
                    
            elif query_type == 'sparql':
                # Requête SPARQL directe
                sparql_query = request.POST.get('sparql_query', '').strip()
                logger.info(f"Requête SPARQL: {sparql_query[:100]}...")
                
                if sparql_query:
                    query_results = rdf_manager.execute_sparql_query(sparql_query)
                    
                    context.update({
                        'query_executed': True,
                        'query_type': 'sparql',
                        'sparql_query': sparql_query,
                        'results': query_results,
                        'results_count': len(query_results),
                    })
                    messages.success(request, f"Requête SPARQL exécutée avec succès! {len(query_results)} résultat(s) trouvé(s).")
                else:
                    messages.error(request, "Veuillez saisir une requête SPARQL.")
                    
            elif query_type == 'predefined':
                # Requête prédéfinie
                query_id = request.POST.get('predefined_query_id')
                logger.info(f"ID requête prédéfinie: {query_id}")
                predefined_queries = context['all_predefined_queries']
                
                if query_id and query_id in predefined_queries:
                    query_info = predefined_queries[query_id]
                    query_results = rdf_manager.execute_sparql_query(query_info['query'])
                    
                    context.update({
                        'query_executed': True,
                        'query_type': 'predefined',
                        'query_name': query_info['name'],
                        'query_description': query_info['description'],
                        'sparql_query': query_info['query'],
                        'results': query_results,
                        'results_count': len(query_results),
                    })
                    messages.success(request, f"Requête '{query_info['name']}' exécutée avec succès!")
                else:
                    messages.error(request, f"Requête prédéfinie non trouvée. ID reçu: '{query_id}'. IDs disponibles: {list(predefined_queries.keys())}")
            else:
                messages.error(request, f"Type de requête inconnu: {query_type}")
                    
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution de la requête: {e}")
            context.update({
                'query_error': True,
                'error_message': str(e)
            })
            messages.error(request, f"Erreur lors de l'exécution: {str(e)}")
    
    return render(request, 'query.html', context)


@login_required
def entities_view(request, entity_type):
    """Vue pour afficher les entités par type - Utilisateurs connectés"""
    try:
        # Mapping des types d'entités
        entity_methods = {
            'users': ('Utilisateurs', rdf_manager.get_user_data),
            'vehicles': ('Véhicules', rdf_manager.get_vehicles_data),
            'stations': ('Stations', rdf_manager.get_stations_data),
            'trips': ('Trajets', rdf_manager.get_trips_data),
            'traffic': ('Trafic', rdf_manager.get_traffic_data)
        }
        
        if entity_type not in entity_methods:
            messages.error(request, f"Type d'entité non supporté: {entity_type}")
            return redirect('smartcity_app:index')
        
        entity_name, method = entity_methods[entity_type]
        entities = method()
        
        # Pagination
        paginator = Paginator(entities, 25)  # 25 entités par page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'page_title': f'{entity_name} - SmartCity',
            'entity_type': entity_type,
            'entity_name': entity_name,
            'entities': page_obj,
            'total_count': len(entities),
            'is_admin': est_administrateur(request.user),
        }
        
        return render(request, 'entities_list.html', context)
        
    except Exception as e:
        logger.error(f"Erreur dans entities_view pour {entity_type}: {e}")
        messages.error(request, f"Erreur lors du chargement des {entity_type}: {str(e)}")
        return redirect('smartcity_app:index')


@login_required
def search_view(request):
    """Vue pour la recherche - Utilisateurs connectés"""
    context = {
        'page_title': 'Recherche - SmartCity',
    }
    
    if request.method == 'GET' and 'q' in request.GET:
        keyword = request.GET.get('q', '').strip()
        
        if keyword:
            if len(keyword) >= 2:
                try:
                    search_results = rdf_manager.search_by_keyword(keyword)
                    
                    # Pagination des résultats
                    paginator = Paginator(search_results, 20)
                    page_number = request.GET.get('page')
                    page_obj = paginator.get_page(page_number)
                    
                    context.update({
                        'search_performed': True,
                        'keyword': keyword,
                        'results': page_obj,
                        'total_results': len(search_results),
                    })
                    
                    messages.success(request, f"{len(search_results)} résultat(s) trouvé(s) pour '{keyword}'")
                    
                except Exception as e:
                    logger.error(f"Erreur lors de la recherche: {e}")
                    context.update({
                        'search_error': True,
                        'error_message': str(e)
                    })
                    messages.error(request, f"Erreur lors de la recherche: {str(e)}")
            else:
                messages.error(request, "Le mot-clé doit contenir au moins 2 caractères.")
        else:
            messages.error(request, "Veuillez saisir un mot-clé de recherche.")
    
    return render(request, 'search.html', context)


@csrf_exempt
@login_required
def ajax_entity_details(request, entity_uri):
    """Vue AJAX pour récupérer les détails d'une entité - Utilisateurs connectés"""
    try:
        # Construire une requête SPARQL pour récupérer toutes les propriétés de l'entité
        query = f"""
        SELECT ?property ?value
        WHERE {{
            <{entity_uri}> ?property ?value .
        }}
        ORDER BY ?property
        """
        
        results = rdf_manager.execute_sparql_query(query)
        
        # Organiser les résultats
        details = {}
        for result in results:
            prop = result.get('property', '')
            value = result.get('value', '')
            
            # Extraire le nom de la propriété (après le #)
            prop_name = prop.split('#')[-1] if '#' in prop else prop
            details[prop_name] = value
        
        return JsonResponse({
            'success': True,
            'entity_uri': entity_uri,
            'details': details
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des détails pour {entity_uri}: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def entities_list_view(request):
    """Vue pour afficher la liste simplifiée des entités - Tous les utilisateurs"""
    try:
        # Récupérer les statistiques de base pour tous les types d'entités
        stats = rdf_manager.get_statistics()
        
        # Récupérer un échantillon d'entités pour chaque type
        entities_sample = {}
        
        try:
            # Pour les utilisateurs normaux, on ne montre que les entités publiques
            entities_sample['vehicles'] = rdf_manager.get_vehicles_data()[:5]
            entities_sample['stations'] = rdf_manager.get_stations_data()[:5]
            entities_sample['trips'] = rdf_manager.get_trips_data()[:5]
            
            # Les données de trafic et utilisateurs sont réservées aux admins
            if est_administrateur(request.user):
                entities_sample['users'] = rdf_manager.get_user_data()[:5]
                entities_sample['traffic'] = rdf_manager.get_traffic_data()[:5]
                
        except Exception as e:
            logger.warning(f"Erreur lors de la récupération d'échantillons: {e}")
        
        context = {
            'page_title': 'Entités - SmartCity',
            'statistics': stats,
            'entities_sample': entities_sample,
            'is_admin': est_administrateur(request.user),
        }
        
        return render(request, 'entities_overview.html', context)
        
    except Exception as e:
        logger.error(f"Erreur dans entities_list_view: {e}")
        messages.error(request, f"Erreur lors du chargement des entités: {str(e)}")
        if est_administrateur(request.user):
            return redirect('gestion_utilisateurs:dashboard_admin')
        else:
            return redirect('gestion_utilisateurs:dashboard_user')


def registration_view(request):
    """Vue pour l'inscription des nouveaux utilisateurs"""
    if request.method == 'POST':
        try:
            # Récupération des données du formulaire
            nom = request.POST.get('nom', '').strip()
            prenom = request.POST.get('prenom', '').strip()
            username = request.POST.get('username', '').strip()
            email = request.POST.get('email', '').strip()
            telephone = request.POST.get('telephone', '').strip()
            password1 = request.POST.get('password1', '')
            password2 = request.POST.get('password2', '')
            accept_terms = request.POST.get('accept_terms')
            
            # Validation côté serveur
            errors = []
            
            # Vérifications de base
            if not all([nom, prenom, username, email, password1, password2]):
                errors.append("Tous les champs obligatoires doivent être remplis.")
            
            if not accept_terms:
                errors.append("Vous devez accepter les conditions d'utilisation.")
            
            # Validation du nom d'utilisateur
            if len(username) < 3 or len(username) > 30:
                errors.append("Le nom d'utilisateur doit contenir entre 3 et 30 caractères.")
            
            if not re.match(r'^[a-zA-Z0-9_]+$', username):
                errors.append("Le nom d'utilisateur ne peut contenir que des lettres, chiffres et underscore.")
            
            # Vérifier l'unicité du nom d'utilisateur
            if User.objects.filter(username=username).exists():
                errors.append("Ce nom d'utilisateur est déjà utilisé.")
            
            # Vérifier l'unicité de l'email
            if User.objects.filter(email=email).exists():
                errors.append("Cette adresse email est déjà utilisée.")
            
            # Validation du mot de passe
            if len(password1) < 8:
                errors.append("Le mot de passe doit contenir au moins 8 caractères.")
            
            if password1 != password2:
                errors.append("Les mots de passe ne correspondent pas.")
            
            # Validation de l'email
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                errors.append("L'adresse email n'est pas valide.")
            
            if errors:
                for error in errors:
                    messages.error(request, error)
                return render(request, 'gestion_utilisateurs/registration.html')
            
            # Création de l'utilisateur avec transaction
            with transaction.atomic():
                # Créer l'utilisateur Django
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password1,
                    first_name=prenom,
                    last_name=nom
                )
                
                # Récupérer le rôle utilisateur par défaut
                try:
                    role_user = RoleUtilisateur.objects.get(type_role='admin')
                except RoleUtilisateur.DoesNotExist:
                    logger.error("Rôle 'user' non trouvé. Exécutez init_roles.py")
                    messages.error(request, "Erreur de configuration du système. Contactez l'administrateur.")
                    return render(request, 'gestion_utilisateurs/registration.html')
                
                # Le profil utilisateur est créé automatiquement par le signal post_save
                # Récupérons-le et mettons-le à jour avec les informations supplémentaires
                profil = ProfilUtilisateur.objects.get(user=user)
                profil.telephone = telephone
                # Le rôle est déjà défini par le signal, mais on peut le forcer si nécessaire
                if not profil.role:
                    profil.role = role_user
                profil.save()
                
                # Ajouter l'utilisateur au fichier RDF
                try:
                    rdf_manager.add_user_to_rdf(
                        user_id=str(user.id),
                        nom=nom,
                        prenom=prenom,
                        email=email,
                        telephone=telephone,
                        role='user'
                    )
                    logger.info(f"Utilisateur {username} ajouté au fichier RDF")
                except Exception as rdf_error:
                    logger.error(f"Erreur lors de l'ajout dans le RDF: {rdf_error}")
                    # On continue même si l'ajout RDF échoue
                
                messages.success(
                    request, 
                    f"Compte créé avec succès ! Bienvenue {prenom} {nom}. Vous pouvez maintenant vous connecter."
                )
                
                # Rediriger vers la page de connexion
                return redirect('gestion_utilisateurs:connexion')
                
        except Exception as e:
            logger.error(f"Erreur lors de l'inscription: {e}")
            import traceback
            logger.error(f"Traceback complet: {traceback.format_exc()}")
            messages.error(request, "Une erreur est survenue lors de la création du compte. Veuillez réessayer.")
            return render(request, 'gestion_utilisateurs/registration.html')
    
    # GET - Afficher le formulaire d'inscription
    return render(request, 'gestion_utilisateurs/registration.html')