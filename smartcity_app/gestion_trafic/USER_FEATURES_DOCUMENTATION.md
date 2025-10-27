# 👥 Fonctionnalités Utilisateur - Gestion du Trafic

## 📋 Vue d'Ensemble

Cette documentation décrit les fonctionnalités disponibles pour les utilisateurs normaux dans le module de gestion du trafic.

---

## 🎯 Fonctionnalités Principales

### 1. 📊 Tableau de Bord Personnel
**Route**: `/trafic/user/dashboard/`

Affiche un aperçu personnalisé du trafic avec:
- ✅ Statistiques en temps réel (capteurs actifs, zones actives)
- ✅ Zones congestionnées
- ✅ Événements récents
- ✅ Capteurs proches
- ✅ Actions rapides

**Fichiers**:
- `user_views.py`: `dashboard_user_trafic()`
- `templates/gestion_trafic/user/dashboard_trafic.html`

---

### 2. 🗺️ Carte Interactive
**Route**: `/trafic/user/carte/`

Visualisation interactive du trafic avec:
- ✅ Carte Leaflet.js avec OpenStreetMap
- ✅ Marqueurs des capteurs
- ✅ Codes couleur par niveau de congestion
- ✅ Filtres (Tous, Zones Denses, Favoris, Heatmap)
- ✅ Légende interactive
- ✅ Liste des zones disponibles

**Fichiers**:
- `user_views.py`: `carte_trafic_user()`
- `templates/gestion_trafic/user/carte_trafic_user.html`

---

### 3. 🔔 Alertes Personnalisées
**Route**: `/trafic/user/alertes/`

Gestion des alertes avec:
- ✅ Alertes filtrées par zones favorites
- ✅ Zones congestionnées
- ✅ Filtrage par sévérité, type, statut
- ✅ Statut des alertes (actif/résolu)
- ✅ Conseils de mobilité

**Fichiers**:
- `user_views.py`: `mes_alertes()`
- `templates/gestion_trafic/user/mes_alertes.html`

---

### 4. 🚗 Gestion des Trajets
**Route**: `/trafic/user/trajets/`

Gestion complète des trajets avec:
- ✅ Trajets planifiés
- ✅ Historique des trajets
- ✅ Trajets favoris
- ✅ Statistiques (nombre, durée, etc.)

**Fichiers**:
- `user_views.py`: `mes_trajets()`
- `templates/gestion_trafic/user/mes_trajets.html`

---

### 5. ✏️ Planification de Trajets
**Route**: `/trafic/user/trajets/planifier/`

Planification intelligente avec:
- ✅ Sélection lieu départ/arrivée
- ✅ Heure de départ
- ✅ Critères d'optimisation (temps, coût, écologie, confort, santé, sûreté)
- ✅ Options avancées (budget, durée, accessibilité PMR)
- ✅ Validation du formulaire

**Fichiers**:
- `user_views.py`: `planifier_trajet()`
- `templates/gestion_trafic/user/planifier_trajet.html`

---

### 6. 📈 Statistiques Personnelles
**Route**: `/trafic/user/statistiques/`

Suivi personnel avec:
- ✅ Statistiques des zones favorites
- ✅ Graphiques (trajets par mois, modes de transport)
- ✅ Trajets récents
- ✅ Impact écologique (CO2 économisé)
- ✅ Modes de transport utilisés

**Fichiers**:
- `user_views.py`: `mes_statistiques()`
- `templates/gestion_trafic/user/mes_statistiques.html`

---

### 7. ⭐ Zones Favorites
**Routes**:
- Ajouter: `/trafic/user/zone/<id>/favorite/ajouter/`
- Retirer: `/trafic/user/zone/<id>/favorite/retirer/`

Gestion des zones favorites:
- ✅ Ajouter une zone aux favoris
- ✅ Retirer une zone des favoris
- ✅ Alertes personnalisées pour zones favorites
- ✅ Statistiques des zones favorites

**Fichiers**:
- `user_views.py`: `ajouter_zone_favorite()`, `retirer_zone_favorite()`

---

### 8. 🔍 Détail Zone
**Route**: `/trafic/user/zone/<id>/`

Informations détaillées d'une zone:
- ✅ Caractéristiques (vitesse limite, voies, etc.)
- ✅ Capteurs de la zone
- ✅ Données récentes
- ✅ Événements récents
- ✅ Bouton favoris

**Fichiers**:
- `user_views.py`: `detail_zone_user()`
- `templates/gestion_trafic/user/detail_zone_user.html`

---

## 🔌 API Endpoints Utilisateur

### Données Temps Réel
```
GET /trafic/api/user/trafic-temps-reel/
```
Retourne les données de trafic en temps réel pour les zones favorites.

### Alertes
```
GET /trafic/api/user/mes-alertes/
```
Retourne les alertes personnalisées de l'utilisateur.

### Zones Favorites
```
GET /trafic/api/user/zones-favoris/
```
Retourne la liste des zones favorites.

### Capteurs Proches
```
GET /trafic/api/user/capteurs-proches/
```
Retourne les capteurs proches (basés sur zones favorites).

### Statistiques
```
GET /trafic/api/user/mes-statistiques/
```
Retourne les statistiques personnalisées.

### Détail Zone
```
GET /trafic/api/user/zone/<id>/
```
Retourne les détails d'une zone spécifique.

---

## 📁 Structure des Fichiers

```
smartcity_app/gestion_trafic/
├── user_views.py                    # Vues utilisateur
├── user_api_views.py                # API endpoints utilisateur
├── urls.py                          # Routes (mises à jour)
└── templates/gestion_trafic/user/
    ├── dashboard_trafic.html        # Tableau de bord
    ├── carte_trafic_user.html       # Carte interactive
    ├── mes_alertes.html             # Alertes
    ├── mes_trajets.html             # Trajets
    ├── planifier_trajet.html        # Planification
    ├── mes_statistiques.html        # Statistiques
    └── detail_zone_user.html        # Détail zone
```

---

## 🔐 Permissions

Toutes les vues utilisateur sont protégées par:
- `@login_required` - Authentification requise
- Pas de vérification de rôle - Accessibles à tous les utilisateurs authentifiés

---

## 💾 Stockage des Données

Les données utilisateur sont stockées dans:
- **Session Django**: Zones favorites, trajets planifiés
- **Base de données**: Zones, capteurs, événements, données de trafic

---

## 🎨 Interface Utilisateur

### Couleurs et Codes
- 🟢 **Vert**: Trafic fluide (< 30% congestion)
- 🟡 **Orange**: Trafic ralenti (30-50% congestion)
- 🟠 **Orange foncé**: Trafic dense (50-70% congestion)
- 🔴 **Rouge**: Trafic bloqué (> 70% congestion)

### Icônes
- 📡 Radar
- 📹 Caméra
- ⭐ Zone favorite
- 🔔 Alerte
- 🗺️ Carte
- 📊 Statistiques

---

## 🚀 Utilisation

### Pour les Utilisateurs

1. **Accéder au Dashboard**
   - Cliquer sur "Mon Trafic" dans le menu
   - Voir l'aperçu du trafic en temps réel

2. **Consulter la Carte**
   - Cliquer sur "Voir la Carte"
   - Visualiser le trafic géographiquement
   - Filtrer par type de capteur

3. **Ajouter des Zones Favorites**
   - Cliquer sur "Ajouter aux Favoris" sur une zone
   - Les alertes seront personnalisées

4. **Planifier un Trajet**
   - Cliquer sur "Planifier un Trajet"
   - Remplir le formulaire
   - Sélectionner les critères d'optimisation

5. **Consulter les Statistiques**
   - Cliquer sur "Mes Statistiques"
   - Voir l'impact écologique
   - Analyser les trajets

---

## 📊 Données Affichées

### Tableau de Bord
- Nombre de capteurs actifs
- Nombre de zones actives
- Alertes récentes
- Zones congestionnées
- Événements récents

### Carte
- Marqueurs des capteurs
- Codes couleur par congestion
- Heatmap optionnelle
- Légende interactive

### Alertes
- Type d'événement
- Description
- Sévérité (critique, majeure, mineure)
- Zone affectée
- Statut (actif, résolu)

### Trajets
- Lieu départ/arrivée
- Heure de départ
- Critères d'optimisation
- Statut (planifié, en cours, complété)

### Statistiques
- Trajets planifiés
- Zones favorites
- CO2 économisé
- Modes de transport utilisés
- Graphiques de tendance

---

## 🔄 Flux de Données

```
Utilisateur
    ↓
Vues Utilisateur (user_views.py)
    ↓
API Endpoints (user_api_views.py)
    ↓
Modèles (models.py)
    ↓
Base de Données
```

---

## 📝 Notes

- Les données de trafic sont mises à jour en temps réel
- Les zones favorites sont stockées en session
- Les trajets sont stockés en session (à améliorer avec BD)
- Les alertes sont filtrées par zones favorites
- L'interface est responsive et mobile-friendly

---

## 🎯 Prochaines Améliorations

- [ ] Sauvegarde des trajets en base de données
- [ ] Notifications push pour les alertes
- [ ] Intégration avec les transports en commun
- [ ] Calcul d'itinéraires optimisés
- [ ] Partage de trajets (covoiturage)
- [ ] Système de notation des trajets
- [ ] Historique détaillé des trajets
- [ ] Export des statistiques (PDF, CSV)

---

**Dernière mise à jour**: 2025-10-27  
**Version**: 1.0  
**Statut**: ✅ Opérationnel

