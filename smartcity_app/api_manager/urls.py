"""
Configuration des URLs pour l'API SmartCity
"""
from django.urls import path, include
from . import api_views, admin_views

app_name = 'api_manager'

urlpatterns = [
    # Interface d'administration API
    path('', admin_views.index_api_manager, name='index_api_manager'),
    path('docs/', admin_views.documentation_api, name='docs'),
    path('keys/', admin_views.gestion_api_keys, name='keys'),
    path('analytics/', admin_views.analytics_api, name='analytics'),
    path('portail/', admin_views.portail_developpeur, name='portail'),
    
    # API Status
    path('status/', api_views.get_api_status, name='api_status'),
    
    # IA & Natural Language Processing
    path('ask/', api_views.ask_ai_question, name='ask_ai'),
    
    # SPARQL Queries
    path('sparql/', api_views.execute_sparql_query, name='execute_sparql'),
    
    # Ontology Information
    path('ontology/info/', api_views.get_ontology_info, name='ontology_info'),
    
    # Entity Management
    path('entities/<str:entity_type>/', api_views.get_entities_by_type, name='get_entities'),
    
    # Search
    path('search/', api_views.search_entities, name='search_entities'),
    
    # Predefined Queries
    path('queries/predefined/', api_views.get_predefined_queries, name='predefined_queries'),
    path('queries/predefined/<str:query_id>/execute/', api_views.execute_predefined_query, name='execute_predefined'),
    
    # Trip Management
    path('trips/add/', api_views.add_trip_to_ontology, name='add_trip'),
    path('trips/delete/', api_views.delete_trip_from_ontology, name='delete_trip'),
    
    # Transport Options
    path('transport/options/', api_views.get_transport_options, name='transport_options'),
]