from django.urls import path
from . import views
from . import api_views
from . import user_views
from . import user_api_views

app_name = 'gestion_trafic'

urlpatterns = [
    # Page d'accueil
    path('', views.index_trafic, name='index_trafic'),

    # CRUD Capteurs de Trafic (Admin)
    path('capteurs/', views.liste_capteurs, name='liste_capteurs'),
    path('capteurs/creer/', views.creer_capteur, name='creer_capteur'),
    path('capteurs/<int:capteur_id>/', views.detail_capteur, name='detail_capteur'),
    path('capteurs/<int:capteur_id>/modifier/', views.modifier_capteur, name='modifier_capteur'),
    path('capteurs/<int:capteur_id>/supprimer/', views.supprimer_capteur, name='supprimer_capteur'),

    # Vues existantes (redirections pour compatibilité)
    path('monitoring/', views.monitoring_trafic, name='monitoring'),
    path('predictions/', views.predictions_trafic, name='predictions'),
    path('incidents/', views.gestion_incidents, name='incidents'),
    path('feux/', views.gestion_feux, name='feux'),
    path('analytics/', views.analytics_trafic, name='analytics'),

    # Cartographie Admin
    path('carte/', views.carte_trafic, name='carte_trafic'),

    # ============================================================================
    # VUES UTILISATEUR - GESTION DU TRAFIC
    # ============================================================================
    path('user/dashboard/', user_views.dashboard_trafic, name='dashboard_trafic'),
    path('user/carte/', user_views.carte_trafic_user, name='carte_trafic_user'),
    path('user/alertes/', user_views.mes_alertes, name='mes_alertes'),
    path('user/trajets/', user_views.mes_trajets, name='mes_trajets'),
    path('user/trajets/planifier/', user_views.planifier_trajet, name='planifier_trajet'),
    path('user/statistiques/', user_views.mes_statistiques, name='mes_statistiques'),
    path('user/zone/<int:zone_id>/', user_views.detail_zone_user, name='detail_zone_user'),
    path('user/zone/<int:zone_id>/favorite/ajouter/', user_views.ajouter_zone_favorite, name='ajouter_zone_favorite'),
    path('user/zone/<int:zone_id>/favorite/retirer/', user_views.retirer_zone_favorite, name='retirer_zone_favorite'),

    # ============================================================================
    # API REST ENDPOINTS - CAPTEURS
    # ============================================================================
    path('api/capteurs/', api_views.api_capteurs, name='api_capteurs'),
    path('api/capteurs/<int:capteur_id>/', api_views.api_capteur_detail, name='api_capteur_detail'),

    # ============================================================================
    # API REST ENDPOINTS - DONNÉES DE TRAFIC
    # ============================================================================
    path('api/donnees/', api_views.api_donnees_trafic, name='api_donnees_trafic'),
    path('api/statistiques/', api_views.api_statistiques_trafic, name='api_statistiques_trafic'),

    # ============================================================================
    # API REST ENDPOINTS - ZONES ET INFRASTRUCTURE
    # ============================================================================
    path('api/zones/', api_views.api_zones_trafic, name='api_zones_trafic'),
    path('api/feux/', api_views.api_feux_signalisation, name='api_feux_signalisation'),

    # ============================================================================
    # API REST ENDPOINTS - ÉVÉNEMENTS
    # ============================================================================
    path('api/evenements/', api_views.api_evenements_trafic, name='api_evenements_trafic'),

    # ============================================================================
    # API REST ENDPOINTS - CARTOGRAPHIE (Google Maps & OpenStreetMap)
    # ============================================================================
    path('api/maps/capteurs/', api_views.api_maps_capteurs, name='api_maps_capteurs'),
    path('api/maps/zones/', api_views.api_maps_zones, name='api_maps_zones'),
    path('api/maps/directions/', api_views.api_maps_directions, name='api_maps_directions'),
    path('api/maps/heatmap/', api_views.api_maps_heatmap, name='api_maps_heatmap'),
    path('api/maps/geocoding/', api_views.api_maps_geocoding, name='api_maps_geocoding'),
    path('api/maps/reverse-geocoding/', api_views.api_maps_reverse_geocoding, name='api_maps_reverse_geocoding'),

    # Legacy API endpoints (compatibilité)
    path('api/temps-reel/', views.api_temps_reel, name='api_temps_reel'),
    path('api/capteur/<int:capteur_id>/donnees/', views.api_donnees_capteur, name='api_donnees_capteur'),

    # ============================================================================
    # API ENDPOINTS UTILISATEUR
    # ============================================================================
    path('api/user/trafic-temps-reel/', user_api_views.api_trafic_temps_reel, name='api_trafic_temps_reel'),
    path('api/user/alertes/', user_api_views.api_mes_alertes, name='api_mes_alertes'),
    path('api/user/zones-favoris/', user_api_views.api_zones_favoris, name='api_zones_favoris'),
    path('api/user/capteurs-proches/', user_api_views.api_capteurs_proches, name='api_capteurs_proches'),
    path('api/user/statistiques/', user_api_views.api_mes_statistiques, name='api_mes_statistiques'),
    path('api/user/zone/<int:zone_id>/', user_api_views.api_detail_zone_user, name='api_detail_zone_user'),
]