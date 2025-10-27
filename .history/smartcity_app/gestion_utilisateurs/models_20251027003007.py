"""
Gestion des Utilisateurs - SmartCity
Domaine de gestion : 👥 Utilisateurs

Ce module gère :
- Profils utilisateurs et authentification avec rôles
- Préférences de mobilité des utilisateurs
- Historique des trajets utilisateurs
- Système de recommandations personnalisées
- Gestion des rôles : Utilisateur normal et Administrateur
"""

from django.db import models
from django.contrib.auth.models import User, Group, Permission
from django.db.models.signals import post_save
from django.dispatch import receiver


class RoleUtilisateur(models.Model):
    """Rôles disponibles dans le système SmartCity"""
    
    TYPES_ROLE = [
        ('admin', 'Administrateur'),
    ]
    
    nom = models.CharField(max_length=50, unique=True)
    type_role = models.CharField(max_length=20, choices=TYPES_ROLE, unique=True)
    description = models.TextField()
    permissions_specifiques = models.JSONField(default=list, blank=True)
    # Accès aux fonctionnalités
    peut_voir_dashboard = models.BooleanField(default=False)
    peut_voir_ontologie = models.BooleanField(default=False)
    peut_gerer_utilisateurs = models.BooleanField(default=False)
    peut_modifier_systeme = models.BooleanField(default=False)
    peut_voir_stats_globales = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Rôle Utilisateur"
        verbose_name_plural = "Rôles Utilisateur"
    
    def __str__(self):
        return self.nom
    
    @property
    def est_admin(self):
        """Vérifie si le rôle est administrateur"""
        return self.type_role == 'admin'


class ProfilUtilisateur(models.Model):
    """Profil étendu pour les utilisateurs du système SmartCity"""
    
    MODES_TRANSPORT_PREFERENCES = [
        ('metro', 'Métro'),
        ('bus', 'Bus'),
        ('tramway', 'Tramway'),
        ('velo', 'Vélo'),
        ('marche', 'Marche'),
        ('voiture', 'Voiture'),
        ('covoiturage', 'Covoiturage'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.ForeignKey(RoleUtilisateur, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Informations personnelles
    date_naissance = models.DateField(null=True, blank=True)
    telephone = models.CharField(max_length=15, blank=True)
    adresse = models.TextField(blank=True)
    photo_profil = models.ImageField(upload_to='profils/', blank=True, null=True)
    
    # Préférences de mobilité
    modes_transport_preferes = models.JSONField(default=list, blank=True)
    budget_transport_mensuel = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    temps_trajet_max_acceptable = models.IntegerField(help_text="En minutes", null=True, blank=True)
    
    # Paramètres d'accessibilité
    necessite_accessibilite = models.BooleanField(default=False)
    type_handicap = models.CharField(max_length=100, blank=True)
    
    # Préférences environnementales
    preference_eco_friendly = models.BooleanField(default=False)
    accepte_modes_alternatifs = models.BooleanField(default=True)
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True)
    derniere_mise_a_jour = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Profil Utilisateur"
        verbose_name_plural = "Profils Utilisateurs"
    
    def __str__(self):
        return f"Profil de {self.user.get_full_name() or self.user.username} ({self.role.nom})"
    
    @property
    def est_administrateur(self):
        """Vérifie si l'utilisateur est administrateur"""
        return self.role and self.role.type_role == 'admin'
    
    @property
    def peut_acceder_dashboard(self):
        """Vérifie si l'utilisateur peut accéder au dashboard"""
        return self.role and self.role.peut_voir_dashboard
    
    @property
    def peut_acceder_ontologie(self):
        """Vérifie si l'utilisateur peut accéder à l'ontologie"""
        return self.role and self.role.peut_voir_ontologie
    
    def a_permission(self, permission):
        """Vérifie si l'utilisateur a une permission spécifique"""
        if self.est_administrateur:
            return True  # Admin a toutes les permissions
        return permission in self.role.permissions_specifiques


class PreferenceLocalisation(models.Model):
    """Lieux favoris des utilisateurs"""
    
    TYPE_LIEU = [
        ('domicile', 'Domicile'),
        ('travail', 'Travail'),
        ('ecole', 'École'),
        ('loisirs', 'Loisirs'),
        ('courses', 'Courses'),
        ('sante', 'Santé'),
        ('autre', 'Autre'),
    ]
    
    profil = models.ForeignKey(ProfilUtilisateur, on_delete=models.CASCADE, related_name='lieux_favoris')
    nom_lieu = models.CharField(max_length=200)
    type_lieu = models.CharField(max_length=20, choices=TYPE_LIEU)
    adresse = models.TextField()
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    frequence_visite = models.IntegerField(default=1, help_text="Nombre de visites par semaine")
    
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Lieu Favori"
        verbose_name_plural = "Lieux Favoris"
    
    def __str__(self):
        return f"{self.nom_lieu} ({self.get_type_lieu_display()}) - {self.profil.user.username}"


class HistoriqueActivite(models.Model):
    """Historique des activités utilisateur dans le système"""
    
    TYPE_ACTIVITE = [
        ('recherche_trajet', 'Recherche de trajet'),
        ('planification_trajet', 'Planification de trajet'),
        ('evaluation_trajet', 'Évaluation de trajet'),
        ('modification_profil', 'Modification du profil'),
        ('consultation_info', 'Consultation d\'informations'),
        ('signalement', 'Signalement'),
    ]
    
    profil = models.ForeignKey(ProfilUtilisateur, on_delete=models.CASCADE, related_name='historique')
    type_activite = models.CharField(max_length=50, choices=TYPE_ACTIVITE)
    description = models.TextField()
    donnees_contexte = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Activité Utilisateur"
        verbose_name_plural = "Activités Utilisateur"
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.get_type_activite_display()} - {self.profil.user.username} ({self.timestamp.strftime('%d/%m/%Y %H:%M')})"


# Signaux pour la gestion automatique des rôles et profils

@receiver(post_save, sender=User)
def creer_profil_utilisateur(sender, instance, created, **kwargs):
    """Crée automatiquement un profil utilisateur lors de la création d'un User"""
    if created:
        # Récupérer ou créer le rôle utilisateur normal par défaut
        role_user, created = RoleUtilisateur.objects.get_or_create(
            type_role='user',
            defaults={
                'nom': 'Utilisateur Normal',
                'description': 'Utilisateur standard avec accès aux fonctionnalités de base',
                'peut_voir_dashboard': False,
                'peut_voir_ontologie': False,
                'peut_gerer_utilisateurs': False,
                'peut_modifier_systeme': False,
                'peut_voir_stats_globales': False,
                'permissions_specifiques': ['consulter_trajets', 'planifier_trajet', 'modifier_profil']
            }
        )
        
        # Si c'est le premier utilisateur ou un superuser, le faire admin
        if instance.is_superuser or User.objects.count() == 1:
            role_admin, created = RoleUtilisateur.objects.get_or_create(
                type_role='admin',
                defaults={
                    'nom': 'Administrateur',
                    'description': 'Administrateur avec accès complet au système',
                    'peut_voir_dashboard': True,
                    'peut_voir_ontologie': True,
                    'peut_gerer_utilisateurs': True,
                    'peut_modifier_systeme': True,
                    'peut_voir_stats_globales': True,
                    'permissions_specifiques': ['all']
                }
            )
            role = role_admin
        else:
            role = role_user
        
        ProfilUtilisateur.objects.create(user=instance, role=role)

@receiver(post_save, sender=ProfilUtilisateur)
def enregistrer_creation_profil(sender, instance, created, **kwargs):
    """Enregistre la création d'un profil dans l'historique"""
    if created:
        HistoriqueActivite.objects.create(
            profil=instance,
            type_activite='modification_profil',
            description='Création du profil utilisateur',
            donnees_contexte={'action': 'creation_profil', 'role': instance.role.nom}
        )