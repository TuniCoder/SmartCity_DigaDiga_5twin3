# 📡 API REST - Gestion du Trafic

Documentation complète des endpoints API pour la gestion du trafic dans SmartCity.

## 🌐 Base URL

```
http://127.0.0.1:8000/trafic/api/
```

## 📋 Table des Matières

1. [Capteurs de Trafic](#capteurs-de-trafic)
2. [Données de Trafic](#données-de-trafic)
3. [Zones de Trafic](#zones-de-trafic)
4. [Feux de Signalisation](#feux-de-signalisation)
5. [Événements de Trafic](#événements-de-trafic)
6. [Statistiques](#statistiques)

---

## 🚨 Capteurs de Trafic

### 1. Lister tous les capteurs

**Endpoint**: `GET /capteurs/`

**Description**: Récupère la liste de tous les capteurs avec filtrage optionnel

**Paramètres de requête**:
- `statut` (optionnel): `actif`, `inactif`, `maintenance`, `defaillant`
- `type_capteur` (optionnel): `boucle_magnetique`, `camera_ia`, `radar`, `lidar`, etc.
- `zone_id` (optionnel): ID de la zone de trafic
- `precision_min` (optionnel): Précision minimale en %

**Exemple de requête**:
```bash
curl -X GET "http://127.0.0.1:8000/trafic/api/capteurs/?statut=actif&precision_min=90"
```

**Réponse (200 OK)**:
```json
{
  "success": true,
  "count": 28,
  "capteurs": [
    {
      "id": 1,
      "nom": "Capteur Centre-1",
      "code_capteur": "CTR-001",
      "type_capteur": "camera_ia",
      "statut": "actif",
      "latitude": 36.8065,
      "longitude": 10.1815,
      "zone_trafic": "Avenue des Champs-Élysées",
      "zone_id": 1,
      "direction_mesure": "Nord-Sud",
      "frequence_mesure": 60,
      "precision_detection": 95.0,
      "vitesse_min_detection": 5,
      "vitesse_max_detection": 200,
      "fournisseur": "TrafficTech Solutions",
      "modele": "TT-CAM-2024",
      "date_installation": "2025-09-26",
      "est_operationnel": true
    }
  ]
}
```

---

### 2. Créer un nouveau capteur

**Endpoint**: `POST /capteurs/`

**Description**: Crée un nouveau capteur et l'ajoute automatiquement au fichier RDF

**Champs obligatoires**:
- `nom`: Nom du capteur
- `code_capteur`: Code unique du capteur
- `type_capteur`: Type de capteur
- `zone_id`: ID de la zone
- `latitude`: Latitude GPS
- `longitude`: Longitude GPS
- `direction_mesure`: Direction mesurée
- `date_installation`: Date d'installation (YYYY-MM-DD)

**Champs optionnels**:
- `frequence_mesure`: Fréquence en secondes (défaut: 60)
- `precision_detection`: Précision en % (défaut: 95.0)
- `vitesse_min_detection`: Vitesse min en km/h (défaut: 5)
- `vitesse_max_detection`: Vitesse max en km/h (défaut: 200)
- `fournisseur`: Nom du fournisseur
- `modele`: Modèle du capteur
- `statut`: Statut initial (défaut: actif)

**Exemple de requête**:
```bash
curl -X POST "http://127.0.0.1:8000/trafic/api/capteurs/" \
  -H "Content-Type: application/json" \
  -d '{
    "nom": "Capteur Test API",
    "code_capteur": "API-TEST-001",
    "type_capteur": "camera_ia",
    "zone_id": 1,
    "latitude": 36.8070,
    "longitude": 10.1820,
    "direction_mesure": "Est-Ouest",
    "date_installation": "2025-10-27",
    "frequence_mesure": 60,
    "precision_detection": 97.5,
    "fournisseur": "SmartCity API",
    "modele": "SC-API-2025"
  }'
```

**Réponse (201 Created)**:
```json
{
  "success": true,
  "message": "Capteur créé avec succès",
  "capteur_id": 29,
  "capteur": {
    "id": 29,
    "nom": "Capteur Test API",
    "code_capteur": "API-TEST-001"
  }
}
```

---

### 3. Détails d'un capteur

**Endpoint**: `GET /capteurs/{capteur_id}/`

**Exemple**:
```bash
curl -X GET "http://127.0.0.1:8000/trafic/api/capteurs/1/"
```

---

### 4. Modifier un capteur

**Endpoint**: `PUT /capteurs/{capteur_id}/`

**Champs modifiables**:
- `nom`
- `statut`
- `precision_detection`
- `frequence_mesure`

**Exemple**:
```bash
curl -X PUT "http://127.0.0.1:8000/trafic/api/capteurs/1/" \
  -H "Content-Type: application/json" \
  -d '{
    "statut": "maintenance",
    "precision_detection": 92.5
  }'
```

---

### 5. Supprimer un capteur

**Endpoint**: `DELETE /capteurs/{capteur_id}/`

```bash
curl -X DELETE "http://127.0.0.1:8000/trafic/api/capteurs/1/"
```

---

## 📊 Données de Trafic

### 1. Récupérer les données de trafic

**Endpoint**: `GET /donnees/`

**Paramètres**:
- `capteur_id` (optionnel): Filtrer par capteur
- `zone_id` (optionnel): Filtrer par zone
- `heures` (optionnel): Nombre d'heures à récupérer (défaut: 24)
- `niveau_congestion` (optionnel): `fluide`, `dense`, `ralenti`, `bouchon`, `bloque`

**Exemple**:
```bash
curl -X GET "http://127.0.0.1:8000/trafic/api/donnees/?zone_id=1&heures=12&niveau_congestion=dense"
```

**Réponse**:
```json
{
  "success": true,
  "count": 150,
  "donnees": [
    {
      "id": 1,
      "capteur": "Capteur Centre-1",
      "capteur_id": 1,
      "timestamp": "2025-10-27T14:30:00Z",
      "nombre_vehicules": 45,
      "vitesse_moyenne": 35.5,
      "vitesse_mediane": 38.0,
      "debit_vehicules": 2700,
      "niveau_congestion": "dense",
      "taux_occupation": 75.5,
      "vehicules_legers": 38,
      "vehicules_lourds": 5,
      "deux_roues": 2,
      "transports_publics": 0,
      "incident_detecte": false,
      "type_incident": "",
      "conditions_meteo": "Ensoleillé",
      "temperature": 22.5
    }
  ]
}
```

---

### 2. Enregistrer de nouvelles données

**Endpoint**: `POST /donnees/`

**Champs obligatoires**:
- `capteur_id`: ID du capteur
- `timestamp`: Horodatage (ISO 8601)
- `nombre_vehicules`: Nombre de véhicules
- `niveau_congestion`: Niveau de congestion
- `taux_occupation`: Taux d'occupation (0-100)

**Exemple**:
```bash
curl -X POST "http://127.0.0.1:8000/trafic/api/donnees/" \
  -H "Content-Type: application/json" \
  -d '{
    "capteur_id": 1,
    "timestamp": "2025-10-27T15:00:00Z",
    "nombre_vehicules": 52,
    "vitesse_moyenne": 38.5,
    "vitesse_mediane": 40.0,
    "debit_vehicules": 3120,
    "vehicules_legers": 45,
    "vehicules_lourds": 4,
    "deux_roues": 3,
    "transports_publics": 0,
    "niveau_congestion": "dense",
    "taux_occupation": 82.0,
    "conditions_meteo": "Ensoleillé",
    "temperature": 23.0,
    "incident_detecte": false
  }'
```

---

## 📍 Zones de Trafic

### Lister les zones

**Endpoint**: `GET /zones/`

```bash
curl -X GET "http://127.0.0.1:8000/trafic/api/zones/"
```

**Réponse**:
```json
{
  "success": true,
  "count": 7,
  "zones": [
    {
      "id": 1,
      "nom": "Avenue des Champs-Élysées",
      "type_zone": "centre_ville",
      "vitesse_limite": 50,
      "nombre_voies": 4,
      "nombre_capteurs": 19,
      "capteurs_actifs": 18,
      "zone_pietons": false
    }
  ]
}
```

---

## 🚦 Feux de Signalisation

### Lister les feux

**Endpoint**: `GET /feux/`

**Paramètres**:
- `zone_id` (optionnel): Filtrer par zone

```bash
curl -X GET "http://127.0.0.1:8000/trafic/api/feux/?zone_id=1"
```

---

## 📢 Événements de Trafic

### Lister les événements

**Endpoint**: `GET /evenements/`

**Paramètres**:
- `statut` (optionnel): `prevu`, `en_cours`, `termine`, `annule` (défaut: `en_cours`)

```bash
curl -X GET "http://127.0.0.1:8000/trafic/api/evenements/?statut=en_cours"
```

---

## 📈 Statistiques

### Récupérer les statistiques

**Endpoint**: `GET /statistiques/`

**Paramètres**:
- `zone_id` (optionnel): Filtrer par zone
- `heures` (optionnel): Nombre d'heures (défaut: 24)

```bash
curl -X GET "http://127.0.0.1:8000/trafic/api/statistiques/?heures=24"
```

**Réponse**:
```json
{
  "success": true,
  "periode_heures": 24,
  "statistiques": {
    "total_mesures": 1440,
    "vitesse_moyenne_globale": 42.3,
    "vitesse_max": 85.5,
    "vitesse_min": 5.2,
    "taux_occupation_moyen": 68.5,
    "incidents_detectes": 3,
    "distribution_congestion": {
      "fluide": 480,
      "dense": 600,
      "ralenti": 300,
      "bouchon": 60
    },
    "capteurs_actifs": 27,
    "capteurs_total": 28
  }
}
```

---

## 🔐 Authentification

Actuellement, tous les endpoints sont accessibles sans authentification (`AllowAny`).

Pour ajouter une authentification, modifier les `permission_classes` dans `api_views.py`.

---

## 📝 Codes d'Erreur

| Code | Signification |
|------|---------------|
| 200 | OK - Requête réussie |
| 201 | Created - Ressource créée |
| 204 | No Content - Suppression réussie |
| 400 | Bad Request - Erreur dans les paramètres |
| 404 | Not Found - Ressource non trouvée |
| 500 | Server Error - Erreur serveur |

---

## 🧪 Tests avec Postman

Importez cette collection Postman pour tester les API:

```json
{
  "info": {
    "name": "SmartCity Trafic API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Lister les capteurs",
      "request": {
        "method": "GET",
        "url": "http://127.0.0.1:8000/trafic/api/capteurs/"
      }
    },
    {
      "name": "Créer un capteur",
      "request": {
        "method": "POST",
        "url": "http://127.0.0.1:8000/trafic/api/capteurs/",
        "body": {
          "mode": "raw",
          "raw": "{\"nom\": \"Test\", \"code_capteur\": \"TEST-001\", ...}"
        }
      }
    }
  ]
}
```

---

**Dernière mise à jour**: 27 octobre 2025  
**Version API**: 1.0

