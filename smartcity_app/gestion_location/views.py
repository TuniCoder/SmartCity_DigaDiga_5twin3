"""
Vues pour la Gestion de Location - SmartCity
Module : 🚗 Location de Véhicules Intelligente
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db import transaction
import json
import uuid
from datetime import datetime, timedelta

from ..gestion_location.models import (
    TypeLocation,
    VehiculeLocation,
    Location,
    OptionLocation,
    ServiceLocation,
    HistoriqueLocation,
    AlerteLocation
)
from ..ontology_manager.rdf_utils import rdf_manager
from ..gestion_utilisateurs.models import ProfilUtilisateur


# ========== VUES CLIENT (Frontend) ==========

@login_required
def index_location_view(request):
    """Vue d'accueil du module Gestion de Location - Dashboard client"""
    
    # Statistiques des locations de l'utilisateur
    locations_totales = Location.objects.filter(utilisateur=request.user).count()
    locations_actives = Location.objects.filter(
        utilisateur=request.user,
        statut__in=['en_attente', 'confirmee', 'en_cours']
    ).count()
    
    # Dernières locations
    dernieres_locations = Location.objects.filter(
        utilisateur=request.user
    ).order_by('-date_creation')[:5]
    
    # Véhicules disponibles par catégorie
    vehicules_disponibles = VehiculeLocation.objects.filter(statut='disponible')
    types_location = TypeLocation.objects.filter(disponible=True)
    
    # Statistiques par catégorie
    stats_categories = {}
    for type_loc in types_location:
        count = vehicules_disponibles.filter(type_location=type_loc).count()
        if count > 0:
            stats_categories[type_loc.categorie] = {
                'nom': type_loc.get_categorie_display(),
                'count': count,
                'prix_min': float(type_loc.prix_heure),
                'icone': type_loc.icone,
                'couleur': type_loc.couleur
            }
    
    # Alertes personnalisées
    alertes_personnelles = AlerteLocation.objects.filter(
        location__utilisateur=request.user,
        active=True
    ).order_by('-niveau_priorite')[:3]
    
    context = {
        'locations_totales': locations_totales,
        'locations_actives': locations_actives,
        'dernieres_locations': dernieres_locations,
        'stats_categories': stats_categories,
        'alertes_personnelles': alertes_personnelles,
        'page_title': 'Dashboard Location - SmartCity'
    }
    
    return render(request, 'gestion_location/index_location.html', context)


@login_required
def rechercher_vehicules_view(request):
    """Interface de recherche et location de véhicules"""
    
    # Récupérer les filtres de recherche
    categorie = request.GET.get('categorie', '')
    lieu_prise = request.GET.get('lieu_prise', '')
    date_debut = request.GET.get('date_debut', '')
    date_fin = request.GET.get('date_fin', '')
    prix_max = request.GET.get('prix_max', '')
    
    # Véhicules disponibles
    vehicules_query = VehiculeLocation.objects.filter(statut='disponible')
    
    # Appliquer les filtres
    if categorie:
        vehicules_query = vehicules_query.filter(type_location__categorie=categorie)
    
    if prix_max:
        try:
            prix_max_float = float(prix_max)
            vehicules_query = vehicules_query.filter(type_location__prix_heure__lte=prix_max_float)
        except ValueError:
            pass
    
    # Récupérer les types de location pour les filtres
    types_location = TypeLocation.objects.filter(disponible=True).order_by('categorie', 'nom')
    options_location = OptionLocation.objects.filter(disponible=True)
    services_location = ServiceLocation.objects.filter(disponible=True)
    
    # Pagination
    paginator = Paginator(vehicules_query, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_title': 'Rechercher un Véhicule - SmartCity',
        'vehicules': page_obj,
        'types_location': types_location,
        'options_location': options_location,
        'services_location': services_location,
        'filtres': {
            'categorie': categorie,
            'lieu_prise': lieu_prise,
            'date_debut': date_debut,
            'date_fin': date_fin,
            'prix_max': prix_max,
        },
        'categories_choices': TypeLocation.CATEGORIES,
    }
    
    return render(request, 'gestion_location/rechercher_vehicules.html', context)


@login_required
@require_http_methods(["POST"])
def creer_location_view(request):
    """Créer une nouvelle location, 100% basé sur RDF."""
    if hasattr(request.user, 'profilutilisateur') and request.user.profilutilisateur.est_administrateur:
        messages.error(request, "Les administrateurs ne peuvent pas créer de réservations.")
        return redirect('gestion_location:rechercher_vehicules')
    
    try:
        # Récupérer les données du formulaire
        vehicule_id = request.POST.get('vehicule_id')
        date_debut_str = request.POST.get('date_debut')
        date_fin_str = request.POST.get('date_fin')
        lieu_prise = request.POST.get('lieu_prise', '').strip()
        lieu_retour = request.POST.get('lieu_retour', '').strip()
        conducteur_principal = request.POST.get('conducteur_principal', '').strip()
        conducteur_secondaire = request.POST.get('conducteur_secondaire', '').strip()
        numero_permis = request.POST.get('numero_permis', '').strip()
        
        options_choisies = request.POST.getlist('options_choisies')
        services_additionnels = request.POST.getlist('services_additionnels')
        assurance_comprise = request.POST.get('assurance_comprise') == 'on'
        assurance_supplementaire = request.POST.get('assurance_supplementaire') == 'on'
        
        # Validation
        if not all([vehicule_id, date_debut_str, date_fin_str, lieu_prise, lieu_retour, conducteur_principal]):
            messages.error(request, "Tous les champs obligatoires doivent être remplis.")
            return redirect('gestion_location:rechercher_vehicules')
        
        # Parser les dates
        date_debut = timezone.make_aware(datetime.fromisoformat(date_debut_str.replace('T', ' ')))
        date_fin = timezone.make_aware(datetime.fromisoformat(date_fin_str.replace('T', ' ')))
        
        if date_fin <= date_debut or date_debut <= timezone.now():
            messages.error(request, "Les dates de location sont invalides.")
            return redirect('gestion_location:rechercher_vehicules')
        
        # Récupérer le véhicule (dépendance restante sur le modèle VehiculeLocation)
        vehicule = get_object_or_404(VehiculeLocation, id=vehicule_id, statut='disponible')
        
        # TODO: Remplacer cette vérification par une logique RDF
        # Vérifier la disponibilité du véhicule (dépendance restante sur le modèle Location)
        conflits = Location.objects.filter(
            vehicule=vehicule,
            statut__in=['en_attente', 'confirmee', 'en_cours'],
            date_debut__lt=date_fin,
            date_fin__gt=date_debut
        )
        if conflits.exists():
            messages.error(request, "Ce véhicule n'est pas disponible pour les dates sélectionnées.")
            return redirect('gestion_location:rechercher_vehicules')
        
        # Calculer le prix (dépendance restante sur les modèles)
        duree_heures = (date_fin - date_debut).total_seconds() / 3600
        prix_base = float(vehicule.type_location.prix_heure) * duree_heures
        prix_options = sum(float(opt.prix_unitaire) for opt in OptionLocation.objects.filter(id__in=options_choisies))
        prix_services = sum(float(serv.prix_fixe) for serv in ServiceLocation.objects.filter(id__in=services_additionnels))
        prix_total = prix_base + prix_options + prix_services
        
        # Générer un numéro de location unique
        numero_location = f"LOC{datetime.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:8].upper()}"
        
        # Préparer les données pour l'ontologie
        location_rdf_data = {
            'utilisateur_id': str(request.user.id),
            'utilisateur_username': request.user.username,
            'vehicule_id': str(vehicule.id),
            'numero_location': numero_location,
            'type_location': 'ponctuelle',
            'statut': 'en_attente',
            'date_debut': date_debut.isoformat(),
            'date_fin': date_fin.isoformat(),
            'lieu_prise': lieu_prise,
            'lieu_retour': lieu_retour,
            'conducteur_principal': conducteur_principal,
            'conducteur_secondaire': conducteur_secondaire,
            'numero_permis': numero_permis,
            'prix_total_calcule': prix_total,
            'caution_payee': float(vehicule.type_location.caution_requise),
            'options_choisies': json.dumps(options_choisies),
            'services_additionnels': json.dumps(services_additionnels),
            'assurance_comprise': assurance_comprise,
            'franchise_assurance': 500.0 if assurance_supplementaire else 1000.0,
            'assurance_supplementaire': assurance_supplementaire,
            'cree_par_admin': False,
        }
        
        # Sauvegarder uniquement dans RDF
        success, location_uri = rdf_manager.create_location(location_rdf_data)
        
        if success:
            # TODO: La mise à jour du statut du véhicule dépend encore de SQLite.
            # Idéalement, le statut du véhicule devrait aussi être dans l'ontologie.
            vehicule.statut = 'reserve'
            vehicule.save()
            logger.info(f"Location {numero_location} sauvegardée dans RDF. URI: {location_uri}")
            messages.success(request, f"✅ Location créée avec succès ! Numéro: {numero_location}")
            return redirect('gestion_location:mes_locations')
        else:
            logger.error(f"Erreur lors de la sauvegarde RDF pour la location {numero_location}: {location_uri}")
            messages.error(request, f"Erreur lors de la création de la location: {location_uri}")
            return redirect('gestion_location:rechercher_vehicules')
            
    except VehiculeLocation.DoesNotExist:
        messages.error(request, "Le véhicule demandé n'existe pas ou n'est plus disponible.")
        return redirect('gestion_location:rechercher_vehicules')
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la création de la location: {e}")
        messages.error(request, "Une erreur inattendue est survenue.")
        return redirect('gestion_location:rechercher_vehicules')


@login_required
def mes_locations_view(request):
    """Historique des locations de l'utilisateur, 100% basé sur RDF."""
    
    # Récupérer toutes les locations de l'utilisateur depuis RDF
    try:
        all_locations_rdf = rdf_manager.get_locations_by_user(str(request.user.id))
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des locations RDF pour l'utilisateur {request.user.id}: {e}")
        messages.error(request, "Impossible de charger vos locations depuis l'ontologie.")
        all_locations_rdf = []

    # Filtrage en Python sur la liste de dictionnaires
    statut_filtre = request.GET.get('statut')
    type_filtre = request.GET.get('type')
    date_debut_str = request.GET.get('date_debut')
    date_fin_str = request.GET.get('date_fin')

    filtered_locations = all_locations_rdf

    if statut_filtre:
        filtered_locations = [loc for loc in filtered_locations if loc.get('statutLocation') == statut_filtre]
    
    if type_filtre:
        filtered_locations = [loc for loc in filtered_locations if loc.get('typeLocation') == type_filtre]

    if date_debut_str:
        try:
            date_debut_parsed = timezone.datetime.strptime(date_debut_str, '%Y-%m-%d').date()
            filtered_locations = [
                loc for loc in filtered_locations 
                if loc.get('dateDebutLocation') and timezone.datetime.fromisoformat(loc['dateDebutLocation']).date() >= date_debut_parsed
            ]
        except (ValueError, TypeError):
            pass  # Ignorer les dates invalides

    if date_fin_str:
        try:
            date_fin_parsed = timezone.datetime.strptime(date_fin_str, '%Y-%m-%d').date()
            filtered_locations = [
                loc for loc in filtered_locations 
                if loc.get('dateDebutLocation') and timezone.datetime.fromisoformat(loc['dateDebutLocation']).date() <= date_fin_parsed
            ]
        except (ValueError, TypeError):
            pass # Ignorer les dates invalides

    # Pagination sur la liste filtrée
    paginator = Paginator(filtered_locations, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Statistiques basées sur les données RDF filtrées
    total_locations = len(filtered_locations)
    locations_actives = len([loc for loc in filtered_locations if loc.get('statutLocation') in ['en_attente', 'confirmee', 'en_cours']])

    context = {
        'page_title': 'Mes Locations - SmartCity',
        'locations': [],  # Gardé vide pour forcer l'utilisation du bloc RDF dans le template
        'reservations': [],  # Alias vide
        'reservations_rdf': page_obj,  # Les données RDF paginées
        'total_locations': total_locations,
        'total_reservations': total_locations, # Alias
        'locations_actives': locations_actives,
        'reservations_actives': locations_actives, # Alias
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
        'statuts_choices': Location.STATUTS_LOCATION, # Gardé pour les filtres du template
        'types_choices': Location.TYPES_LOCATION,   # Gardé pour les filtres du template
        'source_donnees': 'Ontologie RDF', # Indiquer la source unique
    }
    
    return render(request, 'gestion_location/mes_locations.html', context)


@login_required
def detail_location_view(request, location_id):
    """Détail d'une location spécifique, 100% basé sur RDF."""
    
    # Essayer de récupérer depuis RDF par ID ou par numéro de location
    location_rdf = rdf_manager.get_location_by_id(location_id)
    if not location_rdf:
        location_rdf = rdf_manager.get_location_by_numero(location_id)

    # Si aucune donnée n'est trouvée dans l'ontologie
    if not location_rdf:
        messages.error(request, "Location non trouvée ou accès non autorisé.")
        # Rediriger l'admin vers la liste admin, l'utilisateur vers sa liste
        try:
            if request.user.profilutilisateur.est_administrateur:
                return redirect('gestion_location:admin_liste_locations')
        except ProfilUtilisateur.DoesNotExist:
            pass # Non-admin ou profil non trouvé, rediriger vers la page client
        return redirect('gestion_location:mes_locations')

    # Vérifier que l'utilisateur a le droit de voir cette location
    try:
        is_admin = request.user.profilutilisateur.est_administrateur
    except ProfilUtilisateur.DoesNotExist:
        is_admin = False

    user_id_from_rdf = location_rdf.get('utilisateurId')
    if not is_admin and user_id_from_rdf != str(request.user.id):
        messages.error(request, "Accès non autorisé à cette location.")
        return redirect('gestion_location:mes_locations')

    # Normaliser les données RDF pour le template
    try:
        location_data = {
            'id': location_rdf.get('id'),
            'uri': location_rdf.get('uri'),
            'numeroLocation': location_rdf.get('numeroLocation'),
            'statut': location_rdf.get('statutLocation'),
            'dateDebut': datetime.fromisoformat(location_rdf.get('dateDebutLocation')) if location_rdf.get('dateDebutLocation') else None,
            'dateFin': datetime.fromisoformat(location_rdf.get('dateFinLocation')) if location_rdf.get('dateFinLocation') else None,
            'lieuPrise': location_rdf.get('lieuPrise'),
            'lieuRetour': location_rdf.get('lieuRetour'),
            'conducteurPrincipal': location_rdf.get('conducteurPrincipal'),
            'conducteurSecondaire': location_rdf.get('conducteurSecondaire'),
            'vehicule': {
                'nom': f"Véhicule ID {location_rdf.get('vehiculeId')}", # Placeholder
                'image': '' # Placeholder
            },
            'prixTotal': location_rdf.get('prixTotalCalcule'),
            # Ajouter d'autres champs si nécessaire pour le template
        }
        source_donnees = 'Ontologie RDF'
    except (ValueError, TypeError) as e:
        logger.error(f"Erreur de parsing des données RDF pour la location {location_id}: {e}")
        messages.error(request, "Erreur de format de données dans l'ontologie.")
        return redirect('gestion_location:mes_locations')

    context = {
        'page_title': f'Location {location_data.get("numeroLocation", location_data.get("id", "-"))}',
        'location': location_data,
        'source_donnees': source_donnees,
    }
    
    return render(request, 'gestion_location/detail_location.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def modifier_location_view(request, location_id):
    """Modifier une location existante, 100% basé sur RDF."""
    
    # Récupérer la location depuis l'ontologie
    location_rdf = rdf_manager.get_location_by_id(location_id)
    if not location_rdf:
        location_rdf = rdf_manager.get_location_by_numero(location_id)

    if not location_rdf:
        messages.error(request, "Location non trouvée.")
        return redirect('gestion_location:mes_locations')

    # Vérifier les permissions
    if location_rdf.get('utilisateurId') != str(request.user.id):
        messages.error(request, "Vous n'êtes pas autorisé à modifier cette location.")
        return redirect('gestion_location:mes_locations')

    if request.method == 'GET':
        context = {
            'page_title': f"Modifier la Location {location_rdf.get('numeroLocation')}",
            'location': location_rdf,
        }
        return render(request, 'gestion_location/modifier_location.html', context)

    elif request.method == 'POST':
        try:
            # Vérifier que la location peut être modifiée
            if location_rdf.get('statutLocation') not in ['en_attente', 'confirmee']:
                messages.error(request, "Cette location ne peut plus être modifiée.")
                return redirect('gestion_location:detail_location', location_id=location_id)
            
            # Récupérer les nouvelles données du formulaire
            update_data = {
                'lieu_prise': request.POST.get('lieu_prise', location_rdf.get('lieuPrise')),
                'lieu_retour': request.POST.get('lieu_retour', location_rdf.get('lieuRetour')),
                'conducteur_principal': request.POST.get('conducteur_principal', location_rdf.get('conducteurPrincipal')),
                'conducteur_secondaire': request.POST.get('conducteur_secondaire', location_rdf.get('conducteurSecondaire')),
            }
            
            # Mettre à jour les données dans l'ontologie
            success, message = rdf_manager.update_location(location_id, update_data)
            
            if success:
                messages.success(request, "Location modifiée avec succès !")
                return redirect('gestion_location:detail_location', location_id=location_id)
            else:
                messages.error(request, f"Erreur lors de la modification: {message}")
                return redirect('gestion_location:detail_location', location_id=location_id)
        
        except Exception as e:
            logger.error(f"Erreur lors de la modification de la location {location_id}: {e}")
            messages.error(request, f"Une erreur inattendue est survenue lors de la modification.")
            return redirect('gestion_location:mes_locations')


@login_required
@require_http_methods(["POST"])
def annuler_location_view(request, location_id):
    """Annuler une location, 100% basé sur RDF."""
    
    try:
        # Récupérer la location depuis l'ontologie
        location_rdf = rdf_manager.get_location_by_id(location_id)
        if not location_rdf:
            location_rdf = rdf_manager.get_location_by_numero(location_id)

        if not location_rdf:
            messages.error(request, "Location non trouvée.")
            return redirect('gestion_location:mes_locations')

        # Vérifier les permissions
        if location_rdf.get('utilisateurId') != str(request.user.id):
            messages.error(request, "Vous n'êtes pas autorisé à annuler cette location.")
            return redirect('gestion_location:mes_locations')

        # Vérifier que la location peut être annulée
        if location_rdf.get('statutLocation') in ['terminee', 'annulee']:
            messages.error(request, "Cette location ne peut plus être annulée.")
            return redirect('gestion_location:mes_locations')
        
        # Mettre à jour le statut dans RDF
        success, message = rdf_manager.update_location_status(location_id, 'annulee')
        
        if success:
            # TODO: La mise à jour du statut du véhicule dépend encore de SQLite.
            # Idéalement, le statut du véhicule devrait aussi être dans l'ontologie.
            try:
                vehicule = VehiculeLocation.objects.get(id=location_rdf.get('vehiculeId'))
                vehicule.statut = 'disponible'
                vehicule.save()
            except VehiculeLocation.DoesNotExist:
                logger.warning(f"Impossible de libérer le véhicule {location_rdf.get('vehiculeId')} car il n'a pas été trouvé dans la base de données SQLite.")

            messages.success(request, "Location annulée avec succès !")
        else:
            messages.error(request, f"Erreur lors de l'annulation: {message}")

        return redirect('gestion_location:mes_locations')
        
    except Exception as e:
        logger.error(f"Erreur lors de l'annulation de la location {location_id}: {e}")
        messages.error(request, f"Une erreur inattendue est survenue.")
        return redirect('gestion_location:mes_locations')


# ========== VUES ADMIN (Backend) ==========

@login_required
def admin_dashboard_location_view(request):
    """Dashboard admin pour la gestion des locations, 100% basé sur RDF."""
    
    # Vérifier les permissions admin
    try:
        if not request.user.profilutilisateur.est_administrateur:
            messages.error(request, "Accès refusé.")
            return redirect('gestion_utilisateurs:dashboard_user')
    except ProfilUtilisateur.DoesNotExist:
        messages.error(request, "Profil utilisateur non trouvé.")
        return redirect('gestion_utilisateurs:dashboard_user')

    # Données de l'ontologie
    all_locations_rdf = rdf_manager.get_all_locations()
    all_vehicles_rdf = rdf_manager.get_vehicles_data()

    # Statistiques de location
    total_locations = len(all_locations_rdf)
    locations_en_cours = len([loc for loc in all_locations_rdf if loc.get('statutLocation') in ['en_attente', 'confirmee', 'en_cours']])
    locations_terminees = len([loc for loc in all_locations_rdf if loc.get('statutLocation') == 'terminee'])
    locations_recentes = sorted(all_locations_rdf, key=lambda loc: loc.get('dateDebutLocation', ''), reverse=True)[:10]

    # Statistiques des véhicules
    total_vehicules = len(all_vehicles_rdf)
    vehicules_disponibles = len([v for v in all_vehicles_rdf if v.get('statut') == 'disponible'])
    vehicules_loues = len([v for v in all_vehicles_rdf if v.get('statut') == 'loue'])
    vehicules_maintenance = len([v for v in all_vehicles_rdf if v.get('statut') == 'maintenance'])
    
    # Calcul des revenus du mois courant
    revenus_mois = 0
    current_month = timezone.now().month
    current_year = timezone.now().year
    for loc in all_locations_rdf:
        if loc.get('statutLocation') == 'terminee':
            try:
                date_fin = datetime.fromisoformat(loc.get('dateFinLocation'))
                if date_fin.month == current_month and date_fin.year == current_year:
                    revenus_mois += float(loc.get('prixTotalCalcule', 0))
            except (ValueError, TypeError):
                continue  # Ignorer les dates ou prix mal formatés

    # Les alertes restent basées sur SQLite car elles ne sont pas dans l'ontologie
    alertes_importantes = AlerteLocation.objects.filter(
        active=True,
        niveau_priorite__in=['haute', 'critique']
    ).order_by('-niveau_priorite')[:5]
    
    context = {
        'page_title': 'Dashboard Admin Location - SmartCity',
        'stats': {
            'total_reservations': total_locations,
            'reservations_en_cours': locations_en_cours,
            'reservations_terminees': locations_terminees,
            'total_vehicules': total_vehicules,
            'vehicules_disponibles': vehicules_disponibles,
            'vehicules_loues': vehicules_loues,
            'vehicules_maintenance': vehicules_maintenance,
            'revenus_mois': float(revenus_mois),
        },
        'alertes_importantes': alertes_importantes,
        'locations_recentes': locations_recentes,
        'source_donnees_loc': 'Ontologie RDF'
    }
    
    return render(request, 'gestion_location/admin_dashboard.html', context)


@login_required
def admin_liste_locations_view(request):
    """Liste de toutes les locations pour l'admin, 100% basé sur RDF."""
    
    # Vérifier les permissions admin
    try:
        if not request.user.profilutilisateur.est_administrateur:
            messages.error(request, "Accès refusé.")
            return redirect('gestion_utilisateurs:dashboard_user')
    except ProfilUtilisateur.DoesNotExist:
        messages.error(request, "Profil utilisateur non trouvé.")
        return redirect('gestion_utilisateurs:dashboard_user')
    
    # Récupérer toutes les locations depuis RDF
    try:
        all_locations_rdf = rdf_manager.get_all_locations()
    except Exception as e:
        logger.error(f"Erreur fatale lors de la récupération de toutes les locations RDF: {e}")
        messages.error(request, "Impossible de charger les locations depuis l'ontologie.")
        all_locations_rdf = []

    # Filtrage en Python
    statut_filtre = request.GET.get('statut')
    utilisateur_filtre = request.GET.get('utilisateur')
    date_debut_str = request.GET.get('date_debut')
    date_fin_str = request.GET.get('date_fin')

    filtered_locations = all_locations_rdf

    if statut_filtre:
        filtered_locations = [loc for loc in filtered_locations if loc.get('statutLocation') == statut_filtre]
    
    if utilisateur_filtre:
        filtered_locations = [loc for loc in filtered_locations if utilisateur_filtre.lower() in loc.get('utilisateurUsername', '').lower()]

    if date_debut_str:
        try:
            date_debut_parsed = timezone.datetime.strptime(date_debut_str, '%Y-%m-%d').date()
            filtered_locations = [
                loc for loc in filtered_locations 
                if loc.get('dateDebutLocation') and timezone.datetime.fromisoformat(loc['dateDebutLocation']).date() >= date_debut_parsed
            ]
        except (ValueError, TypeError):
            pass

    if date_fin_str:
        try:
            date_fin_parsed = timezone.datetime.strptime(date_fin_str, '%Y-%m-%d').date()
            filtered_locations = [
                loc for loc in filtered_locations 
                if loc.get('dateDebutLocation') and timezone.datetime.fromisoformat(loc['dateDebutLocation']).date() <= date_fin_parsed
            ]
        except (ValueError, TypeError):
            pass

    # Process locations to add a reliable URL identifier and filter out broken records
    processed_locations = []
    for loc in filtered_locations:
        new_loc = loc.copy()
        url_id = new_loc.get('numeroLocation')
        if not url_id:
            uri = new_loc.get('location', '')
            if '#' in uri:
                url_id = uri.split('#')[-1]
        
        # Only include locations that have a valid identifier
        if url_id:
            new_loc['id_for_url'] = url_id
            processed_locations.append(new_loc)

    # Pagination
    paginator = Paginator(processed_locations, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_title': 'Gestion des Locations - Admin',
        'locations': page_obj,
        'reservations': page_obj,  # Alias
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
        'statuts_choices': Location.STATUTS_LOCATION, # Gardé pour les filtres
        'filtres': {
            'statut': statut_filtre,
            'utilisateur': utilisateur_filtre,
            'date_debut': date_debut_str,
            'date_fin': date_fin_str,
        },
        'source_donnees': 'Ontologie RDF',
    }
    
    return render(request, 'gestion_location/admin_liste_locations.html', context)


@login_required
@require_http_methods(["POST"])
def admin_supprimer_location_view(request, location_id):
    """Supprimer une location (admin uniquement), 100% basé sur RDF."""
    
    # Vérifier les permissions admin
    try:
        if not request.user.profilutilisateur.est_administrateur:
            messages.error(request, "Accès refusé.")
            return redirect('gestion_utilisateurs:dashboard_user')
    except ProfilUtilisateur.DoesNotExist:
        messages.error(request, "Profil utilisateur non trouvé.")
        return redirect('gestion_utilisateurs:dashboard_user')
    
    try:
        # Récupérer les données de la location pour obtenir l'ID du véhicule
        location_rdf = rdf_manager.get_location_by_id(location_id)
        if not location_rdf:
            location_rdf = rdf_manager.get_location_by_numero(location_id)

        # Supprimer de RDF
        success, message = rdf_manager.delete_location(location_id)
        
        if success:
            messages.success(request, "Location supprimée avec succès de l'ontologie !")
            # TODO: La mise à jour du statut du véhicule dépend encore de SQLite.
            if location_rdf and location_rdf.get('vehiculeId'):
                try:
                    vehicule = VehiculeLocation.objects.get(id=location_rdf.get('vehiculeId'))
                    if vehicule.statut == 'reserve':
                        vehicule.statut = 'disponible'
                        vehicule.save()
                except VehiculeLocation.DoesNotExist:
                    logger.warning(f"Impossible de libérer le véhicule {location_rdf.get('vehiculeId')} car il n'est pas dans SQLite.")
        else:
            messages.error(request, f"Erreur lors de la suppression dans l'ontologie: {message}")
        
        return redirect('gestion_location:admin_liste_locations')
        
    except Exception as e:
        logger.error(f"Erreur lors de la suppression de la location {location_id}: {e}")
        messages.error(request, f"Erreur inattendue lors de la suppression: {str(e)}")
        return redirect('gestion_location:admin_liste_locations')


@login_required
@require_http_methods(["POST"])
def admin_changer_statut_location_view(request, location_id):
    """Changer le statut d'une location (admin uniquement), 100% basé sur RDF."""
    
    # Vérifier les permissions admin
    try:
        if not request.user.profilutilisateur.est_administrateur:
            messages.error(request, "Accès refusé.")
            return redirect('gestion_utilisateurs:dashboard_user')
    except ProfilUtilisateur.DoesNotExist:
        messages.error(request, "Profil utilisateur non trouvé.")
        return redirect('gestion_utilisateurs:dashboard_user')
    
    try:
        nouveau_statut = request.POST.get('nouveau_statut')
        
        if not nouveau_statut or nouveau_statut not in dict(Location.STATUTS_LOCATION):
            messages.error(request, "Statut invalide.")
            return redirect('gestion_location:admin_liste_locations')
        
        # Mettre à jour dans RDF
        success, message = rdf_manager.update_location_status(location_id, nouveau_statut)
        
        if success:
            messages.success(request, f"Statut changé vers '{nouveau_statut}' avec succès dans l'ontologie !")
            
            # TODO: La mise à jour du statut du véhicule dépend encore de SQLite.
            # Idéalement, le statut du véhicule devrait aussi être dans l'ontologie.
            location_rdf = rdf_manager.get_location_by_id(location_id)
            if location_rdf and location_rdf.get('vehiculeId'):
                try:
                    vehicule = VehiculeLocation.objects.get(id=location_rdf.get('vehiculeId'))
                    if nouveau_statut == 'confirmee':
                        vehicule.statut = 'reserve'
                        vehicule.save()
                    elif nouveau_statut == 'en_cours':
                        vehicule.statut = 'loue'
                        vehicule.save()
                    elif nouveau_statut == 'terminee' or nouveau_statut == 'annulee':
                        vehicule.statut = 'disponible'
                        vehicule.save()
                except VehiculeLocation.DoesNotExist:
                    logger.warning(f"Impossible de mettre à jour le statut du véhicule {location_rdf.get('vehiculeId')} car il n'est pas dans SQLite.")
        else:
            messages.error(request, f"Erreur lors du changement de statut dans l'ontologie: {message}")
        
        return redirect('gestion_location:admin_liste_locations')
        
    except Exception as e:
        logger.error(f"Erreur lors du changement de statut pour la location {location_id}: {e}")
        messages.error(request, f"Erreur inattendue: {str(e)}")
        return redirect('gestion_location:admin_liste_locations')


# ========== VUES AJAX ==========

@login_required
def ajax_disponibilite_vehicule(request, vehicule_id):
    """Vérifier la disponibilité d'un véhicule en AJAX, 100% basé sur RDF."""
    
    try:
        date_debut_str = request.GET.get('date_debut')
        date_fin_str = request.GET.get('date_fin')
        
        if not date_debut_str or not date_fin_str:
            return JsonResponse({'disponible': False, 'raison': 'Dates manquantes'})
        
        # Parser les dates de la requête
        try:
            req_date_debut = timezone.make_aware(datetime.fromisoformat(date_debut_str.replace('T', ' ')))
            req_date_fin = timezone.make_aware(datetime.fromisoformat(date_fin_str.replace('T', ' ')))
        except ValueError:
            return JsonResponse({'disponible': False, 'raison': 'Format de date invalide'})

        # Récupérer toutes les locations depuis l'ontologie
        all_locations = rdf_manager.get_all_locations()
        
        conflits = []
        disponible = True

        for loc in all_locations:
            # Vérifier si la location concerne le même véhicule et a un statut pertinent
            if (loc.get('vehiculeId') == vehicule_id and 
                loc.get('statutLocation') in ['en_attente', 'confirmee', 'en_cours']):
                
                loc_date_debut_str = loc.get('dateDebutLocation')
                loc_date_fin_str = loc.get('dateFinLocation')

                if not loc_date_debut_str or not loc_date_fin_str:
                    continue

                try:
                    loc_date_debut = timezone.datetime.fromisoformat(loc_date_debut_str)
                    loc_date_fin = timezone.datetime.fromisoformat(loc_date_fin_str)
                except ValueError:
                    continue # Ignorer les locations avec des dates mal formées

                # Logique de chevauchement de dates: (StartA < EndB) and (EndA > StartB)
                if (req_date_debut < loc_date_fin) and (req_date_fin > loc_date_debut):
                    disponible = False
                    conflits.append({
                        'numero_location': loc.get('numeroLocation', 'N/A'),
                        'date_debut': loc_date_debut.isoformat(),
                        'date_fin': loc_date_fin.isoformat(),
                    })
        
        # Récupérer les infos du véhicule pour la réponse (dépendance restante)
        vehicule = get_object_or_404(VehiculeLocation, id=vehicule_id)

        return JsonResponse({
            'disponible': disponible,
            'vehicule': {
                'id': vehicule.id,
                'nom': vehicule.type_location.nom,
                'prix_heure': float(vehicule.type_location.prix_heure),
                'statut': vehicule.statut,
            },
            'conflits': conflits if not disponible else []
        })
        
    except Exception as e:
        logger.error(f"Erreur AJAX pour disponibilité véhicule {vehicule_id}: {e}")
        return JsonResponse({'disponible': False, 'raison': str(e)})


@login_required
def ajax_calculer_prix(request):
    """Calculer le prix d'une location en AJAX"""
    
    try:
        vehicule_id = request.GET.get('vehicule_id')
        date_debut_str = request.GET.get('date_debut')
        date_fin_str = request.GET.get('date_fin')
        options = request.GET.getlist('options[]')
        services = request.GET.getlist('services[]')
        
        if not all([vehicule_id, date_debut_str, date_fin_str]):
            return JsonResponse({'erreur': 'Paramètres manquants'})
        
        vehicule = get_object_or_404(VehiculeLocation, id=vehicule_id)
        
        # Calculer la durée
        date_debut = timezone.datetime.fromisoformat(date_debut_str.replace('T', ' '))
        date_debut = timezone.make_aware(date_debut)
        date_fin = timezone.datetime.fromisoformat(date_fin_str.replace('T', ' '))
        date_fin = timezone.make_aware(date_fin)
        
        duree_heures = (date_fin - date_debut).total_seconds() / 3600
        
        # Prix de base
        prix_base = float(vehicule.type_location.prix_heure) * duree_heures
        
        # Prix des options
        prix_options = 0
        for option_id in options:
            try:
                option = OptionLocation.objects.get(id=option_id)
                if option.unite_tarification == 'location':
                    prix_options += float(option.prix_unitaire)
                elif option.unite_tarification == 'jour':
                    prix_options += float(option.prix_unitaire) * (duree_heures / 24)
                elif option.unite_tarification == 'heure':
                    prix_options += float(option.prix_unitaire) * duree_heures
            except OptionLocation.DoesNotExist:
                pass
        
        # Prix des services
        prix_services = 0
        for service_id in services:
            try:
                service = ServiceLocation.objects.get(id=service_id)
                prix_services += float(service.prix_fixe)
            except ServiceLocation.DoesNotExist:
                pass
        
        prix_total = prix_base + prix_options + prix_services
        
        return JsonResponse({
            'prix_base': prix_base,
            'prix_options': prix_options,
            'prix_services': prix_services,
            'prix_total': prix_total,
            'duree_heures': duree_heures,
            'caution': float(vehicule.type_location.caution_requise),
        })
        
    except Exception as e:
        return JsonResponse({'erreur': str(e)})


# ========== FONCTIONS UTILITAIRES ==========


def _generer_numero_location():
    """Génère un numéro de location unique"""
    return f"LOC{datetime.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:8].upper()}"


def _calculer_duree_location(date_debut, date_fin):
    """Calcule la durée d'une location en heures"""
    delta = date_fin - date_debut
    return delta.total_seconds() / 3600



def _verifier_disponibilite_vehicule(vehicule, date_debut, date_fin):
    """Vérifie la disponibilité d'un véhicule pour une période donnée"""
    conflits = Location.objects.filter(
        vehicule=vehicule,
        statut__in=['en_attente', 'confirmee', 'en_cours'],
        date_debut__lt=date_fin,
        date_fin__gt=date_debut
    )
    return not conflits.exists()


# Import du logger
import logging
logger = logging.getLogger(__name__)