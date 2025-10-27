# 📊 Requêtes SPARQL - Gestion du Trafic

Ce document décrit toutes les requêtes SPARQL disponibles pour la gestion du trafic dans le système SmartCity.

## 🎯 Vue d'ensemble

Les requêtes SPARQL pour la gestion du trafic permettent de :
- Interroger les capteurs de trafic
- Analyser la couverture des zones
- Filtrer par statut, type, fournisseur
- Obtenir des statistiques et agrégations
- Localiser les capteurs par zone géographique

## 📋 Requêtes Disponibles

### 1. **Tous les capteurs de trafic**
**ID**: `all_traffic_sensors`

Liste tous les capteurs de trafic avec leurs informations de base.

```sparql
SELECT ?capteur ?nom ?code ?type ?statut ?latitude ?longitude ?zone
WHERE {
    ?capteur rdf:type mobility:CapteurTrafic .
    OPTIONAL { ?capteur mobility:nomCapteur ?nom }
    OPTIONAL { ?capteur mobility:codeCapteur ?code }
    OPTIONAL { ?capteur mobility:typeCapteur ?type }
    OPTIONAL { ?capteur mobility:statutCapteur ?statut }
    OPTIONAL { ?capteur mobility:latitude ?latitude }
    OPTIONAL { ?capteur mobility:longitude ?longitude }
    OPTIONAL { ?capteur mobility:zoneTrafic ?zone }
}
ORDER BY ?nom
```

**Résultats**: Tous les capteurs avec leurs propriétés principales

---

### 2. **Capteurs de trafic actifs**
**ID**: `active_traffic_sensors`

Liste uniquement les capteurs avec statut "actif".

```sparql
SELECT ?capteur ?nom ?code ?type ?latitude ?longitude ?frequence
WHERE {
    ?capteur rdf:type mobility:CapteurTrafic .
    ?capteur mobility:statutCapteur "actif" .
    OPTIONAL { ?capteur mobility:nomCapteur ?nom }
    OPTIONAL { ?capteur mobility:codeCapteur ?code }
    OPTIONAL { ?capteur mobility:typeCapteur ?type }
    OPTIONAL { ?capteur mobility:latitude ?latitude }
    OPTIONAL { ?capteur mobility:longitude ?longitude }
    OPTIONAL { ?capteur mobility:frequenceMesure ?frequence }
}
ORDER BY ?nom
```

**Résultats**: Capteurs actifs avec fréquence de mesure

---

### 3. **Capteurs par type**
**ID**: `traffic_sensors_by_type`

Compte les capteurs groupés par type.

```sparql
SELECT ?type (COUNT(?capteur) as ?count)
WHERE {
    ?capteur rdf:type mobility:CapteurTrafic .
    ?capteur mobility:typeCapteur ?type .
}
GROUP BY ?type
ORDER BY DESC(?count)
```

**Résultats**: Nombre de capteurs par type (caméra, boucle, radar, etc.)

---

### 4. **Capteurs par zone**
**ID**: `traffic_sensors_by_zone`

Liste les capteurs groupés par zone de trafic.

```sparql
SELECT ?zone (COUNT(?capteur) as ?count) (GROUP_CONCAT(?nom; separator=", ") as ?capteurs)
WHERE {
    ?capteur rdf:type mobility:CapteurTrafic .
    ?capteur mobility:zoneTrafic ?zone .
    OPTIONAL { ?capteur mobility:nomCapteur ?nom }
}
GROUP BY ?zone
ORDER BY DESC(?count)
```

**Résultats**: Zones avec nombre de capteurs et liste des noms

---

### 5. **Couverture des capteurs**
**ID**: `traffic_sensors_coverage`

Affiche la couverture en capteurs par zone avec précision moyenne.

```sparql
SELECT ?zone (COUNT(?capteur) as ?nombreCapteurs) (AVG(?precision) as ?precisionMoyenne)
WHERE {
    ?capteur rdf:type mobility:CapteurTrafic .
    ?capteur mobility:zoneTrafic ?zone .
    OPTIONAL { ?capteur mobility:precisionDetection ?precision }
}
GROUP BY ?zone
ORDER BY DESC(?nombreCapteurs)
```

**Résultats**: Zones avec nombre de capteurs et précision moyenne

---

### 6. **Capteurs haute précision**
**ID**: `high_precision_sensors`

Liste les capteurs avec précision > 90%.

```sparql
SELECT ?capteur ?nom ?type ?precision ?zone
WHERE {
    ?capteur rdf:type mobility:CapteurTrafic .
    ?capteur mobility:precisionDetection ?precision .
    FILTER(?precision > 90) .
    OPTIONAL { ?capteur mobility:nomCapteur ?nom }
    OPTIONAL { ?capteur mobility:typeCapteur ?type }
    OPTIONAL { ?capteur mobility:zoneTrafic ?zone }
}
ORDER BY DESC(?precision)
```

**Résultats**: Capteurs fiables avec haute précision

---

### 7. **Détails complets des capteurs**
**ID**: `traffic_sensors_with_details`

Affiche tous les détails de chaque capteur.

```sparql
SELECT ?capteur ?nom ?code ?type ?statut ?latitude ?longitude ?direction ?frequence ?precision ?vitesseMin ?vitesseMax ?fournisseur ?modele ?zone ?dateInstallation
WHERE {
    ?capteur rdf:type mobility:CapteurTrafic .
    OPTIONAL { ?capteur mobility:nomCapteur ?nom }
    OPTIONAL { ?capteur mobility:codeCapteur ?code }
    OPTIONAL { ?capteur mobility:typeCapteur ?type }
    OPTIONAL { ?capteur mobility:statutCapteur ?statut }
    OPTIONAL { ?capteur mobility:latitude ?latitude }
    OPTIONAL { ?capteur mobility:longitude ?longitude }
    OPTIONAL { ?capteur mobility:directionMesure ?direction }
    OPTIONAL { ?capteur mobility:frequenceMesure ?frequence }
    OPTIONAL { ?capteur mobility:precisionDetection ?precision }
    OPTIONAL { ?capteur mobility:vitesseMinDetection ?vitesseMin }
    OPTIONAL { ?capteur mobility:vitesseMaxDetection ?vitesseMax }
    OPTIONAL { ?capteur mobility:fournisseur ?fournisseur }
    OPTIONAL { ?capteur mobility:modele ?modele }
    OPTIONAL { ?capteur mobility:zoneTrafic ?zone }
    OPTIONAL { ?capteur mobility:dateInstallation ?dateInstallation }
}
ORDER BY ?nom
```

**Résultats**: Tous les détails de chaque capteur

---

### 8. **Capteurs par fournisseur**
**ID**: `traffic_sensors_by_provider`

Liste les capteurs groupés par fournisseur.

```sparql
SELECT ?fournisseur (COUNT(?capteur) as ?count) (GROUP_CONCAT(?nom; separator=", ") as ?capteurs)
WHERE {
    ?capteur rdf:type mobility:CapteurTrafic .
    ?capteur mobility:fournisseur ?fournisseur .
    OPTIONAL { ?capteur mobility:nomCapteur ?nom }
}
GROUP BY ?fournisseur
ORDER BY DESC(?count)
```

**Résultats**: Fournisseurs avec nombre de capteurs

---

### 9. **Capteurs par modèle**
**ID**: `traffic_sensors_by_model`

Liste les capteurs groupés par modèle.

```sparql
SELECT ?modele (COUNT(?capteur) as ?count) ?fournisseur
WHERE {
    ?capteur rdf:type mobility:CapteurTrafic .
    ?capteur mobility:modele ?modele .
    OPTIONAL { ?capteur mobility:fournisseur ?fournisseur }
}
GROUP BY ?modele ?fournisseur
ORDER BY DESC(?count)
```

**Résultats**: Modèles avec nombre de capteurs et fournisseur

---

### 10. **Plages de vitesse des capteurs**
**ID**: `traffic_sensors_speed_range`

Affiche les plages de vitesse min/max détectées.

```sparql
SELECT ?capteur ?nom ?vitesseMin ?vitesseMax ?type
WHERE {
    ?capteur rdf:type mobility:CapteurTrafic .
    ?capteur mobility:vitesseMinDetection ?vitesseMin .
    ?capteur mobility:vitesseMaxDetection ?vitesseMax .
    OPTIONAL { ?capteur mobility:nomCapteur ?nom }
    OPTIONAL { ?capteur mobility:typeCapteur ?type }
}
ORDER BY ?vitesseMin
```

**Résultats**: Capteurs avec leurs plages de vitesse

---

## 🔍 Utilisation

### Via l'interface web
1. Accédez à http://127.0.0.1:8000/query/
2. Sélectionnez l'onglet "Requêtes Prédéfinies"
3. Choisissez une requête de gestion du trafic
4. Cliquez sur "Exécuter"

### Via l'API
```bash
POST /api/sparql/
Content-Type: application/json

{
    "query": "SELECT ?capteur ?nom WHERE { ?capteur rdf:type mobility:CapteurTrafic . OPTIONAL { ?capteur mobility:nomCapteur ?nom } }"
}
```

### En langage naturel
```
"Affiche tous les capteurs de trafic actifs"
"Combien de capteurs par zone?"
"Quels sont les capteurs haute précision?"
"Liste les capteurs par fournisseur"
```

## 📊 Préfixes SPARQL

```sparql
PREFIX mobility: <http://example.org/mobility-ontology/2025/09#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
```

## 🎓 Exemples de Requêtes Personnalisées

### Capteurs inactifs
```sparql
SELECT ?capteur ?nom ?zone
WHERE {
    ?capteur rdf:type mobility:CapteurTrafic .
    ?capteur mobility:statutCapteur "inactif" .
    OPTIONAL { ?capteur mobility:nomCapteur ?nom }
    OPTIONAL { ?capteur mobility:zoneTrafic ?zone }
}
```

### Capteurs avec basse précision
```sparql
SELECT ?capteur ?nom ?precision
WHERE {
    ?capteur rdf:type mobility:CapteurTrafic .
    ?capteur mobility:precisionDetection ?precision .
    FILTER(?precision < 80) .
    OPTIONAL { ?capteur mobility:nomCapteur ?nom }
}
ORDER BY ?precision
```

### Capteurs installés récemment
```sparql
SELECT ?capteur ?nom ?dateInstallation
WHERE {
    ?capteur rdf:type mobility:CapteurTrafic .
    ?capteur mobility:dateInstallation ?dateInstallation .
    OPTIONAL { ?capteur mobility:nomCapteur ?nom }
}
ORDER BY DESC(?dateInstallation)
LIMIT 10
```

---

**Dernière mise à jour**: 27 octobre 2025  
**Version**: 1.0

