# 🏙️ SmartCity Project - Plateforme IA de Mobilité Urbaine

## 🎯 Vue d'ensemble

SmartCity Project est une **plateforme intelligente de mobilité urbaine** développée avec Django qui combine **Intelligence Artificielle**, **données sémantiques** et **optimisation temps réel** pour révolutionner les déplacements en ville.

### ✨ **Fonctionnalités Principales**
- 🧠 **Planificateur IA** : Recommandations intelligentes multi-critères
- 🌍 **Optimisation écologique** : Réduction empreinte carbone
- ⏱️ **Temps réel** : Données live de trafic et transport
- 🔄 **Multimodal** : Bus, métro, vélo, marche combinés
- 📊 **Analytics** : Tableaux de bord et métriques avancées

## 🚀 **État Actuel - Prêt pour l'Équipe**

### ✅ **OPÉRATIONNEL** (1/6 modules)
- **🚗 Gestion des Trajets** - Planificateur IA complet avec interface moderne

### 🚧 **PRÊT DÉVELOPPEMENT** (5/6 modules)  
- **🚉 Gestion des Stations** - Infrastructure + cartes interactives
- **🚦 Gestion du Trafic** - IA prédictive + optimisation temps réel
- **🚗 Gestion des Véhicules** - IoT + GPS + maintenance prédictive
- **🔌 API Manager** - Gateway central + portail développeur  
- **🌐 Ontology Manager** - Données sémantiques RDF/SPARQL

## 👥 **Pour l'Équipe - Démarrage Rapide**

### **🚀 Démarrage Rapide pour Développeurs**
```bash
# 1. Installation (15 minutes)
git clone [repo]
cd smartcity_project
pip install -r requirements.txt

# 2. Configuration base de données
python manage.py migrate

# 3. Données de test et démonstration
python init_users.py                    # Comptes admin/user
python init_planificateur_ia.py         # Données IA et véhicules

# 4. Lancement
python manage.py runserver
# ➜ http://127.0.0.1:8000/

# 5. Test des interfaces
# http://127.0.0.1:8000/entities/      # Données ontologie
# http://127.0.0.1:8000/query/        # Requêtes IA
# http://127.0.0.1:8000/trajets/      # Module complet
```

### **📋 Documentation Équipe**
- 📄 Consultez les README.md dans chaque module pour les détails techniques
- 📊 Chaque module a sa propre documentation de développement  
- 👥 Coordination via issues GitHub et discussions d'équipe
- 🎯 Utilisez les interfaces web pour tester les fonctionnalités

### **🛠️ Scripts d'Initialisation**
```bash
# Initialisation des données de base
python init_users.py                   # Créer utilisateurs admin/test
python init_planificateur_ia.py        # Données de démonstration IA

# Gestion Django
python manage.py migrate               # Base de données
python manage.py runserver             # Démarrer le serveur
```

## 🏗️ **Architecture Modulaire**

### Structure Technique
```
smartcity_project/
├── manage.py                           # Script de gestion Django
├── ontology/
│   └── mobility_ontology_clean.rdf     # Ontologie RDF de mobilité
├── smartcity_core/                     # Configuration Django
│   ├── __init__.py
│   ├── settings.py                     # Paramètres de l'application
│   ├── urls.py                         # Routage principal
│   └── wsgi.py                         # Configuration WSGI
└── smartcity_app/                      # Application principale
    ├── __init__.py
    ├── models.py                       # Modèles Django
    ├── urls.py                         # Routage de l'application
    ├── ontology_manager/               # 🔧 Gestion des ontologies
    │   ├── __init__.py
    │   └── rdf_utils.py               # Utilitaires RDF/SPARQL
    ├── ia_manager/                     # 🧠 Intelligence artificielle
    │   ├── __init__.py
    │   └── ai_api.py                  # Traitement IA des requêtes
    ├── api_manager/                    # 🌐 API REST
    │   ├── __init__.py
    │   └── api_views.py               # Endpoints API
    ├── views_manager/                  # 👁️ Gestion des vues
    │   ├── __init__.py
    │   └── views_main.py              # Vues principales
    ├── static/                         # Ressources statiques
    │   ├── css/
    │   │   └── smartcity.css          # Styles personnalisés
    │   └── js/
    │       └── visualization.js        # Bibliothèque de visualisation
    └── templates/                      # Templates HTML
        ├── base.html                  # Template de base
        ├── index.html                 # Page d'accueil
        ├── ontology_view.html         # Visualisation ontologie
        ├── query.html                 # Interface de requêtes
        ├── entities_list.html         # Liste des entités
        └── search.html                # Interface de recherche
```

## 🚀 Installation et Configuration

### Prérequis
- Python 3.8+
- Django 4.2+
- Git (optionnel)

### Installation
1. **Créer un environnement virtuel** (recommandé)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

2. **Installer les dépendances**
```powershell
pip install -r requirements.txt
```

3. **Configurer la base de données**
```powershell
python manage.py makemigrations
python manage.py migrate
```

4. **Créer un superutilisateur** (optionnel)
```powershell
python manage.py createsuperuser
```

5. **Démarrer le serveur de développement**
```powershell
python manage.py runserver
```

6. **Initialiser les données de test** (optionnel)
```powershell
# Créer utilisateurs admin/test
python init_users.py

# Initialiser données IA et véhicules  
python init_planificateur_ia.py
```

L'application sera accessible à l'adresse : http://localhost:8000

## 💡 Fonctionnalités Principales

### 🔍 Requêtes en Langage Naturel
- Interface conversationnelle pour interroger l'ontologie
- Traitement automatique des questions en français
- Conversion intelligent vers des requêtes SPARQL

### 📊 Visualisation des Données
- Graphiques interactifs avec Chart.js
- Exploration visuelle de l'ontologie
- Export des données en différents formats

### 🌐 API REST Complète
- Endpoints pour toutes les fonctionnalités
- Documentation automatique des API
- Support CORS pour intégrations externes

### 🎨 Interface Responsive
- Design moderne avec Bootstrap 5
- Interface adaptative mobile/desktop
- Thème personnalisé SmartCity

## 📖 Guide d'Utilisation

### Page d'Accueil
- Vue d'ensemble du système
- Statistiques en temps réel
- Navigation vers les différents modules

### Interface de Requêtes (/query/)
Posez des questions en français comme :
- "Quels sont les types de véhicules disponibles ?"
- "Montrez-moi les stations de métro"
- "Combien y a-t-il de modes de transport ?"

### Exploration de l'Ontologie (/ontology/)
- Visualisation des classes et propriétés
- Navigation dans la hiérarchie
- Détails des relations sémantiques

### Liste des Entités (/entities/)
- Exploration par type d'entité
- Recherche et filtrage
- Détails des instances

## 🔧 API Endpoints

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/ask/` | POST | Requête IA en langage naturel |
| `/api/sparql/` | POST | Exécution directe SPARQL |
| `/api/entities/` | GET | Liste toutes les entités |
| `/api/entities/<type>/` | GET | Entités par type |
| `/api/classes/` | GET | Classes de l'ontologie |
| `/api/properties/` | GET | Propriétés de l'ontologie |
| `/api/search/` | GET | Recherche d'entités |
| `/api/statistics/` | GET | Statistiques du système |

## 🧪 Tests et Qualité

### Exécuter les tests
```powershell
pytest
python manage.py test
```

### Vérification de la qualité du code
```powershell
black .
flake8 .
```

### Génération de la documentation
```powershell
cd docs
make html
```

## 🚀 Déploiement

### Développement
Le projet est configuré pour le développement local avec SQLite.

### Production
Pour un déploiement en production :

1. **Variables d'environnement**
```bash
export DJANGO_SETTINGS_MODULE=smartcity_core.settings
export DEBUG=False
export DATABASE_URL=postgresql://user:pass@localhost/smartcity
```

2. **Base de données PostgreSQL**
```powershell
pip install psycopg2-binary
python manage.py migrate
```

3. **Collecte des fichiers statiques**
```powershell
python manage.py collectstatic
```

4. **Serveur WSGI** (Gunicorn recommandé)
```powershell
pip install gunicorn
gunicorn smartcity_core.wsgi:application
```

## 👥 **Attribution des Modules pour l'Équipe**

### **🚀 Modules Prêts pour Développement**

Chaque module peut être développé indépendamment par un membre de l'équipe :

1. **🚉 Gestion des Stations** (`/stations/`)
   - Interface de gestion des arrêts et stations
   - Géolocalisation et services
   - APIs REST pour les données stations

2. **🚦 Gestion du Trafic** (`/trafic/`)
   - Monitoring du trafic en temps réel
   - Données de circulation et analyse
   - Prédictions et optimisations

3. **🚗 Gestion des Véhicules** (`/vehicules/`)
   - Catalogue des types de véhicules
   - Caractéristiques et maintenance
   - Intégration IoT et tracking

4. **👥 Gestion des Utilisateurs** (`/utilisateurs/`)
   - Profils et authentification
   - Préférences personnalisées
   - Système de rôles et permissions

5. **🔌 API Manager** (`/api/`)
   - Gateway central pour toutes les APIs
   - Documentation automatique
   - Gestion des accès et rate limiting

### **📁 Structure par Module**
Chaque module contient :
- `models.py` - Modèles de données Django
- `views.py` - Logique métier et vues
- `urls.py` - Routage du module  
- `README.md` - Documentation spécifique
- `templates/` - Interfaces utilisateur

## 📚 Technologies Utilisées

### Backend
- **Django 4.2+** - Framework web Python
- **RDFlib 6.3+** - Traitement des données RDF
- **SPARQLWrapper** - Exécution de requêtes SPARQL
- **NLTK & spaCy** - Traitement du langage naturel
- **Django REST Framework** - API REST

### Frontend
- **Bootstrap 5.3** - Framework CSS
- **Chart.js** - Visualisation de données
- **Font Awesome** - Icônes
- **JavaScript ES6+** - Interactivité

### Base de données
- **SQLite** - Développement
- **PostgreSQL** - Production (recommandé)

### Outils de développement
- **pytest** - Tests unitaires
- **Black** - Formatage du code
- **Flake8** - Analyse statique
- **Sphinx** - Documentation

## 🐛 Résolution de Problèmes

### Problèmes courants

**Erreur d'importation RDF ou ontologie**
```powershell
# Vérifiez que le fichier RDF existe
ls ontology/mobility_ontology_clean.rdf

# Test du gestionnaire RDF
python manage.py shell
>>> from smartcity_app.ontology_manager.rdf_utils import rdf_manager
>>> rdf_manager.load_ontology()
True
```

**Erreurs de base de données**
```powershell
# Réinitialisez la base de données
rm db.sqlite3
python manage.py migrate
```

**Problèmes de dépendances**
```powershell
# Réinstallez les requirements
pip install -r requirements.txt --upgrade
```

## 📄 Licence

Ce projet est développé dans un cadre académique pour l'apprentissage des technologies du web sémantique et de l'intelligence artificielle appliquées à la mobilité urbaine.

## 🤝 Contribution et Développement en Équipe

### **🔄 Workflow de Développement**
1. **Choix du module** : Sélectionnez un module non assigné
2. **Lecture de la doc** : Consultez le `README.md` du module
3. **Test de l'existant** : Visitez l'URL du module pour voir l'état actuel
4. **Développement** : Implémentez les fonctionnalités manquantes
5. **Integration** : Testez avec les autres modules

### **📝 Standards de Code**
- Suivre la structure Django existante
- Documenter les nouvelles fonctionnalités
- Tester les APIs avec les endpoints existants
- Maintenir la cohérence visuelle (Bootstrap + CSS custom)

### **🔗 Points d'Intégration**
- **Authentification** : Utiliser le système de rôles existant
- **Ontologie** : Intégrer avec `rdf_utils.py` pour les données sémantiques  
- **Templates** : Étendre `base.html` pour la cohérence UI
- **APIs** : Suivre la structure REST existante

Pour contribuer au projet :
1. Forkez le repository
2. Créez une branche pour votre module
3. Développez en suivant les standards
4. Testez l'intégration avec les autres modules
5. Créez une Pull Request avec documentation

## 📞 Contact et Support

Pour toute question ou support :
- Consultez la documentation dans le code
- Vérifiez les logs Django pour les erreurs
- Utilisez l'interface d'administration Django : /admin/

---

**SmartCity Project** - Plateforme Sémantique de Mobilité Urbaine  
Développé avec ❤️ pour l'apprentissage du web sémantique et de l'IA