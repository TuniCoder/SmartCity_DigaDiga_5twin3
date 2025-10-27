"""
Module fournissant des requêtes SPARQL réutilisables pour la gestion des locations.

Ce fichier est importé par `smartcity_app.ia_manager.ai_api` qui s'attend à trouver
un dictionnaire `SPARQL_QUERIES` contenant des entrées comme :
  - active_locations
  - user_locations_details
  - all_locations
  - user_locations
  - location_details
  - locations_by_vehicle
  - locations_by_date_range

Les requêtes ci-dessous sont des requêtes raisonnables basées sur l'ontologie
présente dans le projet. Elles peuvent être adaptées si votre ontologie utilise
des prédicats différents.
"""

SPARQL_QUERIES = {
    "active_locations": {
        "name": "Locations actives",
        "description": "Liste des locations actuellement actives",
        "query": """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX mobility: <http://example.org/mobility-ontology/2025/09#>

        SELECT DISTINCT ?location ?numero ?statut ?dateDebut ?dateFin ?conducteur ?prix
        WHERE {
            ?location rdf:type mobility:Location .
            OPTIONAL { ?location mobility:numeroLocation ?numero }
            OPTIONAL { ?location mobility:statutLocation ?statut }
            OPTIONAL { ?location mobility:dateDebutLocation ?dateDebut }
            OPTIONAL { ?location mobility:dateFinLocation ?dateFin }
            OPTIONAL { ?location mobility:conducteurPrincipal ?conducteur }
            OPTIONAL { ?location mobility:prixTotalCalcule ?prix }
            FILTER(bound(?statut) && (?statut = "en_cours" || ?statut = "active" || ?statut = "en cours"))
        }
        ORDER BY ?dateDebut
        LIMIT 100
        """
    },

    "user_locations_details": {
        "name": "Détails des locations par utilisateur",
        "description": "Récupère les locations et les détails pour chaque utilisateur",
        "query": """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX mobility: <http://example.org/mobility-ontology/2025/09#>

        SELECT DISTINCT ?location ?numero ?statut ?dateDebut ?dateFin ?lieuPrise ?lieuRetour ?conducteur ?prix
        WHERE {
            ?location rdf:type mobility:Location .
            OPTIONAL { ?location mobility:numeroLocation ?numero }
            OPTIONAL { ?location mobility:statutLocation ?statut }
            OPTIONAL { ?location mobility:dateDebutLocation ?dateDebut }
            OPTIONAL { ?location mobility:dateFinLocation ?dateFin }
            OPTIONAL { ?location mobility:lieuPrise ?lieuPrise }
            OPTIONAL { ?location mobility:lieuRetour ?lieuRetour }
            OPTIONAL { ?location mobility:conducteurPrincipal ?conducteur }
            OPTIONAL { ?location mobility:prixTotalCalcule ?prix }
        }
        ORDER BY ?conducteur
        """
    },

    "all_locations": {
        "name": "Toutes les locations",
        "description": "Liste complète des locations avec informations de base",
        "query": """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX mobility: <http://example.org/mobility-ontology/2025/09#>

        SELECT DISTINCT ?location ?numero ?statut ?type ?dateDebut ?dateFin ?lieuPrise ?lieuRetour ?conducteur ?prix
        WHERE {
            ?location rdf:type mobility:Location .
            OPTIONAL { ?location mobility:numeroLocation ?numero }
            OPTIONAL { ?location mobility:statutLocation ?statut }
            OPTIONAL { ?location mobility:typeLocation ?type }
            OPTIONAL { ?location mobility:dateDebutLocation ?dateDebut }
            OPTIONAL { ?location mobility:dateFinLocation ?dateFin }
            OPTIONAL { ?location mobility:lieuPrise ?lieuPrise }
            OPTIONAL { ?location mobility:lieuRetour ?lieuRetour }
            OPTIONAL { ?location mobility:conducteurPrincipal ?conducteur }
            OPTIONAL { ?location mobility:prixTotalCalcule ?prix }
        }
        ORDER BY DESC(?dateDebut)
        """
    },

    "user_locations": {
        "name": "Locations par utilisateur",
        "description": "Liste des locations associées à un utilisateur",
        "query": """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX mobility: <http://example.org/mobility-ontology/2025/09#>

        SELECT DISTINCT ?location ?numero ?statut ?conducteur ?dateDebut ?prix
        WHERE {
            ?location rdf:type mobility:Location .
            ?location mobility:conducteurPrincipal ?conducteur .
            OPTIONAL { ?location mobility:numeroLocation ?numero }
            OPTIONAL { ?location mobility:statutLocation ?statut }
            OPTIONAL { ?location mobility:dateDebutLocation ?dateDebut }
            OPTIONAL { ?location mobility:prixTotalCalcule ?prix }
        }
        ORDER BY ?conducteur
        """
    },

    "location_details": {
        "name": "Détails d'une location",
        "description": "Informations détaillées pour une location donnée (à filtrer par URI de location)",
        "query": """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX mobility: <http://example.org/mobility-ontology/2025/09#>

        SELECT ?location ?numero ?statut ?type ?dateDebut ?dateFin ?lieuPrise ?lieuRetour ?conducteur ?prix ?vehicule
        WHERE {
            ?location rdf:type mobility:Location .
            OPTIONAL { ?location mobility:numeroLocation ?numero }
            OPTIONAL { ?location mobility:statutLocation ?statut }
            OPTIONAL { ?location mobility:typeLocation ?type }
            OPTIONAL { ?location mobility:dateDebutLocation ?dateDebut }
            OPTIONAL { ?location mobility:dateFinLocation ?dateFin }
            OPTIONAL { ?location mobility:lieuPrise ?lieuPrise }
            OPTIONAL { ?location mobility:lieuRetour ?lieuRetour }
            OPTIONAL { ?location mobility:conducteurPrincipal ?conducteur }
            OPTIONAL { ?location mobility:prixTotalCalcule ?prix }
            OPTIONAL { ?location mobility:vehiculeUtilise ?vehicule }
            FILTER(str(?location) = ?LOCATION_URI)
        }
        LIMIT 1
        """
    },

    "locations_by_vehicle": {
        "name": "Locations par véhicule",
        "description": "Récupère les locations groupées par véhicule",
        "query": """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX mobility: <http://example.org/mobility-ontology/2025/09#>

        SELECT DISTINCT ?vehicule ?vehiculeNom ?location ?numero ?dateDebut ?dateFin
        WHERE {
            ?location rdf:type mobility:Location .
            OPTIONAL { ?location mobility:vehiculeUtilise ?vehicule }
            OPTIONAL { ?vehicule mobility:nom ?vehiculeNom }
            OPTIONAL { ?location mobility:numeroLocation ?numero }
            OPTIONAL { ?location mobility:dateDebutLocation ?dateDebut }
            OPTIONAL { ?location mobility:dateFinLocation ?dateFin }
        }
        ORDER BY ?vehiculeNom
        """
    },

    "locations_by_date_range": {
        "name": "Locations par intervalle de dates",
        "description": "Récupère les locations dans une plage de dates (à compléter avec des filtres dynamiques)",
        "query": """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX mobility: <http://example.org/mobility-ontology/2025/09#>

        SELECT DISTINCT ?location ?numero ?statut ?dateDebut ?dateFin ?conducteur ?prix
        WHERE {
            ?location rdf:type mobility:Location .
            OPTIONAL { ?location mobility:numeroLocation ?numero }
            OPTIONAL { ?location mobility:statutLocation ?statut }
            OPTIONAL { ?location mobility:dateDebutLocation ?dateDebut }
            OPTIONAL { ?location mobility:dateFinLocation ?dateFin }
            OPTIONAL { ?location mobility:conducteurPrincipal ?conducteur }
            OPTIONAL { ?location mobility:prixTotalCalcule ?prix }
            # Pour filtrer entre deux dates, l'appelant doit ajouter une clause FILTER appropriée
        }
        ORDER BY ?dateDebut
        """
    }
}

# Export explicite
__all__ = ["SPARQL_QUERIES"]
