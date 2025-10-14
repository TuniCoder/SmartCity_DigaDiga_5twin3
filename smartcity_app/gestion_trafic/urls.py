from django.urls import path
from . import views

app_name = 'gestion_trafic'

urlpatterns = [
    path('', views.index_trafic, name='index_trafic'),
    path('monitoring/', views.monitoring_trafic, name='monitoring'),
    path('predictions/', views.predictions_trafic, name='predictions'),
    path('incidents/', views.gestion_incidents, name='incidents'),
    path('feux/', views.gestion_feux, name='feux'),
    path('capteurs/', views.gestion_capteurs, name='capteurs'),
    path('analytics/', views.analytics_trafic, name='analytics'),
    path('api/temps-reel/', views.api_temps_reel, name='api_temps_reel'),
]