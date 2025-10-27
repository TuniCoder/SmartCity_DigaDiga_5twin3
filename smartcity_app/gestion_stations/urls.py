from django.urls import path
from . import views

app_name = 'gestion_stations'

urlpatterns = [
    path('', views.index_stations, name='index_stations'),
    path('dashboard/', views.dashboard_stations, name='dashboard'),
    path('liste/', views.liste_stations, name='liste'),
    path('ajouter/', views.ajouter_station, name='ajouter'),
    path('modifier/<int:station_id>/', views.modifier_station, name='modifier'),
    path('details/<int:station_id>/', views.details_station, name='details'),
    path('monitoring/', views.monitoring_stations, name='monitoring'),
    path('equipements/', views.gestion_equipements, name='equipements'),
]