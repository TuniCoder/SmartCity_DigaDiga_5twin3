"""
URLs pour la Gestion des Utilisateurs - SmartCity
Domaine : 👥 Utilisateurs
"""

from django.urls import path
from . import views
from ..views_manager.views_main import registration_view

app_name = 'gestion_utilisateurs'

urlpatterns = [
    # Authentification
    path('connexion/', views.connexion_view, name='connexion'),
    path('deconnexion/', views.deconnexion_view, name='deconnexion'),
    path('inscription/', registration_view, name='inscription'),
    
    # Profil utilisateur (commun)
    path('profil/', views.profil_utilisateur_view, name='profil_utilisateur'),
    path('profil/modifier/', views.modifier_profil_view, name='modifier_profil'),
    path('lieu-favori/ajouter/', views.ajouter_lieu_favori_view, name='ajouter_lieu_favori'),
    path('lieu-favori/supprimer/<int:lieu_id>/', views.supprimer_lieu_favori_view, name='supprimer_lieu_favori'),
    
    # Dashboard utilisateur normal
    path('dashboard/', views.dashboard_utilisateur_view, name='dashboard_user_old'),
    path('dashboard-user/', views.dashboard_user, name='dashboard_user'),
    path('mes-trajets/', views.mes_trajets_view, name='mes_trajets'),
    
    # Dashboard et gestion admin
    path('admin/dashboard/', views.dashboard_admin_view, name='dashboard_admin_old'),
    path('dashboard-admin/', views.dashboard_admin, name='dashboard_admin'),
    path('admin/utilisateurs/', views.gestion_utilisateurs_admin_view, name='gestion_users_admin'),
    path('utilisateurs/', views.liste_utilisateurs, name='liste_utilisateurs'),
    path('utilisateurs/creer/', views.creer_utilisateur, name='creer_utilisateur'),
    path('utilisateurs/voir/<int:user_id>/', views.voir_utilisateur, name='voir_utilisateur'),
    path('utilisateurs/modifier/<int:user_id>/', views.modifier_utilisateur, name='modifier_utilisateur'),
    path('utilisateurs/statut/<int:user_id>/', views.changer_statut_utilisateur, name='changer_statut_utilisateur'),
    path('utilisateurs/supprimer/<int:user_id>/', views.supprimer_utilisateur, name='supprimer_utilisateur'),
    path('modifier-role/<int:user_id>/', views.modifier_role_utilisateur, name='modifier_role_utilisateur'),
    path('synchroniser-rdf/', views.synchroniser_utilisateurs_rdf, name='synchroniser_rdf'),
    path('admin/changer-role/<int:user_id>/', views.changer_role_utilisateur, name='changer_role'),
    path('admin/tableau-bord/', views.tableau_bord_utilisateurs_view, name='tableau_bord_utilisateurs'),
    
    # API Endpoints
    path('api/profil/', views.api_profil_utilisateur, name='api_profil_utilisateur'),
    path('api/lieux-favoris/', views.api_lieux_favoris, name='api_lieux_favoris'),
]