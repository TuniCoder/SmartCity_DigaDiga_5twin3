"""
Gestionnaire IA pour interpréter les questions en langage naturel 
et générer des requêtes SPARQL correspondantes
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from django.conf import settings

# Import des requêtes SPARQL pour les locations
from ..gestion_location.location_sparql import SPARQL_QUERIES as LOCATION_SPARQL_QUERIES

logger = logging.getLogger(__name__)

class AIQueryProcessor:
    """Processeur IA pour convertir langage naturel en SPARQL"""
    
    def __init__(self):
        self.entity_patterns = {
            'utilisateur': ['utilisateur', 'user', 'personne', 'client', 'usager'],
            'vehicule': ['véhicule', 'vehicle', 'voiture', 'vélo', 'bike', 'car', 'auto'],
            'station': ['station', 'arrêt', 'stop', 'parking', 'borne'],
            'trajet': ['trajet', 'voyage', 'trip', 'parcours', 'route', 'itinéraire'],
            'trafic': ['trafic', 'traffic', 'circulation', 'transport', 'ligne'],
            'location': ['location', 'rental', 'réservation', 'reservation']
        }
        
        self.action_patterns = {
            'lister': ['liste', 'lister', 'affiche', 'montre', 'voir', 'trouver', 'chercher'],
            'compter': ['compte', 'combien', 'nombre', 'total', 'quantité'],
            'filtrer': ['avec', 'ayant', 'qui ont', 'où', 'filter', 'condition'],
            'localiser': ['où', 'localisation', 'position', 'situé', 'coordonnées']
        }
        
        self.property_patterns = {
            'nom': ['nom', 'name', 'appelé', 'nommé'],
            'type': ['type', 'catégorie', 'kind', 'genre'],
            'statut': ['statut', 'status', 'état', 'disponible'],
            'position': ['position', 'coordonnées', 'latitude', 'longitude', 'où'],
            'distance': ['distance', 'km', 'kilomètre', 'loin'],
            'durée': ['durée', 'temps', 'minute', 'heure'],
            'coût': ['coût', 'prix', 'tarif', 'cost', 'dinar']
        }
    
    def process_natural_language_query(self, question: str) -> Dict:
        """
        Traite une question en langage naturel et génère une requête SPARQL
        """
        try:
            question_lower = question.lower()
            
            # Détecter le type d'entité principal
            main_entity = self._detect_main_entity(question_lower)
            
            # Détecter l'action demandée
            action = self._detect_action(question_lower)
            
            # Détecter les propriétés mentionnées
            properties = self._detect_properties(question_lower)
            
            # Détecter les filtres/conditions
            filters = self._extract_filters(question_lower)
            
            # Générer la requête SPARQL
            sparql_query = self._generate_sparql(main_entity, action, properties, filters)
            
            return {
                'success': True,
                'original_question': question,
                'detected_entity': main_entity,
                'detected_action': action,
                'detected_properties': properties,
                'detected_filters': filters,
                'sparql_query': sparql_query,
                'explanation': self._generate_explanation(main_entity, action, properties, filters)
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement de la question: {e}")
            return {
                'success': False,
                'error': str(e),
                'original_question': question,
                'suggestion': self._get_example_questions()
            }
    
    def _detect_main_entity(self, question: str) -> str:
        """Détecte l'entité principale de la question"""
        for entity, patterns in self.entity_patterns.items():
            for pattern in patterns:
                if pattern in question:
                    return entity
        return 'general'  # Entité par défaut
    
    def _detect_action(self, question: str) -> str:
        """Détecte l'action demandée"""
        for action, patterns in self.action_patterns.items():
            for pattern in patterns:
                if pattern in question:
                    return action
        return 'lister'  # Action par défaut
    
    def _detect_properties(self, question: str) -> List[str]:
        """Détecte les propriétés mentionnées"""
        detected_properties = []
        for prop, patterns in self.property_patterns.items():
            for pattern in patterns:
                if pattern in question:
                    detected_properties.append(prop)
        return detected_properties if detected_properties else ['nom']
    
    def _extract_filters(self, question: str) -> List[Dict]:
        """Extrait les filtres de la question"""
        filters = []
        
        # Filtres simples basés sur des mots-clés
        if 'disponible' in question:
            filters.append({'property': 'statut', 'value': 'disponible', 'operator': '='})
        
        if 'électrique' in question:
            filters.append({'property': 'typeVéhicule', 'value': 'électrique', 'operator': '='})
        
        # Recherche de noms spécifiques (mots en majuscules ou entre guillemets)
        name_matches = re.findall(r'[A-Z][a-z]+|"([^"]*)"', question)
        for match in name_matches:
            name = match if isinstance(match, str) else match[0]
            if len(name) > 2:  # Éviter les mots trop courts
                filters.append({'property': 'nom', 'value': name, 'operator': 'contains'})
        
        return filters
    
    def _generate_sparql(self, entity: str, action: str, properties: List[str], filters: List[Dict]) -> str:
        """Génère la requête SPARQL basée sur les éléments détectés"""
        
        # Mappage des entités vers les classes RDF
        entity_mapping = {
            'utilisateur': 'mobility:Utilisateur',
            'vehicule': 'mobility:Véhicule',
            'station': 'mobility:Station',
            'trajet': 'mobility:Trajet',
            'trafic': 'mobility:Route',
            'location': 'mobility:Location'
        }
        
        # Mappage des propriétés vers RDF
        property_mapping = {
            'nom': {'utilisateur': 'mobility:nom', 'station': 'mobility:nomStation', 'trajet': 'mobility:pointDépart'},
            'type': {'vehicule': 'mobility:typeVéhicule', 'station': 'mobility:typeStation', 'location': 'mobility:typeLocation'},
            'statut': {'vehicule': 'mobility:statut', 'location': 'mobility:statutLocation'},
            'position': {'station': ['mobility:latitude', 'mobility:longitude']},
            'distance': {'trajet': 'mobility:distance'},
            'durée': {'trajet': 'mobility:durée', 'location': 'mobility:dureeLocation'},
            'coût': {'trajet': 'mobility:coût', 'location': 'mobility:prixLocation'}
        }
        
        # Variables de base
        main_var = '?entity'
        select_vars = [main_var]
        where_clauses = []
        
        # Classe principale
        rdf_class = entity_mapping.get(entity, 'owl:Thing')
        where_clauses.append(f'{main_var} rdf:type {rdf_class} .')
        
        # Ajout des propriétés demandées
        for prop in properties:
            if prop in property_mapping and entity in property_mapping[prop]:
                prop_mapping = property_mapping[prop][entity]
                if isinstance(prop_mapping, list):
                    # Plusieurs propriétés (ex: latitude + longitude)
                    for i, prop_uri in enumerate(prop_mapping):
                        var_name = f'?{prop}_{i}'
                        select_vars.append(var_name)
                        where_clauses.append(f'OPTIONAL {{ {main_var} {prop_uri} {var_name} }}')
                else:
                    var_name = f'?{prop}'
                    select_vars.append(var_name)
                    where_clauses.append(f'OPTIONAL {{ {main_var} {prop_mapping} {var_name} }}')
        
        # Ajout des filtres
        for filter_item in filters:
            prop = filter_item['property']
            value = filter_item['value']
            operator = filter_item.get('operator', '=')
            
            if prop in property_mapping and entity in property_mapping[prop]:
                prop_uri = property_mapping[prop][entity]
                if isinstance(prop_uri, str):
                    if operator == 'contains':
                        where_clauses.append(f'{main_var} {prop_uri} ?filter_val .')
                        where_clauses.append(f'FILTER(CONTAINS(LCASE(STR(?filter_val)), "{value.lower()}"))')
                    else:
                        where_clauses.append(f'{main_var} {prop_uri} "{value}" .')
        
        # Construction de la requête finale
        if action == 'compter':
            sparql_query = f"""
            SELECT (COUNT(DISTINCT {main_var}) as ?count)
            WHERE {{
                {' '.join(where_clauses)}
            }}
            """
        else:
            sparql_query = f"""
            SELECT DISTINCT {' '.join(select_vars)}
            WHERE {{
                {' '.join(where_clauses)}
            }}
            ORDER BY {main_var}
            LIMIT 20
            """
        
        return sparql_query.strip()
    
    def _generate_explanation(self, entity: str, action: str, properties: List[str], filters: List[Dict]) -> str:
        """Génère une explication de la requête générée"""
        entity_names = {
            'utilisateur': 'utilisateurs',
            'vehicule': 'véhicules', 
            'station': 'stations',
            'trajet': 'trajets',
            'trafic': 'données de trafic',
            'location': 'locations'
        }
        
        action_names = {
            'lister': 'Liste des',
            'compter': 'Nombre de',
            'filtrer': 'Recherche de',
            'localiser': 'Localisation des'
        }
        
        explanation = f"{action_names.get(action, 'Information sur')} {entity_names.get(entity, entity)}"
        
        if properties and properties != ['nom']:
            prop_desc = ', '.join(properties)
            explanation += f" avec les propriétés: {prop_desc}"
        
        if filters:
            filter_desc = []
            for f in filters:
                filter_desc.append(f"{f['property']} {f.get('operator', '=')} {f['value']}")
            explanation += f" (filtres: {', '.join(filter_desc)})"
        
        return explanation
    
    def _get_example_questions(self) -> List[str]:
        """Retourne des exemples de questions possibles"""
        return [
            "Liste tous les utilisateurs",
            "Combien de véhicules sont disponibles?",
            "Montre-moi les stations avec leurs coordonnées",
            "Quels sont les trajets de plus de 5km?",
            "Trouve les véhicules électriques",
            "Où se trouvent les stations de vélos?",
            "Liste les utilisateurs de type cycliste",
            "Quel est le coût moyen des trajets?"
        ]


class SampleQueries:
    """Classe contenant des requêtes SPARQL prédéfinies pour différents cas d'usage"""
    
    @staticmethod
    def get_predefined_queries() -> Dict[str, Dict]:
        """Retourne un dictionnaire de requêtes SPARQL prédéfinies"""
        return {
            "all_users": {
                "name": "Tous les utilisateurs",
                "description": "Liste tous les utilisateurs avec leurs informations de base",
                "query": """
                SELECT ?user ?nom ?email ?typeUtilisateur ?age
                WHERE {
                    ?user rdf:type mobility:Utilisateur .
                    OPTIONAL { ?user mobility:nom ?nom }
                    OPTIONAL { ?user mobility:email ?email }
                    OPTIONAL { ?user mobility:typeUtilisateur ?typeUtilisateur }
                    OPTIONAL { ?user mobility:âge ?age }
                }
                ORDER BY ?nom
                """,
                "category": "Utilisateurs"
            },
            
            "available_vehicles": {
                "name": "Véhicules disponibles",
                "description": "Liste tous les véhicules avec statut 'disponible'",
                "query": """
                SELECT ?vehicle ?marque ?modele ?couleur ?type
                WHERE {
                    ?vehicle rdf:type mobility:Véhicule .
                    ?vehicle mobility:statut "disponible" .
                    OPTIONAL { ?vehicle mobility:marque ?marque }
                    OPTIONAL { ?vehicle mobility:modèle ?modele }
                    OPTIONAL { ?vehicle mobility:couleur ?couleur }
                    ?vehicle rdf:type ?type .
                    FILTER(?type = mobility:Vélo || ?type = mobility:Voiture)
                }
                ORDER BY ?marque
                """,
                "category": "Véhicules"
            },
            
            "stations_with_location": {
                "name": "Stations avec localisation",
                "description": "Liste toutes les stations avec leurs coordonnées",
                "query": """
                SELECT ?station ?nomStation ?latitude ?longitude ?adresse ?capacite
                WHERE {
                    ?station rdf:type mobility:Station .
                    OPTIONAL { ?station mobility:nomStation ?nomStation }
                    OPTIONAL { ?station mobility:latitude ?latitude }
                    OPTIONAL { ?station mobility:longitude ?longitude }
                    OPTIONAL { ?station mobility:adresse ?adresse }
                    OPTIONAL { ?station mobility:capacité ?capacite }
                }
                ORDER BY ?nomStation
                """,
                "category": "Stations"
            },
            
            "user_trips": {
                "name": "Trajets des utilisateurs",
                "description": "Liste tous les trajets avec les utilisateurs qui les ont effectués",
                "query": """
                SELECT ?trajet ?userName ?pointDepart ?pointArrivee ?distance ?duree ?mode ?cout
                WHERE {
                    ?trajet rdf:type mobility:Trajet .
                    ?trajet mobility:effectuéPar ?user .
                    ?user mobility:nom ?userName .
                    OPTIONAL { ?trajet mobility:pointDépart ?pointDepart }
                    OPTIONAL { ?trajet mobility:pointArrivée ?pointArrivee }
                    OPTIONAL { ?trajet mobility:distance ?distance }
                    OPTIONAL { ?trajet mobility:durée ?duree }
                    OPTIONAL { ?trajet mobility:mode ?mode }
                    OPTIONAL { ?trajet mobility:coût ?cout }
                }
                ORDER BY ?userName
                """,
                "category": "Trajets"
            },

            "user_locations": {
                "name": "Locations par utilisateur",
                "description": "Liste toutes les locations avec les utilisateurs qui les ont effectuées",
                "query": """
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX mobility: <http://example.org/mobility-ontology/2025/09#>
                
                SELECT DISTINCT ?location ?numero ?statut ?userName ?dateDebut ?prix
                WHERE {
                    ?location rdf:type mobility:Location .
                    ?location mobility:conducteurPrincipal ?userName .
                    OPTIONAL { ?location mobility:numeroLocation ?numero }
                    OPTIONAL { ?location mobility:statutLocation ?statut }
                    OPTIONAL { ?location mobility:dateDebutLocation ?dateDebut }
                    OPTIONAL { ?location mobility:prixTotalCalcule ?prix }
                }
                ORDER BY ?userName
                """,
                "category": "Locations"
                
            },
            
            "vehicle_statistics": {
                "name": "Statistiques véhicules",
                "description": "Compte les véhicules par type",
                "query": """
                SELECT ?type (COUNT(?vehicle) as ?count)
                WHERE {
                    ?vehicle rdf:type ?type .
                    FILTER(?type = mobility:Vélo || ?type = mobility:Voiture)
                }
                GROUP BY ?type
                ORDER BY DESC(?count)
                """,
                "category": "Statistiques"
            },


   "all_locations": {
    "name": "Toutes les locations",
    "description": "Liste toutes les locations avec leurs informations de base",
    "query": """
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX mobility: <http://example.org/mobility-ontology/2025/09#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT DISTINCT ?location ?numero ?statut ?type ?dateDebut ?dateFin ?lieuPrise ?lieuRetour ?conducteur ?prix
    WHERE {
        ?location rdf:type mobility:Location .
        OPTIONAL { ?location mobility:numeroLocation ?numero . }
        OPTIONAL { ?location mobility:statutLocation ?statut . }
        OPTIONAL { ?location mobility:typeLocation ?type . }
        OPTIONAL { ?location mobility:dateDebutLocation ?dateDebut . }
        OPTIONAL { ?location mobility:dateFinLocation ?dateFin . }
        OPTIONAL { ?location mobility:lieuPrise ?lieuPrise . }
        OPTIONAL { ?location mobility:lieuRetour ?lieuRetour . }
        OPTIONAL { ?location mobility:conducteurPrincipal ?conducteur . }
        OPTIONAL { ?location mobility:prixTotalCalcule ?prix . }
    }
    ORDER BY DESC(?dateDebut)
    """,
    "category": "Locations"
},



    "location_statistics_by_status": {
        "name": "Statistiques des locations par statut",
        "description": "Compte le nombre de locations pour chaque statut",
        "query": """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX mobility: <http://example.org/mobility-ontology/2025/09#>
        
        SELECT ?statut (COUNT(DISTINCT ?location) as ?count)
        WHERE {
            ?location rdf:type mobility:Location .
            OPTIONAL { ?location mobility:statutLocation ?statut }
        }
        GROUP BY ?statut
        ORDER BY DESC(?count)
        """,
        "category": "Statistiques"
    },
    
    # Utilisation des requêtes SPARQL importées depuis location_sparql.py
    "active_locations": LOCATION_SPARQL_QUERIES["active_locations"],
    "user_locations_details": LOCATION_SPARQL_QUERIES["user_locations_details"],
    "all_locations": LOCATION_SPARQL_QUERIES["all_locations"],
    "user_locations": LOCATION_SPARQL_QUERIES["user_locations"],
    "location_details": LOCATION_SPARQL_QUERIES["location_details"],
    "locations_by_vehicle": LOCATION_SPARQL_QUERIES["locations_by_vehicle"],
    "locations_by_date_range": LOCATION_SPARQL_QUERIES["locations_by_date_range"]
}

# Instance globale du processeur IA
ai_processor = AIQueryProcessor()