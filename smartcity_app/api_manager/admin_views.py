from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages

@login_required
def index_api_manager(request):
    """Page d'accueil de l'API Manager"""
    context = {
        'page_title': 'API Manager - SmartCity',
        'module_name': 'API Manager',
        'module_description': 'Hub central pour toutes les APIs et services SmartCity',
        'coming_soon': True,
        'features_planned': [
            {
                'icon': 'bi-cloud-upload',
                'title': 'API Gateway Centralisé',
                'description': 'Point d\'entrée unique pour toutes les APIs',
                'status': 'progress'
            },
            {
                'icon': 'bi-shield-check',
                'title': 'Authentification & Sécurité',
                'description': 'JWT, API Keys et contrôle d\'accès',
                'status': 'planned'
            },
            {
                'icon': 'bi-speedometer',
                'title': 'Rate Limiting',
                'description': 'Gestion des quotas et limitation de débit',
                'status': 'planned'
            },
            {
                'icon': 'bi-book',
                'title': 'Documentation Auto',
                'description': 'Swagger/OpenAPI pour développeurs',
                'status': 'planned'
            },
            {
                'icon': 'bi-graph-up',
                'title': 'Analytics API',
                'description': 'Monitoring et métriques d\'utilisation',
                'status': 'planned'
            },
            {
                'icon': 'bi-code-slash',
                'title': 'Portail Développeur',
                'description': 'Interface pour développeurs externes',
                'status': 'planned'
            }
        ],
        'team_member': 'À définir',
        'contact_info': 'Module critique - Expertise APIs REST requise'
    }
    return render(request, 'coming_soon.html', context)

@login_required
def documentation_api(request):
    """Documentation des APIs (Swagger)"""
    return index_api_manager(request)

@login_required
def gestion_api_keys(request):
    """Gestion des clés API"""
    return index_api_manager(request)

@login_required
def analytics_api(request):
    """Analytics et monitoring des APIs"""
    return index_api_manager(request)

@login_required
def portail_developpeur(request):
    """Portail pour développeurs externes"""
    return index_api_manager(request)