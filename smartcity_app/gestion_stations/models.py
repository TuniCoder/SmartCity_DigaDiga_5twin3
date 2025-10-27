"""
Gestion des Stations - SmartCity
Domaine de gestion : 🚏 Stations

Ce module gère :
- Stations de transport public (métro, bus, tramway)
- Points de stationnement de véhicules partagés
- Bornes de recharge électrique
- Services et équipements des stations
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class TypeStation(models.Model):
    """Types de stations dans le système de transport urbain"""
    
    CATEGORIES = [
        ('metro', 'Station de Métro'),
        ('bus', 'Arrêt de Bus'),
        ('tramway', 'Station de Tramway'),
        ('train', 'Gare'),
        ('velo_partage', 'Station de Vélos Partagés'),
        ('trottinette', 'Station de Trottinettes'),
        ('voiture_partage', 'Station de Voitures Partagées'),
        ('borne_recharge', 'Borne de Recharge'),
        ('parking', 'Parking'),
        ('multimodal', 'Pôle Multimodal'),
    ]
    
    nom = models.CharField(max_length=100, unique=True)
    categorie = models.CharField(max_length=50, choices=CATEGORIES)
    description = models.TextField(blank=True)
    icone = models.CharField(max_length=50, blank=True, help_text="Classe CSS pour l'icône")
    couleur = models.CharField(max_length=7, default='#007bff', help_text="Couleur hexadécimale")
    
    # Caractéristiques
    capacite_moyenne = models.IntegerField(null=True, blank=True, help_text="Capacité moyenne d'accueil")
    accessible_pmr = models.BooleanField(default=False)
    couvert = models.BooleanField(default=False, help_text="Station couverte")
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True)
    derniere_mise_a_jour = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Type de Station"
        verbose_name_plural = "Types de Stations"
        ordering = ['categorie', 'nom']
    
    def __str__(self):
        return f"{self.nom} ({self.get_categorie_display()})"


class Station(models.Model):
    """Station ou point d'arrêt dans le réseau de transport"""
    
    STATUTS = [
        ('active', 'Active'),
        ('maintenance', 'En Maintenance'),
        ('fermee', 'Fermée'),
        ('construction', 'En Construction'),
    ]
    
    NIVEAUX_ACCESSIBILITE = [
        ('totalement_accessible', 'Totalement Accessible'),
        ('partiellement_accessible', 'Partiellement Accessible'),
        ('non_accessible', 'Non Accessible'),
        ('en_cours_amenagement', 'En Cours d\'Aménagement'),
    ]
    
    # Informations de base
    nom = models.CharField(max_length=200)
    type_station = models.ForeignKey(TypeStation, on_delete=models.CASCADE, related_name='stations')
    code_station = models.CharField(max_length=50, unique=True)
    
    # Localisation
    adresse = models.TextField()
    latitude = models.FloatField()
    longitude = models.FloatField()
    altitude = models.FloatField(null=True, blank=True, help_text="Altitude en mètres")
    
    # Informations opérationnelles
    statut = models.CharField(max_length=20, choices=STATUTS, default='active')
    horaires_ouverture = models.JSONField(default=dict, blank=True, help_text="Horaires par jour de la semaine")
    capacite_actuelle = models.IntegerField(null=True, blank=True)
    capacite_maximale = models.IntegerField(null=True, blank=True)
    
    # Accessibilité
    niveau_accessibilite = models.CharField(max_length=50, choices=NIVEAUX_ACCESSIBILITE, default='non_accessible')
    equipements_pmr = models.TextField(blank=True, help_text="Équipements pour personnes à mobilité réduite")
    
    # Zone et connexions
    zone_tarifaire = models.CharField(max_length=50, blank=True)
    lignes_desservies = models.JSONField(default=list, blank=True, help_text="Liste des lignes qui desservent cette station")
    correspondances = models.ManyToManyField('self', blank=True, symmetrical=True)
    
    # Informations pratiques
    description = models.TextField(blank=True)
    informations_voyageurs = models.TextField(blank=True)
    
    # Métadonnées
    date_mise_en_service = models.DateField(null=True, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    derniere_mise_a_jour = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Station"
        verbose_name_plural = "Stations"
        ordering = ['nom']
        indexes = [
            models.Index(fields=['latitude', 'longitude']),
            models.Index(fields=['code_station']),
            models.Index(fields=['statut']),
        ]
    
    def __str__(self):
        return f"{self.nom} ({self.type_station.get_categorie_display()})"
    
    @property
    def est_active(self):
        """Vérifie si la station est active"""
        return self.statut == 'active'
    
    @property
    def taux_occupation(self):
        """Calcule le taux d'occupation actuel de la station"""
        if self.capacite_maximale and self.capacite_actuelle is not None:
            return (self.capacite_actuelle / self.capacite_maximale) * 100
        return None


class EquipementStation(models.Model):
    """Équipements disponibles dans une station"""
    
    TYPES_EQUIPEMENT = [
        ('ascenseur', 'Ascenseur'),
        ('escalier_mecanique', 'Escalier Mécanique'),
        ('distributeur_tickets', 'Distributeur de Tickets'),
        ('borne_info', 'Borne d\'Information'),
        ('wifi', 'Wi-Fi Gratuit'),
        ('wc', 'Toilettes'),
        ('consigne', 'Consignes'),
        ('parking_velo', 'Parking Vélos'),
        ('borne_recharge', 'Borne de Recharge'),
        ('eclairage', 'Éclairage'),
        ('videosurveillance', 'Vidéosurveillance'),
        ('guichet', 'Guichet d\'Accueil'),
        ('commerces', 'Commerces'),
        ('banc', 'Bancs'),
        ('abri', 'Abri'),
    ]
    
    STATUTS_EQUIPEMENT = [
        ('fonctionnel', 'Fonctionnel'),
        ('en_panne', 'En Panne'),
        ('maintenance', 'En Maintenance'),
        ('hors_service', 'Hors Service'),
    ]
    
    station = models.ForeignKey(Station, on_delete=models.CASCADE, related_name='equipements')
    type_equipement = models.CharField(max_length=50, choices=TYPES_EQUIPEMENT)
    nom = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # État de l'équipement
    statut = models.CharField(max_length=20, choices=STATUTS_EQUIPEMENT, default='fonctionnel')
    derniere_verification = models.DateTimeField(null=True, blank=True)
    prochaine_maintenance = models.DateTimeField(null=True, blank=True)
    
    # Localisation dans la station
    niveau = models.CharField(max_length=50, blank=True, help_text="Niveau ou étage")
    zone = models.CharField(max_length=100, blank=True, help_text="Zone spécifique dans la station")
    
    # Caractéristiques techniques
    specifications_techniques = models.JSONField(default=dict, blank=True)
    fournisseur = models.CharField(max_length=100, blank=True)
    modele = models.CharField(max_length=100, blank=True)
    
    # Métadonnées
    date_installation = models.DateField(null=True, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    derniere_mise_a_jour = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Équipement de Station"
        verbose_name_plural = "Équipements de Stations"
        ordering = ['station', 'type_equipement', 'nom']
    
    def __str__(self):
        return f"{self.nom} ({self.get_type_equipement_display()}) - {self.station.nom}"
    
    @property
    def est_fonctionnel(self):
        """Vérifie si l'équipement est fonctionnel"""
        return self.statut == 'fonctionnel'


class IncidentStation(models.Model):
    """Incidents et signalements concernant les stations"""
    
    TYPES_INCIDENT = [
        ('panne_equipement', 'Panne d\'Équipement'),
        ('probleme_acces', 'Problème d\'Accessibilité'),
        ('vandalisme', 'Vandalisme'),
        ('nettoyage', 'Problème de Propreté'),
        ('securite', 'Problème de Sécurité'),
        ('information', 'Information Erronée'),
        ('autre', 'Autre'),
    ]
    
    NIVEAUX_PRIORITE = [
        ('basse', 'Basse'),
        ('normale', 'Normale'),
        ('haute', 'Haute'),
        ('critique', 'Critique'),
    ]
    
    STATUTS_INCIDENT = [
        ('signale', 'Signalé'),
        ('en_cours', 'En Cours de Traitement'),
        ('resolu', 'Résolu'),
        ('ferme', 'Fermé'),
    ]
    
    # Incident
    station = models.ForeignKey(Station, on_delete=models.CASCADE, related_name='incidents')
    equipement = models.ForeignKey(EquipementStation, on_delete=models.SET_NULL, null=True, blank=True)
    
    type_incident = models.CharField(max_length=50, choices=TYPES_INCIDENT)
    titre = models.CharField(max_length=200)
    description = models.TextField()
    
    # Gestion
    niveau_priorite = models.CharField(max_length=20, choices=NIVEAUX_PRIORITE, default='normale')
    statut = models.CharField(max_length=20, choices=STATUTS_INCIDENT, default='signale')
    
    # Personnes impliquées
    signale_par = models.CharField(max_length=100, blank=True)
    assigne_a = models.CharField(max_length=100, blank=True)
    
    # Temporal
    date_signalement = models.DateTimeField(auto_now_add=True)
    date_prise_en_compte = models.DateTimeField(null=True, blank=True)
    date_resolution = models.DateTimeField(null=True, blank=True)
    
    # Suivi
    actions_entreprises = models.TextField(blank=True)
    commentaires_resolution = models.TextField(blank=True)
    cout_reparation = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Métadonnées
    derniere_mise_a_jour = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Incident de Station"
        verbose_name_plural = "Incidents de Stations"
        ordering = ['-date_signalement']
    
    def __str__(self):
        return f"{self.titre} - {self.station.nom} ({self.get_statut_display()})"