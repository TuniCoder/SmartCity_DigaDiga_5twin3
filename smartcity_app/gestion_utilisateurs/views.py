"""
Vues pour la Gestion des Utilisateurs - SmartCity
Domaine : 👥 Utilisateurs
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
import json

from .models import ProfilUtilisateur, PreferenceLocalisation, HistoriqueActivite, RoleUtilisateur

# Fonctions utilitaires pour la vérification des permissions

def est_administrateur(user):
    """Vérifie si l'utilisateur est administrateur"""
    if not user.is_authenticated:
        return False
    try:
        profil = ProfilUtilisateur.objects.get(user=user)
        return profil.est_administrateur
    except ProfilUtilisateur.DoesNotExist:
        return False

def peut_voir_dashboard(user):
    """Vérifie si l'utilisateur peut voir le dashboard"""
    if not user.is_authenticated:
        return False
    try:
        profil = ProfilUtilisateur.objects.get(user=user)
        return profil.peut_acceder_dashboard
    except ProfilUtilisateur.DoesNotExist:
        return False

def peut_voir_ontologie(user):
    """Vérifie si l'utilisateur peut voir l'ontologie"""
    if not user.is_authenticated:
        return False
    try:
        profil = ProfilUtilisateur.objects.get(user=user)
        return profil.peut_acceder_ontologie
    except ProfilUtilisateur.DoesNotExist:
        return False


# ====== VUES COMMUNES ======

@login_required
def profil_utilisateur_view(request):
    """Vue du profil utilisateur"""
    try:
        profil, _ = ProfilUtilisateur.objects.get_or_create(user=request.user)
        
        context = {
            'page_title': 'Mon Profil - SmartCity',
            'profil': profil,
            'lieux_favoris': profil.lieux_favoris.all(),
            'activites_recentes': profil.historique.all()[:10],
            'est_admin': profil.est_administrateur,
            'peut_dashboard': profil.peut_acceder_dashboard,
            'peut_ontologie': profil.peut_acceder_ontologie,
        }
        
        return render(request, 'gestion_utilisateurs/profil.html', context)
        
    except Exception as e:
        messages.error(request, f"Erreur lors du chargement du profil: {str(e)}")
        return redirect('smartcity_app:index')

def connexion_view(request):
    """Vue de connexion avec redirection selon le rôle"""
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            
            # Redirection selon le rôle
            try:
                profil = ProfilUtilisateur.objects.get(user=user)
                if profil.est_administrateur:
                    messages.success(request, f"Bienvenue Administrateur {user.get_full_name() or user.username} !")
                    return redirect('gestion_utilisateurs:dashboard_admin')
                else:
                    messages.success(request, f"Bienvenue {user.get_full_name() or user.username} !")
                    return redirect('gestion_utilisateurs:dashboard_user')
            except ProfilUtilisateur.DoesNotExist:
                return redirect('smartcity_app:index')
        else:
            messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")
    
    return render(request, 'gestion_utilisateurs/connexion.html')

@login_required
def deconnexion_view(request):
    """Vue de déconnexion"""
    logout(request)
    messages.success(request, "Vous avez été déconnecté avec succès.")
    return redirect('smartcity_app:index')

# ====== VUES UTILISATEUR NORMAL ======

@login_required
def dashboard_utilisateur_view(request):
    """Dashboard pour utilisateur normal"""
    try:
        profil = ProfilUtilisateur.objects.get(user=request.user)
        
        # Vérifier les permissions
        if profil.est_administrateur:
            return redirect('gestion_utilisateurs:dashboard_admin')
        
        # Statistiques personnelles
        mes_trajets_count = profil.historique.filter(type_activite='planification_trajet').count()
        mes_lieux_count = profil.lieux_favoris.count()
        activites_semaine = profil.historique.filter(
            timestamp__gte=timezone.now() - timedelta(days=7)
        ).count()
        
        context = {
            'page_title': 'Mon Dashboard - SmartCity',
            'profil': profil,
            'mes_trajets_count': mes_trajets_count,
            'mes_lieux_count': mes_lieux_count,
            'activites_semaine': activites_semaine,
            'activites_recentes': profil.historique.all()[:5],
            'est_admin': False,
        }
        
        return render(request, 'gestion_utilisateurs/dashboard_user.html', context)
        
    except ProfilUtilisateur.DoesNotExist:
        messages.error(request, "Profil utilisateur non trouvé.")
        return redirect('smartcity_app:index')

@login_required  
def mes_trajets_view(request):
    """Mes trajets planifiés - Utilisateur normal"""
    profil = get_object_or_404(ProfilUtilisateur, user=request.user)
    
    trajets_planifies = profil.historique.filter(
        type_activite='planification_trajet'
    ).order_by('-timestamp')
    
    context = {
        'page_title': 'Mes Trajets - SmartCity',
        'profil': profil,
        'trajets': trajets_planifies,
        'est_admin': False,
    }
    
    return render(request, 'gestion_utilisateurs/mes_trajets.html', context)

# ====== VUES ADMINISTRATEUR ======

@user_passes_test(est_administrateur)
def dashboard_admin_view(request):
    """Dashboard pour administrateur"""
    try:
        # Statistiques globales
        total_utilisateurs = User.objects.count()
        utilisateurs_actifs_7j = HistoriqueActivite.objects.filter(
            timestamp__gte=timezone.now() - timedelta(days=7)
        ).values('profil').distinct().count()
        
        # Statistiques par rôle
        admins_count = ProfilUtilisateur.objects.filter(role__type_role='admin').count()
        users_count = ProfilUtilisateur.objects.filter(role__type_role='user').count()
        
        # Activités récentes du système
        activites_recentes = HistoriqueActivite.objects.select_related('profil__user').order_by('-timestamp')[:10]
        
        context = {
            'page_title': 'Dashboard Administrateur - SmartCity',
            'total_utilisateurs': total_utilisateurs,
            'admins_count': admins_count,
            'users_count': users_count,
            'utilisateurs_actifs_7j': utilisateurs_actifs_7j,
            'activites_recentes': activites_recentes,
            'est_admin': True,
        }
        
        return render(request, 'gestion_utilisateurs/dashboard_admin.html', context)
        
    except Exception as e:
        messages.error(request, f"Erreur lors du chargement du dashboard: {str(e)}")
        return redirect('smartcity_app:index')

@user_passes_test(est_administrateur)
def gestion_utilisateurs_admin_view(request):
    """Gestion des utilisateurs - Administrateur uniquement"""
    utilisateurs = ProfilUtilisateur.objects.select_related('user', 'role').order_by('-date_creation')
    
    # Filtres
    role_filtre = request.GET.get('role', '')
    recherche = request.GET.get('q', '')
    
    if role_filtre:
        utilisateurs = utilisateurs.filter(role__type_role=role_filtre)
    
    if recherche:
        utilisateurs = utilisateurs.filter(
            Q(user__username__icontains=recherche) |
            Q(user__first_name__icontains=recherche) |
            Q(user__last_name__icontains=recherche) |
            Q(user__email__icontains=recherche)
        )
    
    context = {
        'page_title': 'Gestion des Utilisateurs - SmartCity',
        'utilisateurs': utilisateurs,
        'roles': RoleUtilisateur.objects.all(),
        'role_filtre': role_filtre,
        'recherche': recherche,
        'est_admin': True,
    }
    
    return render(request, 'gestion_utilisateurs/gestion_users_admin.html', context)

@user_passes_test(est_administrateur) 
def changer_role_utilisateur(request, user_id):
    """Changer le rôle d'un utilisateur - Admin uniquement"""
    if request.method == 'POST':
        try:
            profil = get_object_or_404(ProfilUtilisateur, user_id=user_id)
            nouveau_role_id = request.POST.get('nouveau_role')
            nouveau_role = get_object_or_404(RoleUtilisateur, id=nouveau_role_id)
            
            ancien_role = profil.role.nom
            profil.role = nouveau_role
            profil.save()
            
            # Enregistrer l'activité
            HistoriqueActivite.objects.create(
                profil=profil,
                type_activite='modification_profil',
                description=f'Changement de rôle: {ancien_role} → {nouveau_role.nom}',
                donnees_contexte={'action': 'changement_role', 'ancien_role': ancien_role, 'nouveau_role': nouveau_role.nom}
            )
            
            messages.success(request, f"Rôle de {profil.user.username} changé vers '{nouveau_role.nom}' avec succès!")
            
        except Exception as e:
            messages.error(request, f"Erreur lors du changement de rôle: {str(e)}")
    
    return redirect('gestion_utilisateurs:gestion_users_admin')


@login_required
def modifier_profil_view(request):
    """Vue pour modifier le profil utilisateur"""
    if request.method == 'POST':
        try:
            profil, created = ProfilUtilisateur.objects.get_or_create(user=request.user)
            
            # Mise à jour des informations de base
            profil.telephone = request.POST.get('telephone', '')
            profil.adresse = request.POST.get('adresse', '')
            profil.budget_transport_mensuel = request.POST.get('budget_transport_mensuel')
            profil.temps_trajet_max_acceptable = request.POST.get('temps_trajet_max_acceptable')
            
            # Préférences de transport
            modes_preferes = request.POST.getlist('modes_transport_preferes')
            profil.modes_transport_preferes = modes_preferes
            
            # Accessibilité
            profil.necessite_accessibilite = 'necessite_accessibilite' in request.POST
            profil.type_handicap = request.POST.get('type_handicap', '')
            
            # Préférences environnementales
            profil.preference_eco_friendly = 'preference_eco_friendly' in request.POST
            profil.accepte_modes_alternatifs = 'accepte_modes_alternatifs' in request.POST
            
            profil.save()
            
            # Enregistrer l'activité
            HistoriqueActivite.objects.create(
                profil=profil,
                type_activite='modification_profil',
                description='Modification des informations du profil',
                donnees_contexte={'action': 'mise_a_jour_profil'}
            )
            
            messages.success(request, "Profil mis à jour avec succès!")
            return redirect('profil_utilisateur')
            
        except Exception as e:
            messages.error(request, f"Erreur lors de la mise à jour: {str(e)}")
    
    profil, created = ProfilUtilisateur.objects.get_or_create(user=request.user)
    context = {
        'page_title': 'Modifier le Profil - SmartCity',
        'profil': profil,
    }
    
    return render(request, 'gestion_utilisateurs/modifier_profil.html', context)


@login_required
def ajouter_lieu_favori_view(request):
    """Vue pour ajouter un lieu favori"""
    if request.method == 'POST':
        try:
            profil, created = ProfilUtilisateur.objects.get_or_create(user=request.user)
            
            lieu = PreferenceLocalisation.objects.create(
                profil=profil,
                nom_lieu=request.POST['nom_lieu'],
                type_lieu=request.POST['type_lieu'],
                adresse=request.POST['adresse'],
                latitude=request.POST.get('latitude') or None,
                longitude=request.POST.get('longitude') or None,
                frequence_visite=int(request.POST.get('frequence_visite', 1))
            )
            
            # Enregistrer l'activité
            HistoriqueActivite.objects.create(
                profil=profil,
                type_activite='modification_profil',
                description=f'Ajout du lieu favori: {lieu.nom_lieu}',
                donnees_contexte={'action': 'ajout_lieu_favori', 'lieu_id': lieu.id}
            )
            
            messages.success(request, f"Lieu '{lieu.nom_lieu}' ajouté avec succès!")
            
        except Exception as e:
            messages.error(request, f"Erreur lors de l'ajout du lieu: {str(e)}")
    
    return redirect('profil_utilisateur')


@login_required
def supprimer_lieu_favori_view(request, lieu_id):
    """Vue pour supprimer un lieu favori"""
    try:
        profil = ProfilUtilisateur.objects.get(user=request.user)
        lieu = get_object_or_404(PreferenceLocalisation, id=lieu_id, profil=profil)
        
        nom_lieu = lieu.nom_lieu
        lieu.delete()
        
        # Enregistrer l'activité
        HistoriqueActivite.objects.create(
            profil=profil,
            type_activite='modification_profil',
            description=f'Suppression du lieu favori: {nom_lieu}',
            donnees_contexte={'action': 'suppression_lieu_favori'}
        )
        
        messages.success(request, f"Lieu '{nom_lieu}' supprimé avec succès!")
        
    except Exception as e:
        messages.error(request, f"Erreur lors de la suppression: {str(e)}")
    
    return redirect('profil_utilisateur')


def tableau_bord_utilisateurs_view(request):
    """Vue du tableau de bord administrateur pour les utilisateurs"""
    # Vue réservée aux administrateurs
    if not request.user.is_staff:
        messages.error(request, "Accès non autorisé.")
        return redirect('smartcity_app:index')
    
    try:
        # Statistiques générales
        total_utilisateurs = User.objects.count()
        utilisateurs_avec_profil = ProfilUtilisateur.objects.count()
        utilisateurs_actifs_7j = HistoriqueActivite.objects.filter(
            timestamp__gte=timezone.now() - timedelta(days=7)
        ).values('profil').distinct().count()
        
        # Statistiques par mode de transport préféré
        from collections import Counter
        modes_transport = []
        for profil in ProfilUtilisateur.objects.all():
            if profil.modes_transport_preferes:
                modes_transport.extend(profil.modes_transport_preferes)
        
        stats_modes = dict(Counter(modes_transport))
        
        # Utilisateurs récents
        utilisateurs_recents = ProfilUtilisateur.objects.select_related('user').order_by('-date_creation')[:10]
        
        context = {
            'page_title': 'Tableau de Bord Utilisateurs - SmartCity',
            'total_utilisateurs': total_utilisateurs,
            'utilisateurs_avec_profil': utilisateurs_avec_profil,
            'utilisateurs_actifs_7j': utilisateurs_actifs_7j,
            'stats_modes_transport': stats_modes,
            'utilisateurs_recents': utilisateurs_recents,
            'pourcentage_profils_complets': round((utilisateurs_avec_profil / total_utilisateurs) * 100, 1) if total_utilisateurs > 0 else 0,
        }
        
        return render(request, 'gestion_utilisateurs/tableau_bord.html', context)
        
    except Exception as e:
        messages.error(request, f"Erreur lors du chargement du tableau de bord: {str(e)}")
        return redirect('smartcity_app:index')


# API Endpoints pour les utilisateurs

@login_required
def api_profil_utilisateur(request):
    """API pour récupérer les données du profil utilisateur"""
    try:
        profil = ProfilUtilisateur.objects.get(user=request.user)
        
        data = {
            'id': profil.id,
            'nom_complet': request.user.get_full_name() or request.user.username,
            'email': request.user.email,
            'telephone': profil.telephone,
            'adresse': profil.adresse,
            'modes_transport_preferes': profil.modes_transport_preferes,
            'budget_transport_mensuel': float(profil.budget_transport_mensuel) if profil.budget_transport_mensuel else None,
            'temps_trajet_max_acceptable': profil.temps_trajet_max_acceptable,
            'necessite_accessibilite': profil.necessite_accessibilite,
            'preference_eco_friendly': profil.preference_eco_friendly,
            'nombre_lieux_favoris': profil.lieux_favoris.count(),
            'date_creation': profil.date_creation.isoformat(),
        }
        
        return JsonResponse({'status': 'success', 'data': data})
        
    except ProfilUtilisateur.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Profil utilisateur non trouvé'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
def api_lieux_favoris(request):
    """API pour récupérer les lieux favoris de l'utilisateur"""
    try:
        profil = ProfilUtilisateur.objects.get(user=request.user)
        lieux = []
        
        for lieu in profil.lieux_favoris.all():
            lieux.append({
                'id': lieu.id,
                'nom_lieu': lieu.nom_lieu,
                'type_lieu': lieu.type_lieu,
                'type_lieu_display': lieu.get_type_lieu_display(),
                'adresse': lieu.adresse,
                'latitude': lieu.latitude,
                'longitude': lieu.longitude,
                'frequence_visite': lieu.frequence_visite,
                'date_creation': lieu.date_creation.isoformat(),
            })
        
        return JsonResponse({'status': 'success', 'data': lieux})
        
    except ProfilUtilisateur.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Profil utilisateur non trouvé'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


# ====== NOUVELLES VUES POUR GESTION DES RÔLES ======

@login_required
def dashboard_user(request):
    """Dashboard simplifié pour utilisateur normal"""
    if est_administrateur(request.user):
        return redirect('gestion_utilisateurs:dashboard_admin')
    
    try:
        profil = ProfilUtilisateur.objects.get(user=request.user)
        context = {
            'profil': profil,
        }
        return render(request, 'gestion_utilisateurs/dashboard_user.html', context)
        
    except ProfilUtilisateur.DoesNotExist:
        messages.error(request, "Profil utilisateur non trouvé.")
        return redirect('smartcity_app:index')

@login_required
@user_passes_test(est_administrateur)
@login_required 
@user_passes_test(est_administrateur)
def dashboard_admin(request):
    """Dashboard complet pour administrateurs"""
    # Calculer les statistiques
    total_users = User.objects.count()
    admin_users_count = ProfilUtilisateur.objects.filter(role__type_role='admin').count()
    normal_users_count = ProfilUtilisateur.objects.filter(role__type_role='user').count()
    
    stats = {
        'total_users': total_users,
        'active_users': User.objects.filter(is_active=True).count(),
        'admin_users': admin_users_count,
        'normal_users': normal_users_count,  # Utiliser le bon nom de variable
        'rdf_entities': 438,
    }
    
    # Utilisateurs récents (derniers 5) - avec gestion des profils manquants
    recent_users = []
    for user in User.objects.order_by('-date_joined')[:5]:
        try:
            # Vérifier que le profil existe
            profil = user.profilutilisateur
            recent_users.append(user)
        except ProfilUtilisateur.DoesNotExist:
            # Créer un profil par défaut si manquant
            try:
                role_user = RoleUtilisateur.objects.get(type_role='user')
                ProfilUtilisateur.objects.create(user=user, role=role_user)
                recent_users.append(user)
            except Exception:
                # Si on ne peut pas créer le profil, ignorer cet utilisateur
                continue
    
    context = {
        'stats': stats,
        'recent_users': recent_users,
    }
    
    return render(request, 'gestion_utilisateurs/dashboard_admin.html', context)

@login_required
@user_passes_test(est_administrateur)
def liste_utilisateurs(request):
    """Liste et gestion des utilisateurs pour admin"""
    users = User.objects.select_related('profilutilisateur__role').all()
    roles = RoleUtilisateur.objects.all()
    
    # Filtres
    search = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')
    status_filter = request.GET.get('status', '')
    
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )
    
    if role_filter:
        users = users.filter(profilutilisateur__role_id=role_filter)
    
    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)
    
    # Statistiques
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    admin_users = ProfilUtilisateur.objects.filter(role__type_role='admin').count()
    new_users = User.objects.filter(
        date_joined__gte=timezone.now() - timedelta(days=7)
    ).count()
    
    context = {
        'users': users,
        'roles': roles,
        'total_users': total_users,
        'active_users': active_users,
        'admin_users': admin_users,
        'new_users': new_users,
    }
    
    return render(request, 'gestion_utilisateurs/liste_utilisateurs.html', context)

@login_required
@user_passes_test(est_administrateur)
def creer_utilisateur(request):
    """Créer un nouvel utilisateur"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        role_id = request.POST.get('role')
        is_active = request.POST.get('is_active') == 'on'
        
        # Validation
        if not username or not email or not password1 or not role_id:
            messages.error(request, "Tous les champs obligatoires doivent être remplis.")
            return redirect('gestion_utilisateurs:liste_utilisateurs')
        
        if password1 != password2:
            messages.error(request, "Les mots de passe ne correspondent pas.")
            return redirect('gestion_utilisateurs:liste_utilisateurs')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, "Ce nom d'utilisateur existe déjà.")
            return redirect('gestion_utilisateurs:liste_utilisateurs')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, "Cette adresse email est déjà utilisée.")
            return redirect('gestion_utilisateurs:liste_utilisateurs')
        
        try:
            # Créer l'utilisateur
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                first_name=first_name,
                last_name=last_name,
                is_active=is_active
            )
            
            # Assigner le rôle via le profil
            role = RoleUtilisateur.objects.get(id=role_id)
            profil, created = ProfilUtilisateur.objects.get_or_create(user=user)
            profil.role = role
            profil.save()
            
            messages.success(request, f"Utilisateur {username} créé avec succès!")
            
        except Exception as e:
            messages.error(request, f"Erreur lors de la création : {str(e)}")
    
    return redirect('gestion_utilisateurs:liste_utilisateurs')


@login_required
@user_passes_test(est_administrateur)
@login_required 
@user_passes_test(est_administrateur)
def modifier_role_utilisateur(request, user_id):
    """Modifier le rôle d'un utilisateur avec synchronisation RDF"""
    if request.method == 'POST':
        try:
            from ..ontology_manager.rdf_utils import rdf_manager
            
            user = get_object_or_404(User, id=user_id)
            nouveau_role = request.POST.get('nouveau_role')
            
            if nouveau_role not in ['user', 'admin']:
                error_msg = "Rôle invalide."
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'message': error_msg})
                messages.error(request, error_msg)
                return redirect('gestion_utilisateurs:liste_utilisateurs')
            
            # Mettre à jour le profil Django
            profil, created = ProfilUtilisateur.objects.get_or_create(user=user)
            
            # Récupérer l'instance de RoleUtilisateur
            try:
                nouveau_role_obj = RoleUtilisateur.objects.get(type_role=nouveau_role)
            except RoleUtilisateur.DoesNotExist:
                error_msg = f"Rôle '{nouveau_role}' non trouvé dans la base de données."
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'message': error_msg})
                messages.error(request, error_msg)
                return redirect('gestion_utilisateurs:liste_utilisateurs')
            
            ancien_role = profil.role.type_role if profil.role else 'user'
            profil.role = nouveau_role_obj
            
            profil.save()
            
            # Synchroniser avec le RDF
            rdf_success = True
            try:
                if not rdf_manager.sync_user_to_rdf(user):
                    rdf_success = False
            except Exception as rdf_error:
                rdf_success = False
            
            # Préparer le message de succès
            if rdf_success:
                success_msg = f"Rôle de {user.username} modifié vers '{nouveau_role}' avec succès (Django + RDF)!"
            else:
                success_msg = f"Rôle modifié dans Django mais erreur de synchronisation RDF pour {user.username}"
            
            # Enregistrer l'activité
            try:
                HistoriqueActivite.objects.create(
                    profil=profil,
                    type_activite='modification_profil',
                    description=f'Changement de rôle par admin: {ancien_role} → {nouveau_role}',
                    donnees_contexte={
                        'action': 'changement_role_admin',
                        'ancien_role': str(ancien_role),
                        'nouveau_role': nouveau_role,
                        'modifie_par': request.user.username
                    }
                )
            except Exception as hist_error:
                # Ne pas faire échouer la modification pour l'historique
                pass
            
            # Réponse selon le type de requête
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True, 
                    'message': success_msg,
                    'nouveau_role': nouveau_role,
                    'rdf_success': rdf_success
                })
            else:
                if rdf_success:
                    messages.success(request, success_msg)
                else:
                    messages.warning(request, success_msg)
                return redirect('gestion_utilisateurs:liste_utilisateurs')
                
        except Exception as e:
            error_msg = f"Erreur lors de la modification du rôle: {str(e)}"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': error_msg})
            messages.error(request, error_msg)
            return redirect('gestion_utilisateurs:liste_utilisateurs')
    
    # GET request - redirect to list
    return redirect('gestion_utilisateurs:liste_utilisateurs')


@login_required 
@user_passes_test(est_administrateur)
def synchroniser_utilisateurs_rdf(request):
    """Synchroniser tous les utilisateurs vers le RDF"""
    if request.method == 'POST':
        try:
            from ..ontology_manager.rdf_utils import rdf_manager
            
            users = User.objects.all()
            success_count = 0
            error_count = 0
            
            for user in users:
                try:
                    if rdf_manager.sync_user_to_rdf(user):
                        success_count += 1
                    else:
                        error_count += 1
                except Exception as e:
                    error_count += 1
            
            if error_count == 0:
                messages.success(
                    request, 
                    f"Synchronisation réussie ! {success_count} utilisateurs synchronisés vers le RDF."
                )
            else:
                messages.warning(
                    request, 
                    f"Synchronisation partielle : {success_count} réussies, {error_count} erreurs."
                )
                
        except Exception as e:
            messages.error(request, f"Erreur lors de la synchronisation : {str(e)}")
    
    return redirect('gestion_utilisateurs:liste_utilisateurs')


@login_required
@user_passes_test(est_administrateur)
def voir_utilisateur(request, user_id):
    """Voir les détails d'un utilisateur - Admin uniquement"""
    user = get_object_or_404(User, id=user_id)
    try:
        profil = ProfilUtilisateur.objects.get(user=user)
    except ProfilUtilisateur.DoesNotExist:
        profil = None
    
    # Récupérer les informations RDF si disponibles
    try:
        from ..ontology_manager.rdf_utils import rdf_manager
        rdf_data = rdf_manager.get_user_from_rdf(str(user_id))
    except Exception:
        rdf_data = {}
    
    context = {
        'user_detail': user,
        'profil': profil,
        'rdf_data': rdf_data,
    }
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        from django.template.loader import render_to_string
        html = render_to_string('gestion_utilisateurs/user_detail_modal.html', context, request)
        return JsonResponse({'html': html})
    
    return JsonResponse({'error': 'Requête non autorisée'}, status=400)


@login_required
@user_passes_test(est_administrateur)
def modifier_utilisateur(request, user_id):
    """Modifier un utilisateur - Admin uniquement"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        try:
            # Mettre à jour les informations de base
            user.first_name = request.POST.get('first_name', '').strip()
            user.last_name = request.POST.get('last_name', '').strip()
            user.email = request.POST.get('email', '').strip()
            user.is_active = request.POST.get('is_active') == 'on'
            user.save()
            
            # Mettre à jour le profil
            profil, created = ProfilUtilisateur.objects.get_or_create(user=user)
            profil.telephone = request.POST.get('telephone', '').strip()
            profil.save()
            
            # Synchroniser avec RDF
            try:
                from ..ontology_manager.rdf_utils import rdf_manager
                rdf_manager.sync_user_to_rdf(user)
            except Exception as e:
                messages.warning(request, f"Utilisateur modifié mais erreur de synchronisation RDF: {str(e)}")
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f'Utilisateur {user.username} modifié avec succès!'
                })
            else:
                messages.success(request, f'Utilisateur {user.username} modifié avec succès!')
                return redirect('gestion_utilisateurs:liste_utilisateurs')
                
        except Exception as e:
            error_msg = f"Erreur lors de la modification: {str(e)}"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': error_msg})
            else:
                messages.error(request, error_msg)
                return redirect('gestion_utilisateurs:liste_utilisateurs')
    
    # GET - Récupérer les données pour le modal
    try:
        profil = ProfilUtilisateur.objects.get(user=user)
    except ProfilUtilisateur.DoesNotExist:
        profil = None
    
    context = {
        'user_edit': user,
        'profil': profil,
    }
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        from django.template.loader import render_to_string
        html = render_to_string('gestion_utilisateurs/user_edit_modal.html', context, request)
        return JsonResponse({'html': html})
    
    return JsonResponse({'error': 'Requête non autorisée'}, status=400)


@login_required
@user_passes_test(est_administrateur)
def changer_statut_utilisateur(request, user_id):
    """Activer/Désactiver un utilisateur - Admin uniquement"""
    if request.method == 'POST':
        try:
            user = get_object_or_404(User, id=user_id)
            
            # Ne pas permettre de désactiver son propre compte
            if user == request.user:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': 'Vous ne pouvez pas désactiver votre propre compte!'
                    })
                else:
                    messages.error(request, 'Vous ne pouvez pas désactiver votre propre compte!')
                    return redirect('gestion_utilisateurs:liste_utilisateurs')
            
            # Inverser le statut
            nouveau_statut = not user.is_active
            user.is_active = nouveau_statut
            user.save()
            
            statut_text = "activé" if nouveau_statut else "désactivé"
            message = f'Utilisateur {user.username} {statut_text} avec succès!'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': message,
                    'new_status': nouveau_statut,
                    'status_text': 'Actif' if nouveau_statut else 'Inactif',
                    'status_class': 'success' if nouveau_statut else 'warning'
                })
            else:
                messages.success(request, message)
                return redirect('gestion_utilisateurs:liste_utilisateurs')
                
        except Exception as e:
            error_msg = f"Erreur lors du changement de statut: {str(e)}"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': error_msg})
            else:
                messages.error(request, error_msg)
                return redirect('gestion_utilisateurs:liste_utilisateurs')
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


@login_required
@user_passes_test(est_administrateur)
def supprimer_utilisateur(request, user_id):
    """Supprimer un utilisateur - Admin uniquement"""
    if request.method == 'POST':
        try:
            user = get_object_or_404(User, id=user_id)
            
            # Ne pas permettre de supprimer son propre compte
            if user == request.user:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': 'Vous ne pouvez pas supprimer votre propre compte!'
                    })
                else:
                    messages.error(request, 'Vous ne pouvez pas supprimer votre propre compte!')
                    return redirect('gestion_utilisateurs:liste_utilisateurs')
            
            username = user.username
            
            # Supprimer du RDF si possible
            try:
                from ..ontology_manager.rdf_utils import rdf_manager
                rdf_manager.delete_user_from_rdf(str(user_id))
            except Exception as e:
                # Continue même si la suppression RDF échoue
                pass
            
            # Supprimer l'utilisateur (cascade supprimera le profil)
            user.delete()
            
            message = f'Utilisateur {username} supprimé avec succès!'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': message
                })
            else:
                messages.success(request, message)
                return redirect('gestion_utilisateurs:liste_utilisateurs')
                
        except Exception as e:
            error_msg = f"Erreur lors de la suppression: {str(e)}"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': error_msg})
            else:
                messages.error(request, error_msg)
                return redirect('gestion_utilisateurs:liste_utilisateurs')
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)