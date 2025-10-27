"""
Configuration des URLs pour l'application SmartCity
"""
from django.urls import path, include
from django.views.generic import RedirectView
from .views_manager import views_main

app_name = 'smartcity_app'

urlpatterns = [
    # Page d'accueil
    path('', views_main.index_view, name='index'),
    
    # Ontologie
    path('ontology/', views_main.ontology_view, name='ontology_view'),
    
    # Requêtes et IA
    path('query/', views_main.query_view, name='query'),
    
    # Entités par type
    path('entities/<str:entity_type>/', views_main.entities_view, name='entities'),
    
    # Liste des entités (pour tous les utilisateurs)
    path('entities/', views_main.entities_list_view, name='entities_list'),
    
    # Recherche
    path('search/', views_main.search_view, name='search'),
    
    # AJAX endpoints
    path('ajax/entity-details/<path:entity_uri>/', views_main.ajax_entity_details, name='ajax_entity_details'),
    
    # Modules de gestion
    path('trajets/', include('smartcity_app.gestion_trajets.urls')),
    
    # Module de paiement Stripe
    path('payment/', include('smartcity_app.payment_service.urls')),
    
    # Redirections pour compatibilité
    path('home/', RedirectView.as_view(pattern_name='smartcity_app:index', permanent=True)),
    path('dashboard/', RedirectView.as_view(pattern_name='smartcity_app:index', permanent=True)),
]