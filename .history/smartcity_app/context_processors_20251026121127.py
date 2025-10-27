from django.conf import settings

def google_maps_api_key(request):
    """Ajoute la clé API Google Maps au contexte de tous les templates"""
    return {'google_maps_api_key': getattr(settings, 'GOOGLE_MAPS_API_KEY', '')}