"""
Gestion des Trajets - SmartCity
Domaine de gestion : 🛣️ Trajets & Planification Intelligente

Ce module gère :
- Planification et optimisation des itinéraires intelligents
- Calcul multimodal des trajets avec IA
- Recommandations personnalisées en temps réel
- Historique et préférences de trajets
- Alertes et notifications de transport
- Système de transport urbain intelligent
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
import json


class CritereTrajet(models.Model):
    """Critères d'optimisation pour les trajets"""
    
    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    poids_default = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text="Poids par défaut dans l'algorithme d'optimisation"
    )
    unite_mesure = models.CharField(max_length=50, help_text="Unité de mesure (minutes, km, €, etc.)")
    
    # Configuration
    est_actif = models.BooleanField(default=True)
    ordre_affichage = models.IntegerField(default=1)
    
    class Meta:
        verbose_name = "Critère de Trajet"
        verbose_name_plural = "Critères de Trajet"
        ordering = ['ordre_affichage', 'nom']
    
    def __str__(self):
        return self.nom


class ModeTransport(models.Model):
    """Modes de transport disponibles pour les trajets"""
    
    CATEGORIES_MODE = [
        ('transport_public', 'Transport Public'),
        ('transport_actif', 'Transport Actif'),
        ('transport_prive', 'Transport Privé'),
        ('transport_partage', 'Transport Partagé'),
        ('transport_innovant', 'Transport Innovant'),
    ]
    
    # Informations de base
    nom = models.CharField(max_length=100)
    categorie = models.CharField(max_length=50, choices=CATEGORIES_MODE)
    icone = models.CharField(max_length=50, help_text="Classe CSS pour l'icône")
    couleur = models.CharField(max_length=7, default='#007bff')
    
    # Caractéristiques techniques
    vitesse_moyenne = models.FloatField(help_text="Vitesse moyenne en km/h")
    vitesse_maximale = models.FloatField(null=True, blank=True, help_text="Vitesse maximale en km/h")
    rayon_action = models.FloatField(help_text="Rayon d'action moyen en km")
    
    # Coûts
    cout_fixe = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Coût fixe par trajet")
    cout_par_km = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Coût par kilomètre")
    cout_par_minute = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Coût par minute")
    
    # Impact environnemental
    emission_co2_par_km = models.FloatField(default=0, help_text="Émissions CO2 en g/km")
    impact_environnemental = models.IntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Impact environnemental (1=très faible, 10=très élevé)"
    )
    
    # Accessibilité
    accessible_pmr = models.BooleanField(default=False)
    age_minimum = models.IntegerField(default=0, help_text="Âge minimum pour utiliser ce mode")
    permis_requis = models.BooleanField(default=False)
    
    # Disponibilité
    disponible_24h = models.BooleanField(default=False)
    conditions_meteo = models.JSONField(default=list, help_text="Conditions météo supportées")
    
    # Métadonnées
    description = models.TextField(blank=True)
    est_actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Mode de Transport"
        verbose_name_plural = "Modes de Transport"
        ordering = ['categorie', 'nom']
    
    def __str__(self):
        return f"{self.nom} ({self.get_categorie_display()})"


class Trajet(models.Model):
    """Trajet planifié ou réalisé"""
    
    STATUTS_TRAJET = [
        ('planifie', 'Planifié'),
        ('en_cours', 'En Cours'),
        ('termine', 'Terminé'),
        ('annule', 'Annulé'),
        ('reporte', 'Reporté'),
    ]
    
    TYPES_TRAJET = [
        ('domicile_travail', 'Domicile-Travail'),
        ('travail_domicile', 'Travail-Domicile'),
        ('loisirs', 'Loisirs'),
        ('courses', 'Courses'),
        ('sante', 'Santé'),
        ('education', 'Éducation'),
        ('professionnel', 'Professionnel'),
        ('autre', 'Autre'),
    ]
    
    # Utilisateur (optionnel pour trajets anonymes)
    utilisateur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='trajets')
    
    # Informations de base
    nom_trajet = models.CharField(max_length=200, blank=True)
    type_trajet = models.CharField(max_length=50, choices=TYPES_TRAJET, default='autre')
    statut = models.CharField(max_length=20, choices=STATUTS_TRAJET, default='planifie')
    
    # Points de départ et d'arrivée
    lieu_depart = models.CharField(max_length=200)
    latitude_depart = models.FloatField()
    longitude_depart = models.FloatField()
    
    lieu_arrivee = models.CharField(max_length=200)
    latitude_arrivee = models.FloatField()
    longitude_arrivee = models.FloatField()
    
    # Points intermédiaires (optionnels)
    points_intermediaires = models.JSONField(default=list, blank=True)
    
    # Temporel
    date_heure_depart_souhaitee = models.DateTimeField()
    date_heure_arrivee_souhaitee = models.DateTimeField(null=True, blank=True)
    date_heure_depart_reelle = models.DateTimeField(null=True, blank=True)
    date_heure_arrivee_reelle = models.DateTimeField(null=True, blank=True)
    
    # Préférences utilisateur
    criteres_optimisation = models.ManyToManyField(CritereTrajet, through='PreferencesCritere')
    modes_transport_acceptes = models.ManyToManyField(ModeTransport, blank=True)
    modes_transport_refuses = models.ManyToManyField(ModeTransport, blank=True, related_name='trajets_refuses')
    
    # Contraintes
    budget_maximum = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    duree_maximale = models.IntegerField(null=True, blank=True, help_text="Durée maximale en minutes")
    nombre_correspondances_max = models.IntegerField(default=3)
    distance_marche_max = models.FloatField(default=1.0, help_text="Distance de marche maximale en km")
    
    # Accessibilité
    necessite_accessibilite = models.BooleanField(default=False)
    accompagne_enfants = models.BooleanField(default=False)
    bagages_lourds = models.BooleanField(default=False)
    
    # Récurrence
    est_recurrent = models.BooleanField(default=False)
    frequence_recurrence = models.CharField(max_length=50, blank=True)
    jours_semaine = models.JSONField(default=list, blank=True)
    date_fin_recurrence = models.DateField(null=True, blank=True)
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True)
    derniere_mise_a_jour = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Trajet"
        verbose_name_plural = "Trajets"
        ordering = ['-date_heure_depart_souhaitee']
        indexes = [
            models.Index(fields=['utilisateur', 'statut']),
            models.Index(fields=['date_heure_depart_souhaitee']),
            models.Index(fields=['type_trajet']),
        ]
    
    def __str__(self):
        if self.nom_trajet:
            return self.nom_trajet
        return f"{self.lieu_depart} → {self.lieu_arrivee} ({self.date_heure_depart_souhaitee.strftime('%d/%m/%Y %H:%M')})"
    
    @property
    def duree_planifiee(self):
        """Calcule la durée planifiée du trajet"""
        if self.date_heure_arrivee_souhaitee:
            delta = self.date_heure_arrivee_souhaitee - self.date_heure_depart_souhaitee
            return delta.total_seconds() / 60  # en minutes
        return None
    
    @property
    def duree_reelle(self):
        """Calcule la durée réelle du trajet"""
        if self.date_heure_depart_reelle and self.date_heure_arrivee_reelle:
            delta = self.date_heure_arrivee_reelle - self.date_heure_depart_reelle
            return delta.total_seconds() / 60  # en minutes
        return None


class PreferencesCritere(models.Model):
    """Table de liaison avec poids personnalisés pour les critères"""
    
    trajet = models.ForeignKey(Trajet, on_delete=models.CASCADE)
    critere = models.ForeignKey(CritereTrajet, on_delete=models.CASCADE)
    poids = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text="Importance de ce critère pour ce trajet"
    )
    
    class Meta:
        unique_together = ['trajet', 'critere']
        verbose_name = "Préférence de Critère"
        verbose_name_plural = "Préférences de Critères"


class ItinerairePropose(models.Model):
    """Itinéraires proposés pour un trajet"""
    
    ALGORITHMES_CALCUL = [
        ('plus_court', 'Plus Court'),
        ('plus_rapide', 'Plus Rapide'),
        ('moins_cher', 'Moins Cher'),
        ('eco_friendly', 'Écologique'),
        ('multimodal', 'Multimodal Optimisé'),
        ('personnalise', 'Personnalisé'),
    ]
    
    # Relation avec le trajet
    trajet = models.ForeignKey(Trajet, on_delete=models.CASCADE, related_name='itineraires_proposes')
    
    # Caractéristiques de l'itinéraire
    nom_itineraire = models.CharField(max_length=200, blank=True)
    algorithme_utilise = models.CharField(max_length=50, choices=ALGORITHMES_CALCUL)
    rang_proposition = models.IntegerField(default=1, help_text="Ordre de proposition (1 = meilleur)")
    
    # Métriques principales
    distance_totale = models.FloatField(help_text="Distance totale en km")
    duree_estimee = models.IntegerField(help_text="Durée estimée en minutes")
    cout_total = models.DecimalField(max_digits=10, decimal_places=2, help_text="Coût total estimé")
    emission_co2_totale = models.FloatField(help_text="Émissions CO2 totales en g")
    
    # Détails par segment
    segments = models.JSONField(help_text="Détails des segments de l'itinéraire")
    
    # Modes utilisés
    modes_transport = models.ManyToManyField(ModeTransport, through='UtilisationModeItineraire')
    
    # Évaluation
    score_optimisation = models.FloatField(help_text="Score d'optimisation global")
    avantages = models.JSONField(default=list, blank=True)
    inconvenients = models.JSONField(default=list, blank=True)
    
    # Conditions de validité
    valide_jusqu_a = models.DateTimeField()
    conditions_trafic = models.CharField(max_length=100, blank=True)
    conditions_meteo = models.CharField(max_length=100, blank=True)
    
    # Sélection utilisateur
    selectionne_par_utilisateur = models.BooleanField(default=False)
    date_selection = models.DateTimeField(null=True, blank=True)
    
    # Métadonnées
    date_calcul = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Itinéraire Proposé"
        verbose_name_plural = "Itinéraires Proposés"
        ordering = ['trajet', 'rang_proposition']
    
    def __str__(self):
        return f"Itinéraire #{self.rang_proposition} - {self.trajet} ({self.get_algorithme_utilise_display()})"


class UtilisationModeItineraire(models.Model):
    """Utilisation des modes de transport dans un itinéraire"""
    
    itineraire = models.ForeignKey(ItinerairePropose, on_delete=models.CASCADE)
    mode_transport = models.ForeignKey(ModeTransport, on_delete=models.CASCADE)
    
    # Métriques pour ce mode
    distance = models.FloatField(help_text="Distance parcourue avec ce mode en km")
    duree = models.IntegerField(help_text="Durée d'utilisation en minutes")
    cout = models.DecimalField(max_digits=10, decimal_places=2, help_text="Coût pour ce mode")
    
    # Ordre dans l'itinéraire
    ordre_utilisation = models.IntegerField(help_text="Ordre d'utilisation dans l'itinéraire")
    
    # Détails spécifiques
    informations_complementaires = models.JSONField(default=dict, blank=True)
    
    class Meta:
        unique_together = ['itineraire', 'mode_transport', 'ordre_utilisation']
        ordering = ['ordre_utilisation']
        verbose_name = "Utilisation de Mode"
        verbose_name_plural = "Utilisations de Modes"


class EvaluationTrajet(models.Model):
    """Évaluation des trajets réalisés par les utilisateurs"""
    
    trajet = models.OneToOneField(Trajet, on_delete=models.CASCADE, related_name='evaluation')
    itineraire_utilise = models.ForeignKey(ItinerairePropose, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Notes par critère
    note_duree = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)
    note_cout = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)
    note_confort = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)
    note_ponctualite = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)
    note_facilite = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)
    
    # Note globale
    note_globale = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    
    # Commentaires
    points_positifs = models.TextField(blank=True)
    points_negatifs = models.TextField(blank=True)
    suggestions_amelioration = models.TextField(blank=True)
    
    # Questions spécifiques
    recommanderait = models.BooleanField(null=True)
    reutiliserait_itineraire = models.BooleanField(null=True)
    
    # Incidents rencontrés
    incidents_rencontres = models.JSONField(default=list, blank=True)
    
    # Métadonnées
    date_evaluation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Évaluation de Trajet"
        verbose_name_plural = "Évaluations de Trajets"
    
    def __str__(self):
        return f"Évaluation {self.note_globale}/5 - {self.trajet}"
    
    @property
    def note_moyenne(self):
        """Calcule la note moyenne des critères évalués"""
        notes = [n for n in [self.note_duree, self.note_cout, self.note_confort, 
                           self.note_ponctualite, self.note_facilite] if n is not None]
        return sum(notes) / len(notes) if notes else None


# ========== MODÈLES POUR PLANIFICATION INTELLIGENTE ==========

class TypeVehiculeIntelligent(models.Model):
    """Types de véhicules disponibles dans la ville avec intelligence"""
    CATEGORIES = [
        ('public', 'Transport Public'),
        ('prive', 'Transport Privé'),
        ('partage', 'Transport Partagé'),
        ('actif', 'Transport Actif'),
    ]
    
    nom = models.CharField(max_length=100, verbose_name="Nom du véhicule")
    categorie = models.CharField(max_length=20, choices=CATEGORIES, verbose_name="Catégorie")
    icone = models.CharField(max_length=50, default="fas fa-car", verbose_name="Icône")
    couleur = models.CharField(max_length=7, default="#007bff", verbose_name="Couleur")
    vitesse_moyenne = models.FloatField(default=30.0, verbose_name="Vitesse moyenne (km/h)")
    cout_par_km = models.FloatField(default=0.0, verbose_name="Coût par km (€)")
    empreinte_carbone = models.FloatField(default=0.0, verbose_name="CO2 par km (g)")
    disponible = models.BooleanField(default=True, verbose_name="Disponible")
    capacite_passagers = models.IntegerField(default=1, verbose_name="Capacité passagers")
    accessible_pmr = models.BooleanField(default=False, verbose_name="Accessible PMR")
    
    # Intelligence temps réel
    frequence_passage = models.IntegerField(null=True, blank=True, verbose_name="Fréquence passage (minutes)")
    horaires_service = models.JSONField(default=dict, blank=True, verbose_name="Horaires de service")
    
    class Meta:
        verbose_name = "Type de Véhicule Intelligent"
        verbose_name_plural = "Types de Véhicules Intelligents"
        ordering = ['categorie', 'nom']
    
    def __str__(self):
        return f"{self.nom} ({self.get_categorie_display()})"

class DemandeTrajetIntelligent(models.Model):
    """Demande de planification de trajet intelligente par un utilisateur"""
    PRIORITES = [
        ('rapidite', 'Le plus rapide'),
        ('economique', 'Le moins cher'),
        ('ecologique', 'Le plus écologique'),
        ('confort', 'Le plus confortable'),
        ('moins_circulation', 'Éviter la circulation'),
    ]
    
    STATUTS = [
        ('en_attente', 'En attente'),
        ('en_cours', 'Calcul en cours'),
        ('complete', 'Complétée'),
        ('erreur', 'Erreur'),
    ]
    
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Utilisateur")
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    
    # Origine et destination
    lieu_depart = models.CharField(max_length=300, verbose_name="Lieu de départ")
    lieu_depart_lat = models.FloatField(null=True, blank=True, verbose_name="Latitude départ")
    lieu_depart_lng = models.FloatField(null=True, blank=True, verbose_name="Longitude départ")
    
    lieu_arrivee = models.CharField(max_length=300, verbose_name="Lieu d'arrivée")
    lieu_arrivee_lat = models.FloatField(null=True, blank=True, verbose_name="Latitude arrivée")
    lieu_arrivee_lng = models.FloatField(null=True, blank=True, verbose_name="Longitude arrivée")
    
    # Préférences utilisateur
    vehicules_preferes = models.ManyToManyField(TypeVehiculeIntelligent, blank=True, verbose_name="Véhicules préférés")
    priorite = models.CharField(max_length=20, choices=PRIORITES, default='rapidite', verbose_name="Priorité")
    heure_depart_souhaitee = models.DateTimeField(null=True, blank=True, verbose_name="Heure de départ souhaitée")
    heure_arrivee_souhaitee = models.DateTimeField(null=True, blank=True, verbose_name="Heure d'arrivée souhaitée")
    
    # Contraintes
    budget_maximum = models.FloatField(null=True, blank=True, verbose_name="Budget maximum (€)")
    duree_maximum = models.IntegerField(null=True, blank=True, verbose_name="Durée maximum (minutes)")
    accessible_pmr = models.BooleanField(default=False, verbose_name="Accessible PMR")
    eviter_circulation = models.BooleanField(default=False, verbose_name="Éviter la circulation")
    
    # Statut et résultats
    statut = models.CharField(max_length=20, choices=STATUTS, default='en_attente', verbose_name="Statut")
    resultats_json = models.JSONField(default=dict, blank=True, verbose_name="Résultats calculés")
    score_satisfaction = models.FloatField(null=True, blank=True, verbose_name="Score de satisfaction")
    
    class Meta:
        verbose_name = "Demande de Trajet Intelligent"
        verbose_name_plural = "Demandes de Trajets Intelligents"
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"Trajet IA de {self.utilisateur.username}: {self.lieu_depart} → {self.lieu_arrivee}"

class TrajetRecommande(models.Model):
    """Trajet recommandé par l'IA avec détails temps réel"""
    demande = models.ForeignKey(DemandeTrajetIntelligent, on_delete=models.CASCADE, related_name='trajets_ia', verbose_name="Demande")
    rang = models.IntegerField(verbose_name="Classement")
    
    # Détails du trajet
    vehicules_utilises = models.ManyToManyField(TypeVehiculeIntelligent, verbose_name="Véhicules utilisés")
    etapes_json = models.JSONField(default=list, verbose_name="Étapes détaillées du trajet")
    
    # Métriques principales
    duree_minutes = models.IntegerField(verbose_name="Durée (minutes)")
    distance_km = models.FloatField(verbose_name="Distance (km)")
    cout_total = models.FloatField(verbose_name="Coût total (€)")
    empreinte_carbone_g = models.FloatField(verbose_name="Empreinte carbone (g CO2)")
    score_confort = models.IntegerField(default=5, verbose_name="Score confort (1-10)")
    
    # Analyse circulation et temps réel
    niveau_circulation = models.CharField(
        max_length=20, 
        default='moyen',
        choices=[('faible', 'Faible'), ('moyen', 'Moyen'), ('fort', 'Fort')],
        verbose_name="Niveau de circulation"
    )
    retard_estime = models.IntegerField(default=0, verbose_name="Retard estimé (minutes)")
    fiabilite_score = models.FloatField(default=8.0, verbose_name="Score de fiabilité (1-10)")
    
    # Informations temps réel
    alertes_trafic = models.JSONField(default=list, verbose_name="Alertes trafic")
    horaires_transport = models.JSONField(default=dict, verbose_name="Horaires transport public")
    conditions_meteo = models.JSONField(default=dict, verbose_name="Conditions météo")
    
    # IA et apprentissage
    score_ia = models.FloatField(verbose_name="Score calculé par l'IA")
    facteurs_decision = models.JSONField(default=list, verbose_name="Facteurs de décision IA")
    
    class Meta:
        verbose_name = "Trajet Recommandé IA"
        verbose_name_plural = "Trajets Recommandés IA"
        ordering = ['demande', 'rang']
    
    def __str__(self):
        vehicules = ", ".join([v.nom for v in self.vehicules_utilises.all()[:2]])
        return f"#{self.rang} - {vehicules} ({self.duree_minutes}min, {self.cout_total}€)"

class AlerteTransportTempsReel(models.Model):
    """Alertes en temps réel sur les transports"""
    TYPES_ALERTE = [
        ('retard', 'Retard'),
        ('annulation', 'Annulation'),
        ('perturbation', 'Perturbation'),
        ('maintenance', 'Maintenance'),
        ('incident', 'Incident'),
        ('circulation', 'Circulation dense'),
        ('meteo', 'Conditions météo'),
        ('info', 'Information'),
    ]
    
    SEVERITES = [
        ('info', 'Information'),
        ('attention', 'Attention'),
        ('important', 'Important'),
        ('critique', 'Critique'),
    ]
    
    type_alerte = models.CharField(max_length=20, choices=TYPES_ALERTE, verbose_name="Type d'alerte")
    severite = models.CharField(max_length=15, choices=SEVERITES, default='info', verbose_name="Sévérité")
    
    titre = models.CharField(max_length=200, verbose_name="Titre")
    description = models.TextField(verbose_name="Description")
    
    # Localisation
    vehicule_concerne = models.ForeignKey(TypeVehiculeIntelligent, null=True, blank=True, on_delete=models.CASCADE, verbose_name="Véhicule concerné")
    ligne_transport = models.CharField(max_length=50, blank=True, verbose_name="Ligne de transport")
    zone_geographique = models.CharField(max_length=200, blank=True, verbose_name="Zone géographique")
    coordonnees_lat = models.FloatField(null=True, blank=True, verbose_name="Latitude")
    coordonnees_lng = models.FloatField(null=True, blank=True, verbose_name="Longitude")
    
    # Temporalité
    date_debut = models.DateTimeField(verbose_name="Date de début")
    date_fin = models.DateTimeField(null=True, blank=True, verbose_name="Date de fin")
    duree_estimee = models.IntegerField(null=True, blank=True, verbose_name="Durée estimée (minutes)")
    
    # Gestion
    active = models.BooleanField(default=True, verbose_name="Active")
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    source = models.CharField(max_length=100, default="System", verbose_name="Source")
    
    class Meta:
        verbose_name = "Alerte Transport Temps Réel"
        verbose_name_plural = "Alertes Transport Temps Réel"
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"{self.get_type_alerte_display()}: {self.titre}"
    
    @property
    def est_active(self):
        """Vérifie si l'alerte est encore active"""
        maintenant = timezone.now()
        if not self.active:
            return False
        if self.date_fin and maintenant > self.date_fin:
            return False
        return maintenant >= self.date_debut

class PreferenceUtilisateurIA(models.Model):
    """Préférences de transport intelligentes de l'utilisateur"""
    utilisateur = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preferences_transport_ia', verbose_name="Utilisateur")
    
    # Véhicules et préférences
    vehicules_favoris = models.ManyToManyField(TypeVehiculeIntelligent, blank=True, verbose_name="Véhicules favoris")
    vehicules_evites = models.ManyToManyField(TypeVehiculeIntelligent, related_name='evites_par', blank=True, verbose_name="Véhicules à éviter")
    
    # Préférences par défaut
    priorite_defaut = models.CharField(max_length=20, choices=DemandeTrajetIntelligent.PRIORITES, default='rapidite', verbose_name="Priorité par défaut")
    budget_defaut = models.FloatField(null=True, blank=True, verbose_name="Budget par défaut (€)")
    duree_max_defaut = models.IntegerField(null=True, blank=True, verbose_name="Durée max par défaut (min)")
    
    # Accessibilité et besoins spéciaux
    necessite_pmr = models.BooleanField(default=False, verbose_name="Nécessite accessibilité PMR")
    tolerance_marche = models.IntegerField(default=10, verbose_name="Tolérance marche (minutes)")
    preference_directe = models.BooleanField(default=False, verbose_name="Préfère trajets directs")
    
    # IA et apprentissage
    apprentissage_actif = models.BooleanField(default=True, verbose_name="Apprentissage automatique actif")
    poids_historique = models.FloatField(default=0.3, verbose_name="Poids de l'historique dans les recommandations")
    
    # Notifications
    recevoir_alertes = models.BooleanField(default=True, verbose_name="Recevoir les alertes")
    avance_notification = models.IntegerField(default=10, verbose_name="Avance notification (minutes)")
    notification_retards = models.BooleanField(default=True, verbose_name="Notifications retards")
    notification_alternatives = models.BooleanField(default=True, verbose_name="Proposer alternatives")
    
    # Lieux favoris avec intelligence
    lieux_favoris = models.JSONField(default=list, verbose_name="Lieux favoris avec coordonnées")
    
    class Meta:
        verbose_name = "Préférence Utilisateur IA"
        verbose_name_plural = "Préférences Utilisateurs IA"
    
    def __str__(self):
        return f"Préférences IA de {self.utilisateur.username}"