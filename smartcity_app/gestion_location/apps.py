"""
Configuration de l'application Gestion de Location - SmartCity
"""

from django.apps import AppConfig


class GestionLocationConfig(AppConfig):
    """Configuration pour l'application Gestion de Location"""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'smartcity_app.gestion_location'
    verbose_name = 'Gestion de Location'
    
    def ready(self):
        """Code exécuté au démarrage de l'application"""
        # Import des signaux si nécessaire
        pass
