"""
Tests pour les vues utilisateur - Gestion du Trafic
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import ZoneTrafic, CapteurTrafic, DonneesTrafic, EvenementTrafic
from datetime import datetime, timedelta
from django.utils import timezone


class UserTrafficViewsTestCase(TestCase):
    """Tests pour les vues utilisateur du trafic"""
    
    def setUp(self):
        """Initialiser les données de test"""
        self.client = Client()
        
        # Créer un utilisateur de test
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Créer une zone de test
        self.zone = ZoneTrafic.objects.create(
            nom='Zone Test',
            type_zone='centre_ville',
            coordonnees_zone='{"type": "Point", "coordinates": [10.5, 35.8]}',
            vitesse_limite=50,
            nombre_voies=2,
            sens_circulation='Bidirectionnel'
        )
        
        # Créer un capteur de test
        self.capteur = CapteurTrafic.objects.create(
            nom='Capteur Test',
            code_capteur='CAP001',
            type_capteur='radar',
            zone_trafic=self.zone,
            latitude=35.8,
            longitude=10.5,
            statut='actif',
            date_installation=timezone.now()
        )
        
        # Créer des données de trafic
        self.donnees = DonneesTrafic.objects.create(
            capteur=self.capteur,
            timestamp=timezone.now(),
            nombre_vehicules=50,
            vitesse_moyenne=45,
            niveau_congestion=30,
            taux_occupation=0.5
        )
    
    def test_dashboard_user_trafic_requires_login(self):
        """Test que le dashboard nécessite une authentification"""
        response = self.client.get(reverse('gestion_trafic:dashboard_user_trafic'))
        self.assertEqual(response.status_code, 302)  # Redirection vers login
    
    def test_dashboard_user_trafic_authenticated(self):
        """Test le dashboard pour un utilisateur authentifié"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('gestion_trafic:dashboard_user_trafic'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'gestion_trafic/user/dashboard_trafic.html')
    
    def test_carte_trafic_user_requires_login(self):
        """Test que la carte nécessite une authentification"""
        response = self.client.get(reverse('gestion_trafic:carte_trafic_user'))
        self.assertEqual(response.status_code, 302)
    
    def test_carte_trafic_user_authenticated(self):
        """Test la carte pour un utilisateur authentifié"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('gestion_trafic:carte_trafic_user'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'gestion_trafic/user/carte_trafic_user.html')
    
    def test_mes_alertes_requires_login(self):
        """Test que les alertes nécessitent une authentification"""
        response = self.client.get(reverse('gestion_trafic:mes_alertes'))
        self.assertEqual(response.status_code, 302)
    
    def test_mes_alertes_authenticated(self):
        """Test les alertes pour un utilisateur authentifié"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('gestion_trafic:mes_alertes'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'gestion_trafic/user/mes_alertes.html')
    
    def test_mes_trajets_requires_login(self):
        """Test que les trajets nécessitent une authentification"""
        response = self.client.get(reverse('gestion_trafic:mes_trajets'))
        self.assertEqual(response.status_code, 302)
    
    def test_mes_trajets_authenticated(self):
        """Test les trajets pour un utilisateur authentifié"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('gestion_trafic:mes_trajets'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'gestion_trafic/user/mes_trajets.html')
    
    def test_planifier_trajet_requires_login(self):
        """Test que la planification nécessite une authentification"""
        response = self.client.get(reverse('gestion_trafic:planifier_trajet'))
        self.assertEqual(response.status_code, 302)
    
    def test_planifier_trajet_authenticated(self):
        """Test la planification pour un utilisateur authentifié"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('gestion_trafic:planifier_trajet'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'gestion_trafic/user/planifier_trajet.html')
    
    def test_mes_statistiques_requires_login(self):
        """Test que les statistiques nécessitent une authentification"""
        response = self.client.get(reverse('gestion_trafic:mes_statistiques'))
        self.assertEqual(response.status_code, 302)
    
    def test_mes_statistiques_authenticated(self):
        """Test les statistiques pour un utilisateur authentifié"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('gestion_trafic:mes_statistiques'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'gestion_trafic/user/mes_statistiques.html')
    
    def test_detail_zone_user_requires_login(self):
        """Test que le détail zone nécessite une authentification"""
        response = self.client.get(
            reverse('gestion_trafic:detail_zone_user', args=[self.zone.id])
        )
        self.assertEqual(response.status_code, 302)
    
    def test_detail_zone_user_authenticated(self):
        """Test le détail zone pour un utilisateur authentifié"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('gestion_trafic:detail_zone_user', args=[self.zone.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'gestion_trafic/user/detail_zone_user.html')
    
    def test_ajouter_zone_favorite(self):
        """Test l'ajout d'une zone aux favoris"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('gestion_trafic:ajouter_zone_favorite', args=[self.zone.id])
        )
        # Vérifier que la zone est ajoutée à la session
        self.assertIn('zones_favoris', self.client.session)
    
    def test_retirer_zone_favorite(self):
        """Test le retrait d'une zone des favoris"""
        self.client.login(username='testuser', password='testpass123')
        # D'abord ajouter
        self.client.get(
            reverse('gestion_trafic:ajouter_zone_favorite', args=[self.zone.id])
        )
        # Puis retirer
        response = self.client.get(
            reverse('gestion_trafic:retirer_zone_favorite', args=[self.zone.id])
        )
        # Vérifier que la zone est retirée
        self.assertNotIn(self.zone.id, self.client.session.get('zones_favoris', []))


class UserTrafficAPITestCase(TestCase):
    """Tests pour les API endpoints utilisateur"""
    
    def setUp(self):
        """Initialiser les données de test"""
        self.client = Client()
        
        # Créer un utilisateur de test
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Créer une zone de test
        self.zone = ZoneTrafic.objects.create(
            nom='Zone Test',
            type_zone='centre_ville',
            coordonnees_zone='{"type": "Point", "coordinates": [10.5, 35.8]}',
            vitesse_limite=50,
            nombre_voies=2,
            sens_circulation='Bidirectionnel'
        )
    
    def test_api_trafic_temps_reel_requires_login(self):
        """Test que l'API temps réel nécessite une authentification"""
        response = self.client.get(reverse('gestion_trafic:api_trafic_temps_reel'))
        self.assertEqual(response.status_code, 302)
    
    def test_api_trafic_temps_reel_authenticated(self):
        """Test l'API temps réel pour un utilisateur authentifié"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('gestion_trafic:api_trafic_temps_reel'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('success', data)
    
    def test_api_mes_alertes_requires_login(self):
        """Test que l'API alertes nécessite une authentification"""
        response = self.client.get(reverse('gestion_trafic:api_mes_alertes'))
        self.assertEqual(response.status_code, 302)
    
    def test_api_zones_favoris_requires_login(self):
        """Test que l'API zones favoris nécessite une authentification"""
        response = self.client.get(reverse('gestion_trafic:api_zones_favoris'))
        self.assertEqual(response.status_code, 302)
    
    def test_api_mes_statistiques_requires_login(self):
        """Test que l'API statistiques nécessite une authentification"""
        response = self.client.get(reverse('gestion_trafic:api_mes_statistiques'))
        self.assertEqual(response.status_code, 302)


class UserTrafficDataTestCase(TestCase):
    """Tests pour les données du trafic utilisateur"""
    
    def setUp(self):
        """Initialiser les données de test"""
        # Créer une zone
        self.zone = ZoneTrafic.objects.create(
            nom='Zone Test',
            type_zone='centre_ville',
            coordonnees_zone='{"type": "Point", "coordinates": [10.5, 35.8]}',
            vitesse_limite=50,
            nombre_voies=2,
            sens_circulation='Bidirectionnel'
        )
        
        # Créer un capteur
        self.capteur = CapteurTrafic.objects.create(
            nom='Capteur Test',
            code_capteur='CAP001',
            type_capteur='radar',
            zone_trafic=self.zone,
            latitude=35.8,
            longitude=10.5,
            statut='actif',
            date_installation=timezone.now()
        )
    
    def test_zone_creation(self):
        """Test la création d'une zone"""
        self.assertEqual(self.zone.nom, 'Zone Test')
        self.assertEqual(self.zone.type_zone, 'centre_ville')
        self.assertEqual(self.zone.vitesse_limite, 50)
    
    def test_capteur_creation(self):
        """Test la création d'un capteur"""
        self.assertEqual(self.capteur.nom, 'Capteur Test')
        self.assertEqual(self.capteur.type_capteur, 'radar')
        self.assertEqual(self.capteur.statut, 'actif')
    
    def test_zone_capteurs_relationship(self):
        """Test la relation zone-capteurs"""
        self.assertEqual(self.zone.capteurs.count(), 1)
        self.assertEqual(self.zone.capteurs.first(), self.capteur)

