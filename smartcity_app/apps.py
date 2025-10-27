from django.apps import AppConfig


class SmartcityAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'smartcity_app'
    verbose_name = 'SmartCity Application'

    def ready(self):
        """Chargement des signaux et intégration RDF"""
        # Importer l'intégration RDF pour activer les signaux
        try:
            from .gestion_trafic import rdf_integration
            # Module d'integration RDF charge pour la gestion du trafic
        except ImportError as e:
            pass  # Impossible de charger l'integration RDF

