"""
Chatbot Models for AI Assistant
"""
from django.db import models
from django.contrib.auth.models import User


class ChatMessage(models.Model):
    """Modèle pour stocker l'historique des conversations avec l'IA"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chatbot_messages')
    message = models.TextField(verbose_name="Message utilisateur")
    response = models.TextField(verbose_name="Réponse IA")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    message_type = models.CharField(
        max_length=20,
        choices=[
            ('question', 'Question'),
            ('general', 'Général'),
            ('vehicle', 'Véhicule'),
            ('maintenance', 'Maintenance'),
        ],
        default='question',
        verbose_name="Type de message"
    )
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Message de chat"
        verbose_name_plural = "Messages de chat"
    
    def __str__(self):
        return f"{self.user.username} - {self.timestamp.strftime('%d/%m/%Y %H:%M')}"


class AIAssistant(models.Model):
    """Modèle pour la configuration de l'assistant IA"""
    name = models.CharField(max_length=100, default="Assistant SmartCity", verbose_name="Nom de l'assistant")
    system_prompt = models.TextField(
        default="Tu es un assistant intelligent spécialisé dans la gestion de ville intelligente (SmartCity). Tu peux aider avec la gestion de véhicules, la mobilité urbaine, les transports, et toutes questions liées à la ville intelligente. Réponds en français de manière claire et professionnelle.",
        verbose_name="Prompt système"
    )
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Assistant IA"
        verbose_name_plural = "Assistants IA"
    
    def __str__(self):
        return self.name