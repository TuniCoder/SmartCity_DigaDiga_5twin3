"""
Gestion des Véhicules - SmartCity
Domaine de gestion : 🚗 Véhicules

Ce module gère :
- Types de véhicules et leurs caractéristiques
- Parc de véhicules de transport public
- Véhicules partagés (vélos, trottinettes, voitures)
- Maintenance et disponibilité des véhicules
- Intégration avec l'ontologie RDF
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
import logging

logger = logging.getLogger(__name__)


class TypeVehicule(models.Model):
    """Types de véhicules dans le système de mobilité urbaine"""
    
    CATEGORIES = [
        ('transport_public', 'Transport Public'),
        ('vehicule_partage', 'Véhicule Partagé'),
        ('vehicule_prive', 'Véhicule Privé'),
        ('vehicule_service', 'Véhicule de Service'),
    ]
    
    MODES_PROPULSION = [
        ('electrique', 'Électrique'),
        ('hybride', 'Hybride'),
        ('essence', 'Essence'),
        ('diesel', 'Diesel'),
        ('gaz', 'Gaz'),
        ('hydrogene', 'Hydrogène'),
        ('musculaire', 'Musculaire'),
    ]
    
    nom = models.CharField(max_length=100, unique=True)
    categorie = models.CharField(max_length=50, choices=CATEGORIES)
    mode_propulsion = models.CharField(max_length=50, choices=MODES_PROPULSION)
    
    # Caractéristiques techniques
    capacite_passagers = models.IntegerField(validators=[MinValueValidator(1)])
    vitesse_max = models.FloatField(help_text="Vitesse maximale en km/h", null=True, blank=True)
    autonomie = models.FloatField(help_text="Autonomie en km", null=True, blank=True)
    
    # Caractéristiques environnementales
    emission_co2 = models.FloatField(help_text="Émissions CO2 en g/km", default=0)
    niveau_bruit = models.IntegerField(help_text="Niveau de bruit en dB", null=True, blank=True)
    
    # Accessibilité
    accessible_pmr = models.BooleanField(default=False, help_text="Accessible aux personnes à mobilité réduite")
    equipements_accessibilite = models.TextField(blank=True)
    
    # Métadonnées
    description = models.TextField(blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    derniere_mise_a_jour = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Type de Véhicule"
        verbose_name_plural = "Types de Véhicules"
        ordering = ['categorie', 'nom']
    
    def __str__(self):
        return f"{self.nom} ({self.get_categorie_display()})"


class Vehicule(models.Model):
    """Instance spécifique d'un véhicule"""
    
    STATUTS = [
        ('actif', 'Actif'),
        ('maintenance', 'En Maintenance'),
        ('hors_service', 'Hors Service'),
        ('reserve', 'Réservé'),
    ]
    
    type_vehicule = models.ForeignKey(TypeVehicule, on_delete=models.CASCADE, related_name='vehicules')
    numero_identification = models.CharField(max_length=50, unique=True)
    immatriculation = models.CharField(max_length=20, blank=True)
    
    # Localisation et disponibilité
    localisation_actuelle = models.CharField(max_length=200, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUTS, default='actif')
    
    # Informations techniques
    annee_fabrication = models.IntegerField(null=True, blank=True)
    kilometrage = models.FloatField(default=0, help_text="Kilométrage total")
    niveau_batterie = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        null=True, blank=True,
        help_text="Niveau de batterie en pourcentage"
    )
    
    # Maintenance
    derniere_maintenance = models.DateTimeField(null=True, blank=True)
    prochaine_maintenance = models.DateTimeField(null=True, blank=True)
    
    # Métadonnées
    date_mise_en_service = models.DateTimeField(auto_now_add=True)
    derniere_mise_a_jour = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Véhicule"
        verbose_name_plural = "Véhicules"
        ordering = ['type_vehicule', 'numero_identification']
    
    def __str__(self):
        return f"{self.type_vehicule.nom} - {self.numero_identification}"
    
    @property
    def est_disponible(self):
        """Vérifie si le véhicule est disponible pour utilisation"""
        return self.statut == 'actif'
    
    @property
    def necessite_maintenance(self):
        """Vérifie si le véhicule nécessite une maintenance"""
        if self.prochaine_maintenance:
            from django.utils import timezone
            return timezone.now() >= self.prochaine_maintenance
        return False
    
    def to_rdf_data(self):
        """Convertit l'instance Django en dictionnaire pour l'ontologie RDF"""
        return {
            'type_vehicule': self.type_vehicule.nom,
            'marque': getattr(self, 'marque', ''),
            'modele': getattr(self, 'modele', ''),
            'couleur': getattr(self, 'couleur', ''),
            'statut': self.statut,
            'localisation': self.localisation_actuelle,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'niveau_batterie': getattr(self, 'niveau_batterie', None),
            'capacite_passagers': self.type_vehicule.capacite_passagers,
            'emission_co2': self.type_vehicule.emission_co2,
            'accessible_pmr': self.type_vehicule.accessible_pmr,
        }
    
    def sync_to_rdf(self):
        """Synchronise le véhicule avec l'ontologie RDF"""
        try:
            from ..ontology_manager.vehicle_rdf_manager import vehicle_rdf_manager
            
            vehicle_data = self.to_rdf_data()
            vehicle_id = f"Vehicule_{self.id}"
            
            # Vérifier si le véhicule existe déjà dans le RDF
            existing_vehicle = vehicle_rdf_manager.get_vehicle_by_id(vehicle_id)
            
            if existing_vehicle:
                # Mettre à jour
                success, message = vehicle_rdf_manager.update_vehicle(vehicle_id, vehicle_data)
                if success:
                    logger.info(f"Véhicule {self.id} synchronisé avec le RDF (mise à jour)")
                else:
                    logger.error(f"Erreur lors de la synchronisation RDF du véhicule {self.id}: {message}")
            else:
                # Créer
                success, message = vehicle_rdf_manager.create_vehicle(vehicle_data)
                if success:
                    logger.info(f"Véhicule {self.id} synchronisé avec le RDF (création)")
                else:
                    logger.error(f"Erreur lors de la synchronisation RDF du véhicule {self.id}: {message}")
                    
        except Exception as e:
            logger.error(f"Erreur lors de la synchronisation RDF du véhicule {self.id}: {e}")
    
    def delete_from_rdf(self):
        """Supprime le véhicule de l'ontologie RDF"""
        try:
            from ..ontology_manager.vehicle_rdf_manager import vehicle_rdf_manager
            
            vehicle_id = f"Vehicule_{self.id}"
            success, message = vehicle_rdf_manager.delete_vehicle(vehicle_id)
            
            if success:
                logger.info(f"Véhicule {self.id} supprimé du RDF")
            else:
                logger.error(f"Erreur lors de la suppression RDF du véhicule {self.id}: {message}")
                
        except Exception as e:
            logger.error(f"Erreur lors de la suppression RDF du véhicule {self.id}: {e}")


class MaintenanceVehicule(models.Model):
    """Historique et planification de la maintenance des véhicules"""
    
    TYPES_MAINTENANCE = [
        ('preventive', 'Préventive'),
        ('corrective', 'Corrective'),
        ('revision', 'Révision'),
        ('reparation', 'Réparation'),
        ('controle', 'Contrôle Technique'),
    ]
    
    STATUTS_INTERVENTION = [
        ('planifiee', 'Planifiée'),
        ('en_cours', 'En Cours'),
        ('terminee', 'Terminée'),
        ('annulee', 'Annulée'),
    ]
    
    vehicule = models.ForeignKey(Vehicule, on_delete=models.CASCADE, related_name='maintenances')
    type_maintenance = models.CharField(max_length=50, choices=TYPES_MAINTENANCE)
    statut = models.CharField(max_length=20, choices=STATUTS_INTERVENTION, default='planifiee')
    
    # Planning
    date_planifiee = models.DateTimeField()
    date_debut_relle = models.DateTimeField(null=True, blank=True)
    date_fin_relle = models.DateTimeField(null=True, blank=True)
    
    # Détails de l'intervention
    description = models.TextField()
    technicien_responsable = models.CharField(max_length=100, blank=True)
    cout_estime = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cout_reel = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Pièces et matériaux
    pieces_changees = models.JSONField(default=list, blank=True)
    materiel_utilise = models.TextField(blank=True)
    
    # Résultat
    problemes_detectes = models.TextField(blank=True)
    actions_realisees = models.TextField(blank=True)
    recommandations = models.TextField(blank=True)
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True)
    derniere_mise_a_jour = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Maintenance de Véhicule"
        verbose_name_plural = "Maintenances de Véhicules"
        ordering = ['-date_planifiee']
    
    def __str__(self):
        return f"{self.get_type_maintenance_display()} - {self.vehicule} ({self.date_planifiee.strftime('%d/%m/%Y')})"


class UtilisationVehicule(models.Model):
    """Historique d'utilisation des véhicules"""
    
    vehicule = models.ForeignKey(Vehicule, on_delete=models.CASCADE, related_name='utilisations')
    
    # Informations de trajet
    heure_debut = models.DateTimeField()
    heure_fin = models.DateTimeField(null=True, blank=True)
    lieu_depart = models.CharField(max_length=200)
    lieu_arrivee = models.CharField(max_length=200, blank=True)
    
    # Métriques
    distance_parcourue = models.FloatField(null=True, blank=True, help_text="Distance en km")
    nombre_passagers = models.IntegerField(default=0)
    consommation_energie = models.FloatField(null=True, blank=True, help_text="Consommation en kWh ou L")
    
    # Conditions
    conditions_meteo = models.CharField(max_length=100, blank=True)
    niveau_trafic = models.CharField(max_length=50, blank=True)
    
    # Évaluation
    note_experience = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True
    )
    commentaires = models.TextField(blank=True)
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Utilisation de Véhicule"
        verbose_name_plural = "Utilisations de Véhicules"
        ordering = ['-heure_debut']
    
    def __str__(self):
        return f"{self.vehicule} - {self.heure_debut.strftime('%d/%m/%Y %H:%M')}"


# Signaux Django pour synchronisation automatique avec RDF
@receiver(post_save, sender=Vehicule)
def sync_vehicle_to_rdf_on_save(sender, instance, created, **kwargs):
    """Synchronise automatiquement le véhicule avec l'ontologie RDF lors de la sauvegarde"""
    try:
        instance.sync_to_rdf()
    except Exception as e:
        logger.error(f"Erreur lors de la synchronisation automatique du véhicule {instance.id}: {e}")

@receiver(post_delete, sender=Vehicule)
def sync_vehicle_to_rdf_on_delete(sender, instance, **kwargs):
    """Supprime automatiquement le véhicule de l'ontologie RDF lors de la suppression"""
    try:
        instance.delete_from_rdf()
    except Exception as e:
        logger.error(f"Erreur lors de la suppression automatique du véhicule {instance.id} du RDF: {e}")


class ChatMessage(models.Model):
    """Modèle pour stocker l'historique des conversations avec l'IA"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_messages')
    message = models.TextField(verbose_name="Message utilisateur")
    response = models.TextField(verbose_name="Réponse IA")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    message_type = models.CharField(
        max_length=20,
        choices=[
            ('question', 'Question'),
            ('maintenance', 'Maintenance'),
            ('diagnostic', 'Diagnostic'),
            ('general', 'Général'),
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
    name = models.CharField(max_length=100, default="Assistant Véhicules", verbose_name="Nom de l'assistant")
    system_prompt = models.TextField(
        default="Tu es un assistant spécialisé dans la gestion de véhicules et la maintenance automobile. Tu peux aider avec les diagnostics, les conseils de maintenance, les réparations et toutes questions liées aux véhicules.",
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