from django.apps import AppConfig


class GestionTraficConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'smartcity_app.gestion_trafic'
    verbose_name = 'Gestion du Trafic'

    def ready(self):
        """Chargement des signaux et intégration RDF"""
        # Importer l'intégration RDF pour activer les signaux
        from . import rdf_integration
        print("🔄 Module d'intégration RDF chargé pour la gestion du trafic")

