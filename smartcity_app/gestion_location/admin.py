"""
Configuration de l'interface d'administration Django pour la Gestion de Location
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import (
    TypeLocation,
    VehiculeLocation,
    Location,
    OptionLocation,
    ServiceLocation,
    HistoriqueLocation,
    AlerteLocation
)


@admin.register(TypeLocation)
class TypeLocationAdmin(admin.ModelAdmin):
    """Administration des types de véhicules"""
    
    list_display = [
        'nom', 'categorie', 'prix_heure', 'prix_jour', 
        'capacite_passagers', 'nombre_total', 'disponible'
    ]
    list_filter = ['categorie', 'disponible', 'accessible_pmr']
    search_fields = ['nom', 'description']
    ordering = ['categorie', 'nom']
    
    fieldsets = (
        ('Informations Générales', {
            'fields': ('nom', 'categorie', 'description', 'icone', 'couleur')
        }),
        ('Caractéristiques Techniques', {
            'fields': ('capacite_passagers', 'capacite_bagages', 'vitesse_maximale', 'autonomie_km')
        }),
        ('Tarification', {
            'fields': ('prix_heure', 'prix_jour', 'prix_km', 'caution_requise')
        }),
        ('Accessibilité et Équipements', {
            'fields': ('accessible_pmr', 'permis_requis', 'age_minimum', 'equipements')
        }),
        ('Impact Environnemental', {
            'fields': ('emission_co2_par_km', 'consommation_moyenne')
        }),
        ('Disponibilité', {
            'fields': ('disponible', 'nombre_total')
        }),
    )


@admin.register(VehiculeLocation)
class VehiculeLocationAdmin(admin.ModelAdmin):
    """Administration des véhicules"""
    
    list_display = [
        'numero_identification', 'type_location', 'statut', 
        'station_location', 'niveau_carburant', 'kilometrage_total'
    ]
    list_filter = ['statut', 'type_location__categorie', 'annee_fabrication']
    search_fields = ['numero_identification', 'immatriculation', 'station_location']
    ordering = ['type_location', 'numero_identification']
    
    fieldsets = (
        ('Identification', {
            'fields': ('type_location', 'numero_identification', 'immatriculation')
        }),
        ('Localisation', {
            'fields': ('station_location', 'latitude', 'longitude', 'adresse_complete')
        }),
        ('État du Véhicule', {
            'fields': ('statut', 'niveau_carburant', 'kilometrage_total')
        }),
        ('Informations Techniques', {
            'fields': ('annee_fabrication', 'couleur', 'numero_serie')
        }),
        ('Maintenance', {
            'fields': ('derniere_maintenance', 'prochaine_maintenance', 'probleme_signale')
        }),
        ('Assurance et Documents', {
            'fields': ('numero_assurance', 'date_expiration_assurance', 'controle_technique')
        }),
    )


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    """Administration des locations"""

    def has_add_permission(self, request):
        return False
    
    list_display = [
        'numero_location', 'utilisateur', 'vehicule', 
        'statut', 'date_debut', 'prix_total_calcule'
    ]
    list_filter = ['statut', 'type_location', 'date_debut', 'assurance_comprise']
    search_fields = ['numero_location', 'utilisateur__username', 'conducteur_principal']
    ordering = ['-date_creation']
    readonly_fields = ['numero_location', 'date_creation', 'derniere_mise_a_jour']
    
    fieldsets = (
        ('Informations Générales', {
            'fields': ('numero_location', 'utilisateur', 'vehicule', 'type_location', 'statut')
        }),
        ('Dates et Lieux', {
            'fields': ('date_debut', 'date_fin', 'date_debut_reelle', 'date_fin_reelle', 
                      'lieu_prise', 'lieu_retour', 'latitude_prise', 'longitude_prise',
                      'latitude_retour', 'longitude_retour')
        }),
        ('Informations Conducteur', {
            'fields': ('conducteur_principal', 'conducteur_secondaire', 'numero_permis', 'date_naissance')
        }),
        ('Tarification', {
            'fields': ('prix_heure', 'prix_total_calcule', 'prix_total_final', 
                      'caution_payee', 'caution_rendue')
        }),
        ('Kilométrage', {
            'fields': ('kilometrage_depart', 'kilometrage_retour', 'kilometrage_total')
        }),
        ('État du Véhicule', {
            'fields': ('etat_depart', 'etat_retour', 'dommages_signales')
        }),
        ('Options et Services', {
            'fields': ('options_choisies', 'services_additionnels')
        }),
        ('Assurance', {
            'fields': ('assurance_comprise', 'franchise_assurance', 'assurance_supplementaire')
        }),
        ('Commentaires et Évaluation', {
            'fields': ('commentaires_client', 'note_experience', 'commentaires_admin')
        }),
        ('Récurrence', {
            'fields': ('est_recurrente', 'frequence_recurrence', 'date_fin_recurrence')
        }),
        ('Métadonnées', {
            'fields': ('date_creation', 'derniere_mise_a_jour', 'cree_par_admin')
        }),
    )


@admin.register(OptionLocation)
class OptionLocationAdmin(admin.ModelAdmin):
    """Administration des options"""
    
    list_display = ['nom', 'categorie', 'prix_unitaire', 'unite_tarification', 'disponible']
    list_filter = ['categorie', 'disponible', 'unite_tarification']
    search_fields = ['nom', 'description']
    ordering = ['categorie', 'nom']


@admin.register(ServiceLocation)
class ServiceLocationAdmin(admin.ModelAdmin):
    """Administration des services"""
    
    list_display = ['nom', 'prix_fixe', 'prix_variable', 'disponible']
    list_filter = ['disponible']
    search_fields = ['nom', 'description']
    ordering = ['nom']


@admin.register(HistoriqueLocation)
class HistoriqueLocationAdmin(admin.ModelAdmin):
    """Administration de l'historique"""
    
    list_display = ['location', 'satisfaction_client', 'probleme_rencontre', 'date_creation']
    list_filter = ['probleme_rencontre', 'date_creation']
    search_fields = ['location__numero_location']
    ordering = ['-date_creation']


@admin.register(AlerteLocation)
class AlerteLocationAdmin(admin.ModelAdmin):
    """Administration des alertes"""
    
    list_display = [
        'titre', 'type_alerte', 'niveau_priorite', 
        'active', 'traitee', 'date_creation'
    ]
    list_filter = ['type_alerte', 'niveau_priorite', 'active', 'traitee']
    search_fields = ['titre', 'description']
    ordering = ['-niveau_priorite', '-date_creation']
    
    fieldsets = (
        ('Informations Générales', {
            'fields': ('type_alerte', 'niveau_priorite', 'titre', 'description')
        }),
        ('Liens', {
            'fields': ('location', 'vehicule')
        }),
        ('Gestion', {
            'fields': ('active', 'traitee', 'traitee_par', 'date_traitement')
        }),
        ('Métadonnées', {
            'fields': ('date_creation', 'date_echeance')
        }),
    )


# Configuration de l'interface admin
admin.site.site_header = "Administration SmartCity - Location"
admin.site.site_title = "SmartCity Location Admin"
admin.site.index_title = "Gestion de Location"
