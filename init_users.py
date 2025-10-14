"""
Script d'initialisation des rôles et utilisateurs de test
Exécuter avec : python manage.py shell < init_users.py
"""

from django.contrib.auth.models import User
from smartcity_app.gestion_utilisateurs.models import RoleUtilisateur, ProfilUtilisateur

# Créer les rôles s'ils n'existent pas
role_admin, created = RoleUtilisateur.objects.get_or_create(
    nom='Administrateur',
    defaults={
        'type_role': 'admin',
        'description': 'Administrateur avec tous les droits',
        'peut_voir_dashboard': True,
        'peut_voir_ontologie': True,
        'peut_gerer_utilisateurs': True,
        'peut_modifier_systeme': True,
        'peut_voir_stats_globales': True
    }
)

role_user, created = RoleUtilisateur.objects.get_or_create(
    nom='Utilisateur',
    defaults={
        'type_role': 'user',
        'description': 'Utilisateur standard avec accès limité',
        'peut_voir_dashboard': False,
        'peut_voir_ontologie': False,  # Les utilisateurs normaux n'ont pas accès à l'ontologie complète
        'peut_gerer_utilisateurs': False,
        'peut_modifier_systeme': False,
        'peut_voir_stats_globales': False
    }
)

print(f"Rôles créés : {role_admin.nom}, {role_user.nom}")

# Créer utilisateur admin s'il n'existe pas
if not User.objects.filter(username='admin').exists():
    admin_user = User.objects.create_user(
        username='admin',
        email='admin@smartcity.com',
        password='admin123',
        first_name='Admin',
        last_name='System',
        is_active=True,
        is_staff=True,
        is_superuser=True
    )
    
    # Assigner le rôle admin
    try:
        profil_admin = ProfilUtilisateur.objects.get(user=admin_user)
        profil_admin.role = role_admin
        profil_admin.save()
        print(f"Utilisateur admin créé avec le rôle : {role_admin.nom}")
    except ProfilUtilisateur.DoesNotExist:
        print("Erreur : Profil admin non créé automatiquement")
else:
    print("Utilisateur admin existe déjà")

# Créer utilisateur normal s'il n'existe pas
if not User.objects.filter(username='user').exists():
    normal_user = User.objects.create_user(
        username='user',
        email='user@smartcity.com',
        password='user123',
        first_name='Utilisateur',
        last_name='Normal',
        is_active=True
    )
    
    # Assigner le rôle utilisateur
    try:
        profil_user = ProfilUtilisateur.objects.get(user=normal_user)
        profil_user.role = role_user
        profil_user.save()
        print(f"Utilisateur normal créé avec le rôle : {role_user.nom}")
    except ProfilUtilisateur.DoesNotExist:
        print("Erreur : Profil utilisateur non créé automatiquement")
else:
    print("Utilisateur normal existe déjà")

print("\nInitialisation terminée !")
print("Comptes disponibles :")
print("- Admin : admin / admin123")
print("- Utilisateur : user / user123")