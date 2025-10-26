from django.urls import path
from . import views

app_name = 'gestion_vehicules'

urlpatterns = [
    # Pages principales
    path('', views.index_vehicules, name='index_vehicules'),
    path('liste/', views.liste_vehicules, name='liste_vehicules'),
    path('flotte/', views.gestion_flotte, name='gestion_flotte'),
    path('tracking/', views.tracking_vehicules, name='tracking_vehicules'),
    path('maintenance/', views.gestion_maintenance, name='gestion_maintenance'),
    path('partages/', views.vehicules_partages, name='vehicules_partages'),
    path('analytics/', views.analytics_vehicules, name='analytics_vehicules'),
    
    # CRUD Véhicules
    path('creer/', views.creer_vehicule, name='creer_vehicule'),
    path('<int:vehicule_id>/', views.detail_vehicule, name='detail_vehicule'),
    path('<int:vehicule_id>/modifier/', views.modifier_vehicule, name='modifier_vehicule'),
    path('<int:vehicule_id>/supprimer/', views.supprimer_vehicule, name='supprimer_vehicule'),
    
    # API Endpoints
    path('api/vehicles/', views.api_vehicles_data, name='api_vehicles_data'),
    path('api/vehicles/<int:vehicule_id>/rdf/', views.api_vehicle_rdf_data, name='api_vehicle_rdf_data'),
    path('api/vehicles/<int:vehicule_id>/sync/', views.api_sync_vehicle_to_rdf, name='api_sync_vehicle_to_rdf'),
    path('api/statistics/', views.api_vehicle_statistics, name='api_vehicle_statistics'),
    path('api/positions/', views.api_positions, name='api_positions'),
    path('api/sync-from-rdf/', views.api_sync_from_rdf, name='api_sync_from_rdf'),
]