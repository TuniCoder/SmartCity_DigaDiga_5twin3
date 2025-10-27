"""
Configuration des URLs principales pour SmartCity
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('smartcity_app.urls')),
    path('users/', include('smartcity_app.gestion_utilisateurs.urls')),
    path('api/', include('smartcity_app.api_manager.urls')),
    path('trajets/', include('smartcity_app.gestion_trajets.urls')),
    path('stations/', include('smartcity_app.gestion_stations.urls')),
    path('trafic/', include('smartcity_app.gestion_trafic.urls')),
    path('vehicules/', include('smartcity_app.gestion_vehicules.urls')),
    path('chat/', include('chatbot.urls')),
    path('location/', include('smartcity_app.gestion_location.urls')),
    path('payment_service/', include('smartcity_app.payment_service.urls')), 
]

# Servir les fichiers statiques et média en développement
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Configuration admin
admin.site.site_header = "Administration SmartCity"
admin.site.site_title = "SmartCity Admin"
admin.site.index_title = "Gestion de la Mobilité Urbaine"