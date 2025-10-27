"""
Configuration des modèles Django pour SmartCity
Ces modèles sont optionnels car nous utilisons principalement RDF
"""

from django.db import models
from django.contrib.auth.models import User

# Importer les modèles des modules de gestion
from .gestion_utilisateurs.models import *
from .gestion_vehicules.models import *
from .gestion_stations.models import *
from .gestion_trafic.models import *
from .gestion_trajets.models import *
from .gestion_location.models import *


class UserProfile(models.Model):
    """Profil utilisateur étendu (optionnel)"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    rdf_uri = models.URLField(blank=True, null=True, help_text="URI RDF de l'utilisateur dans l'ontologie")
    transport_preferences = models.JSONField(default=dict, help_text="Préférences de transport en JSON")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Profil Utilisateur"
        verbose_name_plural = "Profils Utilisateurs"

    def __str__(self):
        return f"Profil de {self.user.username}"


class QueryLog(models.Model):
    """Journal des requêtes pour analyse et amélioration"""
    QUERY_TYPES = [
        ('natural', 'Question Naturelle'),
        ('sparql', 'Requête SPARQL'),
        ('predefined', 'Requête Prédéfinie'),
        ('api', 'Requête API'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    query_type = models.CharField(max_length=20, choices=QUERY_TYPES)
    original_query = models.TextField(help_text="Question originale ou requête SPARQL")
    generated_sparql = models.TextField(blank=True, help_text="SPARQL généré par l'IA")
    results_count = models.IntegerField(default=0)
    execution_time = models.FloatField(help_text="Temps d'exécution en secondes")
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Journal de Requête"
        verbose_name_plural = "Journal des Requêtes"
        ordering = ['-timestamp']

    def __str__(self):
        return f"Requête {self.query_type} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"


class SystemSettings(models.Model):
    """Configuration système"""
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Paramètre Système"
        verbose_name_plural = "Paramètres Système"

    def __str__(self):
        return f"{self.key}: {self.value[:50]}..."


class FeedbackMessage(models.Model):
    """Messages de feedback des utilisateurs"""
    FEEDBACK_TYPES = [
        ('bug', 'Signalement de Bug'),
        ('suggestion', 'Suggestion d\'amélioration'),
        ('question', 'Question'),
        ('compliment', 'Compliment'),
    ]

    name = models.CharField(max_length=100)
    email = models.EmailField()
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_TYPES)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    query_context = models.TextField(blank=True, help_text="Contexte de la requête si applicable")
    resolved = models.BooleanField(default=False)
    admin_response = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Message de Feedback"
        verbose_name_plural = "Messages de Feedback"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.feedback_type.title()} de {self.name}: {self.subject}"