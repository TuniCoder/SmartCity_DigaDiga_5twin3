"""
URLs pour la Gestion de Location - SmartCity
Module : 🚗 Location de Véhicules Intelligente
"""

from django.urls import path
from . import views

app_name = 'gestion_location'

urlpatterns = [
    # ========== VUES CLIENT (Frontend) ==========
    
    # Dashboard principal
    path('', views.index_location_view, name='index_location'),
    
    # Recherche et location
    path('rechercher/', views.rechercher_vehicules_view, name='rechercher_vehicules'),
    path('creer-location/', views.creer_location_view, name='creer_location'),
    
    # Gestion des locations utilisateur
    path('mes-locations/', views.mes_locations_view, name='mes_locations'),
    # Accept string IDs so we can view RDF locations by their numero (e.g. "LOC2025XXX")
    path('location/<str:location_id>/', views.detail_location_view, name='detail_location'),
path('modifier-location/<str:location_id>/', views.modifier_location_view, name='modifier_location'),
path('annuler-location/<str:location_id>/', views.annuler_location_view, name='annuler_location'),
    
    # ========== VUES ADMIN (Backend) ==========
    
    # Dashboard admin
    path('admin/', views.admin_dashboard_location_view, name='admin_dashboard'),
    path('admin/locations/', views.admin_liste_locations_view, name='admin_liste_locations'),
    
    # Actions admin
path('admin/supprimer-location/<str:location_id>/', views.admin_supprimer_location_view, name='admin_supprimer_location'),
path('admin/changer-statut/<str:location_id>/', views.admin_changer_statut_location_view, name='admin_changer_statut_location'),
    
    # ========== VUES AJAX ==========
    
    # Vérifications en temps réel
    path('ajax/disponibilite/<int:vehicule_id>/', views.ajax_disponibilite_vehicule, name='ajax_disponibilite_vehicule'),
    path('ajax/calculer-prix/', views.ajax_calculer_prix, name='ajax_calculer_prix'),
]
