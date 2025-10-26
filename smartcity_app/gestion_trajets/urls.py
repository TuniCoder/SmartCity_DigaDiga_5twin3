"""
URLs pour la Gestion des Trajets Intelligents - SmartCity
Domaine : 🚗 Trajets IA
"""

from django.urls import path
from . import views

app_name = 'gestion_trajets'

urlpatterns = [
    # Page d'accueil du module
    path('', views.index_trajets_view, name='index_trajets'),
    
    # Vue principale du planificateur
    path('planificateur/', views.planificateur_trajet_view, name='planificateur_trajet'),
    
    # Création et gestion des demandes
    path('creer-demande/', views.creer_demande_trajet_view, name='creer_demande_trajet'),
    path('resultats/<int:demande_id>/', views.resultats_trajet_view, name='resultats_trajet'),
    
    # Transport en temps réel
    path('temps-reel/', views.temps_reel_transport_view, name='temps_reel_transport'),
    
    # Historique et préférences
    path('mes-trajets/', views.mes_trajets_view, name='mes_trajets'),
    path('preferences/', views.preferences_trajet_view, name='preferences_trajet'),
    
    # Gestion des demandes de trajets
    path('supprimer/<int:demande_id>/', views.supprimer_demande_trajet_view, name='supprimer_demande_trajet'),
    
    # AJAX endpoints
    path('ajax/recherche-lieux/', views.ajax_recherche_lieux, name='ajax_recherche_lieux'),
    path('ajax/actualiser/<int:demande_id>/', views.ajax_actualiser_temps_reel, name='ajax_actualiser_temps_reel'),
    
    # **NOUVEAUX ENDPOINTS** : Services avancés avec Leaflet et routing
    path('ajax/calculer-itineraire/', views.ajax_calculer_itineraire, name='ajax_calculer_itineraire'),
    path('ajax/recherche-intelligente/', views.ajax_recherche_trajets_intelligente, name='ajax_recherche_trajets_intelligente'),
]