from django.urls import path
from . import views

app_name = 'gestion_vehicules'

urlpatterns = [
    path('', views.index_vehicules, name='index_vehicules'),
    path('flotte/', views.gestion_flotte, name='flotte'),
    path('tracking/', views.tracking_vehicules, name='tracking'),
    path('maintenance/', views.gestion_maintenance, name='maintenance'),
    path('partages/', views.vehicules_partages, name='partages'),
    path('analytics/', views.analytics_vehicules, name='analytics'),
    path('conducteurs/', views.gestion_conducteurs, name='conducteurs'),
    path('api/positions/', views.api_positions, name='api_positions'),
]