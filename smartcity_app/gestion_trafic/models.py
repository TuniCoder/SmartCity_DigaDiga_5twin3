"""
Gestion du Trafic - SmartCity
Domaine de gestion : 🚦 Trafic

Ce module gère :
- Données de circulation en temps réel
- Feux de signalisation intelligents
- Conditions de trafic et congestion
- Événements affectant la circulation
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class ZoneTrafic(models.Model):
    """Zones de surveillance du trafic dans la ville"""
    
    TYPES_ZONE = [
        ('centre_ville', 'Centre-Ville'),
        ('peripherie', 'Périphérie'),
        ('zone_industrielle', 'Zone Industrielle'),
        ('zone_residentielle', 'Zone Résidentielle'),
        ('zone_commerciale', 'Zone Commerciale'),
        ('autoroute', 'Autoroute'),
        ('rocade', 'Rocade'),
        ('pont', 'Pont'),
        ('tunnel', 'Tunnel'),
    ]
    
    nom = models.CharField(max_length=100)
    type_zone = models.CharField(max_length=50, choices=TYPES_ZONE)
    description = models.TextField(blank=True)
    
    # Délimitation géographique
    coordonnees_zone = models.JSONField(help_text="Polygone définissant la zone (GeoJSON)")
    
    # Caractéristiques
    vitesse_limite = models.IntegerField(help_text="Vitesse limite en km/h")
    nombre_voies = models.IntegerField(default=2)
    sens_circulation = models.CharField(max_length=50, default='bidirectionnel')
    
    # Restrictions
    restrictions_horaires = models.JSONField(default=dict, blank=True)
    restrictions_vehicules = models.JSONField(default=list, blank=True)
    zone_pietons = models.BooleanField(default=False)
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True)
    derniere_mise_a_jour = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Zone de Trafic"
        verbose_name_plural = "Zones de Trafic"
        ordering = ['nom']
    
    def __str__(self):
        return f"{self.nom} ({self.get_type_zone_display()})"


class CapteurTrafic(models.Model):
    """Capteurs de mesure du trafic"""
    
    TYPES_CAPTEUR = [
        ('boucle_magnetique', 'Boucle Magnétique'),
        ('camera_ia', 'Caméra IA'),
        ('radar', 'Radar'),
        ('lidar', 'LiDAR'),
        ('capteur_bluetooth', 'Capteur Bluetooth'),
        ('capteur_wifi', 'Capteur Wi-Fi'),
        ('gps_flottant', 'Données GPS Flottantes'),
    ]
    
    STATUTS = [
        ('actif', 'Actif'),
        ('inactif', 'Inactif'),
        ('maintenance', 'En Maintenance'),
        ('defaillant', 'Défaillant'),
    ]
    
    # Identification
    nom = models.CharField(max_length=100)
    code_capteur = models.CharField(max_length=50, unique=True)
    type_capteur = models.CharField(max_length=50, choices=TYPES_CAPTEUR)
    
    # Localisation
    zone_trafic = models.ForeignKey(ZoneTrafic, on_delete=models.CASCADE, related_name='capteurs')
    latitude = models.FloatField()
    longitude = models.FloatField()
    direction_mesure = models.CharField(max_length=100, help_text="Direction de la voie mesurée")
    
    # Configuration technique
    statut = models.CharField(max_length=20, choices=STATUTS, default='actif')
    frequence_mesure = models.IntegerField(default=60, help_text="Fréquence de mesure en secondes")
    precision_detection = models.FloatField(default=95.0, help_text="Précision de détection en pourcentage")
    
    # Caractéristiques de mesure
    vitesse_min_detection = models.IntegerField(default=5, help_text="Vitesse minimale détectée en km/h")
    vitesse_max_detection = models.IntegerField(default=200, help_text="Vitesse maximale détectée en km/h")
    
    # Maintenance
    date_installation = models.DateField()
    derniere_calibration = models.DateTimeField(null=True, blank=True)
    prochaine_maintenance = models.DateField(null=True, blank=True)
    
    # Métadonnées
    fournisseur = models.CharField(max_length=100, blank=True)
    modele = models.CharField(max_length=100, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    derniere_mise_a_jour = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Capteur de Trafic"
        verbose_name_plural = "Capteurs de Trafic"
        ordering = ['zone_trafic', 'nom']
    
    def __str__(self):
        return f"{self.nom} ({self.code_capteur}) - {self.zone_trafic.nom}"
    
    @property
    def est_operationnel(self):
        """Vérifie si le capteur est opérationnel"""
        return self.statut == 'actif'


class DonneesTrafic(models.Model):
    """Données de trafic collectées en temps réel"""
    
    NIVEAUX_CONGESTION = [
        ('fluide', 'Trafic Fluide'),
        ('dense', 'Trafic Dense'),
        ('ralenti', 'Trafic Ralenti'),
        ('bouchon', 'Bouchon'),
        ('bloque', 'Circulation Bloquée'),
    ]
    
    # Source des données
    capteur = models.ForeignKey(CapteurTrafic, on_delete=models.CASCADE, related_name='donnees')
    timestamp = models.DateTimeField()
    
    # Métriques de trafic
    nombre_vehicules = models.IntegerField(default=0, help_text="Nombre de véhicules détectés")
    vitesse_moyenne = models.FloatField(null=True, blank=True, help_text="Vitesse moyenne en km/h")
    vitesse_mediane = models.FloatField(null=True, blank=True, help_text="Vitesse médiane en km/h")
    debit_vehicules = models.FloatField(null=True, blank=True, help_text="Débit en véhicules/heure")
    
    # Classification des véhicules
    vehicules_legers = models.IntegerField(default=0)
    vehicules_lourds = models.IntegerField(default=0)
    deux_roues = models.IntegerField(default=0)
    transports_publics = models.IntegerField(default=0)
    
    # État du trafic
    niveau_congestion = models.CharField(max_length=20, choices=NIVEAUX_CONGESTION)
    taux_occupation = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Taux d'occupation de la voie en pourcentage"
    )
    
    # Conditions
    conditions_meteo = models.CharField(max_length=100, blank=True)
    visibilite = models.IntegerField(null=True, blank=True, help_text="Visibilité en mètres")
    temperature = models.FloatField(null=True, blank=True, help_text="Température en °C")
    
    # Incidents détectés
    incident_detecte = models.BooleanField(default=False)
    type_incident = models.CharField(max_length=100, blank=True)
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Données de Trafic"
        verbose_name_plural = "Données de Trafic"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['capteur', 'timestamp']),
            models.Index(fields=['niveau_congestion']),
        ]
    
    def __str__(self):
        return f"{self.capteur.nom} - {self.timestamp.strftime('%d/%m/%Y %H:%M')} ({self.get_niveau_congestion_display()})"


class FeuSignalisation(models.Model):
    """Feux de signalisation intelligents"""
    
    TYPES_FEU = [
        ('tricolore_standard', 'Tricolore Standard'),
        ('tricolore_pietons', 'Tricolore avec Piétons'),
        ('clignotant', 'Feu Clignotant'),
        ('feu_priorite', 'Feu de Priorité'),
        ('panneau_variable', 'Panneau à Message Variable'),
    ]
    
    MODES_FONCTIONNEMENT = [
        ('automatique', 'Automatique'),
        ('adaptatif', 'Adaptatif au Trafic'),
        ('coordonne', 'Coordonné'),
        ('manuel', 'Manuel'),
        ('maintenance', 'Mode Maintenance'),
    ]
    
    # Identification
    nom = models.CharField(max_length=100)
    code_feu = models.CharField(max_length=50, unique=True)
    type_feu = models.CharField(max_length=50, choices=TYPES_FEU)
    
    # Localisation
    zone_trafic = models.ForeignKey(ZoneTrafic, on_delete=models.CASCADE, related_name='feux')
    latitude = models.FloatField()
    longitude = models.FloatField()
    carrefour = models.CharField(max_length=200, help_text="Description du carrefour")
    
    # Configuration
    mode_fonctionnement = models.CharField(max_length=50, choices=MODES_FONCTIONNEMENT, default='automatique')
    cycle_standard = models.JSONField(default=dict, help_text="Configuration du cycle standard")
    priorite_pietons = models.BooleanField(default=False)
    priorite_transports = models.BooleanField(default=False)
    
    # Paramètres adaptatifs
    capteurs_associes = models.ManyToManyField(CapteurTrafic, blank=True)
    seuil_adaptation_trafic = models.IntegerField(default=80, help_text="Seuil de déclenchement adaptation (%)")
    temps_reponse_max = models.IntegerField(default=300, help_text="Temps de réponse maximum en secondes")
    
    # État actuel
    phase_actuelle = models.CharField(max_length=50, blank=True)
    temps_restant_phase = models.IntegerField(null=True, blank=True, help_text="Temps restant en secondes")
    
    # Maintenance
    statut = models.CharField(max_length=20, default='actif')
    derniere_maintenance = models.DateTimeField(null=True, blank=True)
    prochaine_maintenance = models.DateField(null=True, blank=True)
    
    # Métadonnées
    date_installation = models.DateField()
    date_creation = models.DateTimeField(auto_now_add=True)
    derniere_mise_a_jour = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Feu de Signalisation"
        verbose_name_plural = "Feux de Signalisation"
        ordering = ['zone_trafic', 'nom']
    
    def __str__(self):
        return f"{self.nom} ({self.code_feu}) - {self.carrefour}"


class EvenementTrafic(models.Model):
    """Événements affectant le trafic"""
    
    TYPES_EVENEMENT = [
        ('accident', 'Accident'),
        ('travaux', 'Travaux'),
        ('manifestation', 'Manifestation'),
        ('evenement_sportif', 'Événement Sportif'),
        ('evenement_culturel', 'Événement Culturel'),
        ('conditions_meteo', 'Conditions Météorologiques'),
        ('panne_infrastructure', 'Panne d\'Infrastructure'),
        ('fermeture_voie', 'Fermeture de Voie'),
        ('deviation', 'Déviation'),
        ('autre', 'Autre'),
    ]
    
    NIVEAUX_IMPACT = [
        ('faible', 'Impact Faible'),
        ('modere', 'Impact Modéré'),
        ('important', 'Impact Important'),
        ('majeur', 'Impact Majeur'),
    ]
    
    STATUTS_EVENEMENT = [
        ('prevu', 'Prévu'),
        ('en_cours', 'En Cours'),
        ('termine', 'Terminé'),
        ('annule', 'Annulé'),
    ]
    
    # Événement
    titre = models.CharField(max_length=200)
    type_evenement = models.CharField(max_length=50, choices=TYPES_EVENEMENT)
    description = models.TextField()
    
    # Localisation et impact
    zones_affectees = models.ManyToManyField(ZoneTrafic)
    niveau_impact = models.CharField(max_length=20, choices=NIVEAUX_IMPACT)
    rayon_impact = models.FloatField(help_text="Rayon d'impact en kilomètres", null=True, blank=True)
    
    # Temporal
    date_debut = models.DateTimeField()
    date_fin_prevue = models.DateTimeField()
    date_fin_reelle = models.DateTimeField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUTS_EVENEMENT, default='prevu')
    
    # Mesures d'accompagnement
    deviations_proposees = models.TextField(blank=True)
    transports_alternatifs = models.TextField(blank=True)
    recommandations = models.TextField(blank=True)
    
    # Communication
    communique_presse = models.TextField(blank=True)
    canaux_diffusion = models.JSONField(default=list, blank=True)
    
    # Suivi
    responsable = models.CharField(max_length=100, blank=True)
    services_impliques = models.JSONField(default=list, blank=True)
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True)
    derniere_mise_a_jour = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Événement de Trafic"
        verbose_name_plural = "Événements de Trafic"
        ordering = ['-date_debut']
    
    def __str__(self):
        return f"{self.titre} ({self.get_type_evenement_display()}) - {self.date_debut.strftime('%d/%m/%Y')}"