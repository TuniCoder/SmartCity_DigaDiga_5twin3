"""
Modèles pour la Gestion de Location - SmartCity
Domaine : 🚗 Location de Véhicules Intelligente
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
import json
from django.core.exceptions import PermissionDenied


class TypeLocation(models.Model):
    """Types de location disponibles"""
    
    CATEGORIES = [
        ('voiture', 'Voiture'),
        ('velo', 'Vélo'),
        ('trottinette', 'Trottinette'),
        ('scooter', 'Scooter'),
        ('utilitaire', 'Véhicule Utilitaire'),
        ('luxe', 'Véhicule de Luxe'),
    ]
    
    nom = models.CharField(max_length=100, unique=True)
    categorie = models.CharField(max_length=50, choices=CATEGORIES)
    description = models.TextField(blank=True)
    icone = models.CharField(max_length=50, default="fas fa-car")
    couleur = models.CharField(max_length=7, default='#007bff')
    
    # Caractéristiques techniques
    capacite_passagers = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    capacite_bagages = models.IntegerField(default=0)
    vitesse_maximale = models.FloatField(null=True, blank=True, help_text="Vitesse max en km/h")
    autonomie_km = models.FloatField(null=True, blank=True, help_text="Autonomie en km")
    
    # Tarification
    prix_heure = models.DecimalField(max_digits=10, decimal_places=2, help_text="Prix par heure")
    prix_jour = models.DecimalField(max_digits=10, decimal_places=2, help_text="Prix par jour")
    prix_km = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Prix par km")
    caution_requise = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Caution en €")
    
    # Accessibilité et équipements
    accessible_pmr = models.BooleanField(default=False)
    permis_requis = models.CharField(max_length=20, default='B', help_text="Type de permis requis")
    age_minimum = models.IntegerField(default=18, help_text="Âge minimum")
    equipements = models.JSONField(default=list, blank=True, help_text="Équipements disponibles")
    
    # Impact environnemental
    emission_co2_par_km = models.FloatField(default=0, help_text="Émissions CO2 en g/km")
    consommation_moyenne = models.FloatField(null=True, blank=True, help_text="Consommation en L/100km")
    
    # Disponibilité
    disponible = models.BooleanField(default=True)
    nombre_total = models.IntegerField(default=1, help_text="Nombre total de véhicules de ce type")
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True)
    derniere_mise_a_jour = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Type de Location"
        verbose_name_plural = "Types de Location"
        ordering = ['categorie', 'nom']
    
    def __str__(self):
        return f"{self.nom} ({self.get_categorie_display()})"
    
    @property
    def prix_moyen_heure(self):
        """Calcule le prix moyen par heure"""
        return float(self.prix_heure)
    
    @property
    def est_electrique(self):
        """Vérifie si le véhicule est électrique"""
        return self.emission_co2_par_km < 50


class VehiculeLocation(models.Model):
    """Véhicule spécifique disponible à la location"""
    
    STATUTS = [
        ('disponible', 'Disponible'),
        ('loue', 'Loué'),
        ('maintenance', 'En Maintenance'),
        ('hors_service', 'Hors Service'),
        ('reserve', 'Réservé'),
    ]
    
    type_location = models.ForeignKey(TypeLocation, on_delete=models.CASCADE, related_name='vehicules')
    numero_identification = models.CharField(max_length=50, unique=True)
    immatriculation = models.CharField(max_length=20, blank=True)
    
    # Localisation actuelle
    station_location = models.CharField(max_length=200, blank=True, help_text="Station de location")
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    adresse_complete = models.TextField(blank=True)
    
    # État du véhicule
    statut = models.CharField(max_length=20, choices=STATUTS, default='disponible')
    niveau_carburant = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        null=True, blank=True,
        help_text="Niveau de carburant/batterie en %"
    )
    kilometrage_total = models.FloatField(default=0, help_text="Kilométrage total")
    
    # Informations techniques
    annee_fabrication = models.IntegerField(null=True, blank=True)
    couleur = models.CharField(max_length=50, blank=True)
    numero_serie = models.CharField(max_length=100, blank=True)
    
    # Maintenance
    derniere_maintenance = models.DateTimeField(null=True, blank=True)
    prochaine_maintenance = models.DateTimeField(null=True, blank=True)
    probleme_signale = models.TextField(blank=True, help_text="Problème signalé par le client")
    
    # Assurance et documents
    numero_assurance = models.CharField(max_length=100, blank=True)
    date_expiration_assurance = models.DateField(null=True, blank=True)
    controle_technique = models.DateField(null=True, blank=True)
    
    # Métadonnées
    date_mise_en_service = models.DateTimeField(auto_now_add=True)
    derniere_mise_a_jour = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Véhicule de Location"
        verbose_name_plural = "Véhicules de Location"
        ordering = ['type_location', 'numero_identification']
        indexes = [
            models.Index(fields=['statut']),
            models.Index(fields=['type_location', 'statut']),
            models.Index(fields=['latitude', 'longitude']),
        ]
    
    def __str__(self):
        return f"{self.type_location.nom} - {self.numero_identification}"
    
    @property
    def est_disponible(self):
        """Vérifie si le véhicule est disponible"""
        return self.statut == 'disponible'
    
    @property
    def necessite_maintenance(self):
        """Vérifie si le véhicule nécessite une maintenance"""
        if self.prochaine_maintenance:
            return timezone.now().date() >= self.prochaine_maintenance
        return False


class Location(models.Model):
    """Location de véhicule"""
    
    STATUTS_LOCATION = [
        ('en_attente', 'En Attente'),
        ('confirmee', 'Confirmée'),
        ('en_cours', 'En Cours'),
        ('terminee', 'Terminée'),
        ('annulee', 'Annulée'),
        ('en_retard', 'En Retard'),
    ]
    
    TYPES_LOCATION = [
        ('ponctuelle', 'Location Ponctuelle'),
        ('recurrente', 'Location Récurrente'),
        ('longue_duree', 'Location Longue Durée'),
        ('weekend', 'Location Weekend'),
        ('vacances', 'Location Vacances'),
    ]
    
    # Utilisateur et véhicule
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='locations')
    vehicule = models.ForeignKey(VehiculeLocation, on_delete=models.CASCADE, related_name='locations')
    
    # Informations de location
    numero_location = models.CharField(max_length=50, unique=True)
    type_location = models.CharField(max_length=50, choices=TYPES_LOCATION, default='ponctuelle')
    statut = models.CharField(max_length=20, choices=STATUTS_LOCATION, default='en_attente')
    
    # Dates et heures
    date_debut = models.DateTimeField()
    date_fin = models.DateTimeField()
    date_debut_reelle = models.DateTimeField(null=True, blank=True)
    date_fin_reelle = models.DateTimeField(null=True, blank=True)
    
    # Lieux de prise et retour
    lieu_prise = models.CharField(max_length=200)
    lieu_retour = models.CharField(max_length=200)
    latitude_prise = models.FloatField(null=True, blank=True)
    longitude_prise = models.FloatField(null=True, blank=True)
    latitude_retour = models.FloatField(null=True, blank=True)
    longitude_retour = models.FloatField(null=True, blank=True)
    
    # Informations conducteur
    conducteur_principal = models.CharField(max_length=200, help_text="Nom du conducteur principal")
    conducteur_secondaire = models.CharField(max_length=200, blank=True, help_text="Conducteur secondaire")
    numero_permis = models.CharField(max_length=50, blank=True)
    date_naissance = models.DateField(null=True, blank=True)
    
    # Tarification
    prix_heure = models.DecimalField(max_digits=10, decimal_places=2)
    prix_total_calcule = models.DecimalField(max_digits=10, decimal_places=2)
    prix_total_final = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    caution_payee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    caution_rendue = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Kilométrage
    kilometrage_depart = models.FloatField(null=True, blank=True)
    kilometrage_retour = models.FloatField(null=True, blank=True)
    kilometrage_total = models.FloatField(null=True, blank=True)
    
    # État du véhicule
    etat_depart = models.JSONField(default=dict, blank=True, help_text="État du véhicule au départ")
    etat_retour = models.JSONField(default=dict, blank=True, help_text="État du véhicule au retour")
    dommages_signales = models.TextField(blank=True, help_text="Dommages signalés")
    
    # Options et services
    options_choisies = models.JSONField(default=list, blank=True, help_text="Options supplémentaires")
    services_additionnels = models.JSONField(default=list, blank=True, help_text="Services additionnels")
    
    # Assurance
    assurance_comprise = models.BooleanField(default=True)
    franchise_assurance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    assurance_supplementaire = models.BooleanField(default=False)
    
    # Commentaires et évaluation
    commentaires_client = models.TextField(blank=True)
    note_experience = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True
    )
    commentaires_admin = models.TextField(blank=True)
    
    # Récurrence (pour locations récurrentes)
    est_recurrente = models.BooleanField(default=False)
    frequence_recurrence = models.CharField(max_length=50, blank=True)
    date_fin_recurrence = models.DateField(null=True, blank=True)
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True)
    derniere_mise_a_jour = models.DateTimeField(auto_now=True)
    cree_par_admin = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Location"
        verbose_name_plural = "Locations"
        ordering = ['-date_creation']
        indexes = [
            models.Index(fields=['utilisateur', 'statut']),
            models.Index(fields=['date_debut', 'date_fin']),
            models.Index(fields=['statut']),
            models.Index(fields=['numero_location']),
        ]
    
    def __str__(self):
        return f"Location {self.numero_location} - {self.utilisateur.username}"

    def save(self, *args, **kwargs):
        """
        Empêche la création d'une Location si l'utilisateur associé est un administrateur.
        Ceci renforce le contrôle côté modèle (au cas où une création contournerait la vue).
        """
        try:
            is_new = self._state.adding
        except Exception:
            is_new = False

        if is_new and self.utilisateur is not None:
            profil = getattr(self.utilisateur, 'profilutilisateur', None)
            if profil and getattr(profil, 'est_administrateur', False):
                raise PermissionDenied("Les administrateurs ne peuvent pas créer de réservations.")

        super().save(*args, **kwargs)
    
    @property
    def duree_location(self):
        """Calcule la durée de la location"""
        if self.date_debut and self.date_fin:
            delta = self.date_fin - self.date_debut
            return delta.total_seconds() / 3600  # en heures
        return 0
    
    @property
    def duree_reelle(self):
        """Calcule la durée réelle de la location"""
        if self.date_debut_reelle and self.date_fin_reelle:
            delta = self.date_fin_reelle - self.date_debut_reelle
            return delta.total_seconds() / 3600  # en heures
        return 0
    
    @property
    def est_en_cours(self):
        """Vérifie si la location est en cours"""
        maintenant = timezone.now()
        return (self.statut == 'en_cours' or 
                (self.date_debut <= maintenant <= self.date_fin and self.statut == 'confirmee'))
    
    @property
    def est_en_retard(self):
        """Vérifie si la location est en retard"""
        maintenant = timezone.now()
        return maintenant > self.date_fin and self.statut in ['en_cours', 'confirmee']


class OptionLocation(models.Model):
    """Options supplémentaires pour les locations"""
    
    CATEGORIES_OPTIONS = [
        ('confort', 'Confort'),
        ('securite', 'Sécurité'),
        ('navigation', 'Navigation'),
        ('divertissement', 'Divertissement'),
        ('bagages', 'Bagages'),
        ('autre', 'Autre'),
    ]
    
    nom = models.CharField(max_length=100)
    categorie = models.CharField(max_length=50, choices=CATEGORIES_OPTIONS)
    description = models.TextField()
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)
    unite_tarification = models.CharField(max_length=20, default='location', 
                                        help_text="location, jour, heure, km")
    
    # Disponibilité
    disponible = models.BooleanField(default=True)
    compatible_avec = models.ManyToManyField(TypeLocation, blank=True, 
                                           help_text="Types de véhicules compatibles")
    
    # Métadonnées
    icone = models.CharField(max_length=50, default="fas fa-plus")
    couleur = models.CharField(max_length=7, default='#6c757d')
    
    class Meta:
        verbose_name = "Option de Location"
        verbose_name_plural = "Options de Location"
        ordering = ['categorie', 'nom']
    
    def __str__(self):
        return f"{self.nom} ({self.get_categorie_display()}) - {self.prix_unitaire}€"


class ServiceLocation(models.Model):
    """Services additionnels pour les locations"""
    
    nom = models.CharField(max_length=100)
    description = models.TextField()
    prix_fixe = models.DecimalField(max_digits=10, decimal_places=2)
    prix_variable = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    unite_variable = models.CharField(max_length=20, blank=True, help_text="km, jour, etc.")
    
    # Conditions
    disponible = models.BooleanField(default=True)
    conditions_particulieres = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Service de Location"
        verbose_name_plural = "Services de Location"
        ordering = ['nom']
    
    def __str__(self):
        return f"{self.nom} - {self.prix_fixe}€"


class HistoriqueLocation(models.Model):
    """Historique des locations pour analytics et apprentissage"""
    
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='historique')
    
    # Métriques de performance
    satisfaction_client = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True
    )
    probleme_rencontre = models.BooleanField(default=False)
    type_probleme = models.CharField(max_length=100, blank=True)
    
    # Données d'usage
    distance_parcourue = models.FloatField(null=True, blank=True)
    consommation_carburant = models.FloatField(null=True, blank=True)
    nombre_passagers = models.IntegerField(default=1)
    
    # Apprentissage IA
    facteurs_satisfaction = models.JSONField(default=list, blank=True)
    recommandations_ia = models.JSONField(default=list, blank=True)
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Historique de Location"
        verbose_name_plural = "Historiques de Location"
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"Historique {self.location.numero_location}"


class AlerteLocation(models.Model):
    """Alertes et notifications pour les locations"""
    
    TYPES_ALERTE = [
        ('retard', 'Retard de Retour'),
        ('maintenance', 'Maintenance Requise'),
        ('probleme', 'Problème Signalé'),
        ('expiration', 'Expiration Assurance/Contrôle'),
        ('location', 'Nouvelle Location'),
        ('annulation', 'Annulation'),
    ]
    
    NIVEAUX_PRIORITE = [
        ('basse', 'Basse'),
        ('normale', 'Normale'),
        ('haute', 'Haute'),
        ('critique', 'Critique'),
    ]
    
    type_alerte = models.CharField(max_length=20, choices=TYPES_ALERTE)
    niveau_priorite = models.CharField(max_length=20, choices=NIVEAUX_PRIORITE, default='normale')
    
    titre = models.CharField(max_length=200)
    description = models.TextField()
    
    # Liens
    location = models.ForeignKey(Location, on_delete=models.CASCADE, 
                                   null=True, blank=True, related_name='alertes')
    vehicule = models.ForeignKey(VehiculeLocation, on_delete=models.CASCADE, 
                                null=True, blank=True, related_name='alertes')
    
    # Gestion
    active = models.BooleanField(default=True)
    traitee = models.BooleanField(default=False)
    traitee_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    date_traitement = models.DateTimeField(null=True, blank=True)
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True)
    date_echeance = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Alerte de Location"
        verbose_name_plural = "Alertes de Location"
        ordering = ['-niveau_priorite', '-date_creation']
    
    def __str__(self):
        return f"{self.get_type_alerte_display()}: {self.titre}"