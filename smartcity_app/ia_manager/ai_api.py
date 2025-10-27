# smartcity_app/ia_manager/ai_api.py

import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

def ask_ai(prompt):
    try:
        response = openai.ChatCompletion.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": "You are an assistant helping manage SmartCity data."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=500,
            temperature=0.7,
        )
        return response.choices[0].message["content"]
    except Exception as e:
        return f"❌ AI Error: {e}"

class AIProcessor:
    """AI processor for SmartCity queries"""
    
    def __call__(self, prompt):
        """Allow AIProcessor to be called as a function for backward compatibility"""
        return ask_ai(prompt)
    
    def process_natural_language_query(self, question):
        """Process a natural language question and generate SPARQL query"""
        try:
            # Simple placeholder implementation
            # In a real implementation, this would use OpenAI to convert natural language to SPARQL
            
            response = {
                'success': True,
                'sparql_query': self._generate_simple_sparql(question),
                'explanation': f"Traduction de la question '{question}' en requête SPARQL",
                'detected_entity': self._detect_entity(question),
                'detected_action': self._detect_action(question),
                'detected_properties': [],
                'detected_filters': []
            }
            return response
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'suggestion': []
            }
    
    def _generate_simple_sparql(self, question):
        """Generate a simple SPARQL query based on the question"""
        # This is a simplified implementation
        # A real implementation would use AI to generate proper SPARQL
        
        question_lower = question.lower()
        
        if 'station' in question_lower or 'gare' in question_lower:
            return '''
            PREFIX : <http://example.org/mobility-ontology/2025/09#>
            SELECT ?station ?nom ?adresse WHERE {
                ?station a :StationTransport .
                ?station :nom ?nom .
                OPTIONAL { ?station :adresse ?adresse . }
            }
            LIMIT 20
            '''
        elif 'véhicule' in question_lower or 'vehicle' in question_lower:
            return '''
            PREFIX : <http://example.org/mobility-ontology/2025/09#>
            SELECT ?vehicule ?type ?statut WHERE {
                ?vehicule a :Vehicule .
                ?vehicule :type ?type .
                ?vehicule :statut ?statut .
            }
            LIMIT 20
            '''
        else:
            # Generic query
            return '''
            PREFIX : <http://example.org/mobility-ontology/2025/09#>
            SELECT ?s ?p ?o WHERE {
                ?s ?p ?o .
            }
            LIMIT 20
            '''
    
    def _detect_entity(self, question):
        """Detect entity type from question"""
        question_lower = question.lower()
        if 'station' in question_lower or 'gare' in question_lower:
            return 'StationTransport'
        elif 'véhicule' in question_lower or 'vehicle' in question_lower:
            return 'Vehicule'
        elif 'route' in question_lower or 'street' in question_lower:
            return 'Route'
        return None
    
    def _detect_action(self, question):
        """Detect action from question"""
        question_lower = question.lower()
        if 'liste' in question_lower or 'show' in question_lower or 'get' in question_lower:
            return 'SELECT'
        elif 'count' in question_lower or 'combien' in question_lower or 'nombre' in question_lower:
            return 'COUNT'
        return 'SELECT'

# Create instance for backward compatibility
ai_processor = AIProcessor()

class SampleQueries:
    """Predefined SPARQL queries for SmartCity ontology"""
    
    @staticmethod
    def get_predefined_queries():
        """Return dictionary of predefined queries organized by category"""
        return {
            'station-1': {
                'name': 'Stations de transport',
                'question': 'Liste des stations de transport disponibles',
                'sparql': '''
                PREFIX : <http://example.org/mobility-ontology/2025/09#>
                SELECT ?station ?name ?address
                WHERE {
                    ?station a :StationTransport .
                    ?station :nom ?name .
                    OPTIONAL { ?station :adresse ?address . }
                }
                LIMIT 20
                ''',
                'category': 'Stations'
            },
            'vehicle-1': {
                'name': 'Véhicules disponibles',
                'question': 'Quels véhicules sont disponibles',
                'sparql': '''
                PREFIX : <http://example.org/mobility-ontology/2025/09#>
                SELECT ?vehicule ?type ?statut
                WHERE {
                    ?vehicule a :Vehicule .
                    ?vehicule :type ?type .
                    ?vehicule :statut ?statut .
                    FILTER (?statut = "actif")
                }
                LIMIT 20
                ''',
                'category': 'Véhicules'
            },
            'route-1': {
                'name': 'Routes disponibles',
                'question': 'Liste des routes dans la ville',
                'sparql': '''
                PREFIX : <http://example.org/mobility-ontology/2025/09#>
                SELECT ?route ?nom ?longueur
                WHERE {
                    ?route a :Route .
                    ?route :nom ?nom .
                    OPTIONAL { ?route :longueur ?longueur . }
                }
                LIMIT 20
                ''',
                'category': 'Infrastructure'
            },
            'user-1': {
                'name': 'Utilisateurs actifs',
                'question': 'Combien d\'utilisateurs sont actifs',
                'sparql': '''
                PREFIX : <http://example.org/mobility-ontology/2025/09#>
                SELECT ?utilisateur ?nom
                WHERE {
                    ?utilisateur a :Utilisateur .
                    ?utilisateur :nom ?nom .
                    ?utilisateur :statut "actif" .
                }
                LIMIT 20
                ''',
                'category': 'Utilisateurs'
            },
            'traffic-1': {
                'name': 'État du trafic',
                'question': 'Quel est l\'état du trafic',
                'sparql': '''
                PREFIX : <http://example.org/mobility-ontology/2025/09#>
                SELECT ?capteur ?intensite ?heure
                WHERE {
                    ?capteur a :CapteurTrafic .
                    ?capteur :intensiteTrafic ?intensite .
                    ?capteur :timestamp ?heure .
                }
                ORDER BY DESC(?heure)
                LIMIT 20
                ''',
                'category': 'Trafic'
            }
        }
    
    @staticmethod
    def _get_example_questions():
        """Return example questions for the AI assistant"""
        return [
            "Quelles sont les stations de métro près de moi ?",
            "Combien de vélos sont disponibles dans la ville ?",
            "Quels sont les itinéraires pour aller à l'aéroport ?",
            "Y a-t-il des embouteillages sur la route principale ?",
            "Quels transports sont accessibles aux personnes à mobilité réduite ?"
]
"""
Gestionnaire IA pour interpréter les questions en langage naturel 
et générer des requêtes SPARQL correspondantes
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from django.conf import settings

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
            'capteur': ['capteur', 'sensor', 'détecteur', 'capteurs', 'sensors'],
            'zone_trafic': ['zone', 'zone de trafic', 'zone trafic', 'secteur', 'région']
        }

        self.action_patterns = {
            'lister': ['liste', 'lister', 'affiche', 'montre', 'voir', 'trouver', 'chercher'],
            'compter': ['compte', 'combien', 'nombre', 'total', 'quantité'],
            'filtrer': ['avec', 'ayant', 'qui ont', 'où', 'filter', 'condition'],
            'localiser': ['où', 'localisation', 'position', 'situé', 'coordonnées'],
            'analyser': ['analyser', 'analyse', 'étudier', 'examiner', 'vérifier']
        }

        self.property_patterns = {
            'nom': ['nom', 'name', 'appelé', 'nommé'],
            'type': ['type', 'catégorie', 'kind', 'genre'],
            'statut': ['statut', 'status', 'état', 'disponible', 'actif', 'inactif'],
            'position': ['position', 'coordonnées', 'latitude', 'longitude', 'où'],
            'distance': ['distance', 'km', 'kilomètre', 'loin'],
            'durée': ['durée', 'temps', 'minute', 'heure'],
            'coût': ['coût', 'prix', 'tarif', 'cost', 'dinar'],
            'precision': ['précision', 'accuracy', 'fiabilité', 'exactitude'],
            'frequence': ['fréquence', 'frequency', 'intervalle', 'mesure'],
            'vitesse': ['vitesse', 'speed', 'vélocité', 'km/h']
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
            'capteur': 'mobility:CapteurTrafic',
            'zone_trafic': 'mobility:ZoneTrafic'
        }

        # Mappage des propriétés vers RDF
        property_mapping = {
            'nom': {
                'utilisateur': 'mobility:nom',
                'station': 'mobility:nomStation',
                'trajet': 'mobility:pointDépart',
                'capteur': 'mobility:nomCapteur'
            },
            'type': {
                'vehicule': 'mobility:typeVéhicule',
                'station': 'mobility:typeStation',
                'capteur': 'mobility:typeCapteur'
            },
            'statut': {
                'vehicule': 'mobility:statut',
                'capteur': 'mobility:statutCapteur'
            },
            'position': {
                'station': ['mobility:latitude', 'mobility:longitude'],
                'capteur': ['mobility:latitude', 'mobility:longitude']
            },
            'distance': {'trajet': 'mobility:distance'},
            'durée': {'trajet': 'mobility:durée'},
            'coût': {'trajet': 'mobility:coût'},
            'precision': {'capteur': 'mobility:precisionDetection'},
            'frequence': {'capteur': 'mobility:frequenceMesure'},
            'vitesse': {'capteur': ['mobility:vitesseMinDetection', 'mobility:vitesseMaxDetection']}
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
            'trafic': 'données de trafic'
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

            # ===== REQUÊTES GESTION TRAFIC =====

            "all_traffic_sensors": {
                "name": "Tous les capteurs de trafic",
                "description": "Liste tous les capteurs de trafic avec leurs informations",
                "query": """
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
                """,
                "category": "Gestion Trafic"
            },

            "active_traffic_sensors": {
                "name": "Capteurs de trafic actifs",
                "description": "Liste tous les capteurs de trafic avec statut 'actif'",
                "query": """
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
                """,
                "category": "Gestion Trafic"
            },

            "traffic_sensors_by_type": {
                "name": "Capteurs de trafic par type",
                "description": "Compte les capteurs de trafic par type",
                "query": """
                SELECT ?type (COUNT(?capteur) as ?count)
                WHERE {
                    ?capteur rdf:type mobility:CapteurTrafic .
                    ?capteur mobility:typeCapteur ?type .
                }
                GROUP BY ?type
                ORDER BY DESC(?count)
                """,
                "category": "Gestion Trafic"
            },

            "traffic_sensors_by_zone": {
                "name": "Capteurs de trafic par zone",
                "description": "Liste les capteurs de trafic groupés par zone",
                "query": """
                SELECT ?zone (COUNT(?capteur) as ?count) (GROUP_CONCAT(?nom; separator=", ") as ?capteurs)
                WHERE {
                    ?capteur rdf:type mobility:CapteurTrafic .
                    ?capteur mobility:zoneTrafic ?zone .
                    OPTIONAL { ?capteur mobility:nomCapteur ?nom }
                }
                GROUP BY ?zone
                ORDER BY DESC(?count)
                """,
                "category": "Gestion Trafic"
            },

            "traffic_sensors_coverage": {
                "name": "Couverture des capteurs de trafic",
                "description": "Affiche les zones de trafic et leur couverture en capteurs",
                "query": """
                SELECT ?zone (COUNT(?capteur) as ?nombreCapteurs) (AVG(?precision) as ?precisionMoyenne)
                WHERE {
                    ?capteur rdf:type mobility:CapteurTrafic .
                    ?capteur mobility:zoneTrafic ?zone .
                    OPTIONAL { ?capteur mobility:precisionDetection ?precision }
                }
                GROUP BY ?zone
                ORDER BY DESC(?nombreCapteurs)
                """,
                "category": "Gestion Trafic"
            },

            "high_precision_sensors": {
                "name": "Capteurs haute précision",
                "description": "Liste les capteurs avec une précision de détection > 90%",
                "query": """
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
                """,
                "category": "Gestion Trafic"
            },

            "traffic_sensors_with_details": {
                "name": "Détails complets des capteurs",
                "description": "Affiche tous les détails des capteurs de trafic",
                "query": """
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
                """,
                "category": "Gestion Trafic"
            },

            "traffic_sensors_by_provider": {
                "name": "Capteurs par fournisseur",
                "description": "Liste les capteurs groupés par fournisseur",
                "query": """
                SELECT ?fournisseur (COUNT(?capteur) as ?count) (GROUP_CONCAT(?nom; separator=", ") as ?capteurs)
                WHERE {
                    ?capteur rdf:type mobility:CapteurTrafic .
                    ?capteur mobility:fournisseur ?fournisseur .
                    OPTIONAL { ?capteur mobility:nomCapteur ?nom }
                }
                GROUP BY ?fournisseur
                ORDER BY DESC(?count)
                """,
                "category": "Gestion Trafic"
            },

            "traffic_sensors_by_model": {
                "name": "Capteurs par modèle",
                "description": "Liste les capteurs groupés par modèle",
                "query": """
                SELECT ?modele (COUNT(?capteur) as ?count) ?fournisseur
                WHERE {
                    ?capteur rdf:type mobility:CapteurTrafic .
                    ?capteur mobility:modele ?modele .
                    OPTIONAL { ?capteur mobility:fournisseur ?fournisseur }
                }
                GROUP BY ?modele ?fournisseur
                ORDER BY DESC(?count)
                """,
                "category": "Gestion Trafic"
            },

            "traffic_sensors_speed_range": {
                "name": "Plages de vitesse des capteurs",
                "description": "Affiche les plages de vitesse min/max détectées par les capteurs",
                "query": """
                SELECT ?capteur ?nom ?vitesseMin ?vitesseMax ?type
                WHERE {
                    ?capteur rdf:type mobility:CapteurTrafic .
                    ?capteur mobility:vitesseMinDetection ?vitesseMin .
                    ?capteur mobility:vitesseMaxDetection ?vitesseMax .
                    OPTIONAL { ?capteur mobility:nomCapteur ?nom }
                    OPTIONAL { ?capteur mobility:typeCapteur ?type }
                }
                ORDER BY ?vitesseMin
                """,
                "category": "Gestion Trafic"
            },
            
            "reservations_active": {
                "name": "Réservations actives",
                "description": "Liste toutes les réservations actives",
                "query": """
                SELECT ?reservation ?userName ?vehicleBrand ?dateReservation ?dureeReservation ?prix
                WHERE {
                    ?reservation rdf:type mobility:Réservation .
                    ?reservation mobility:statutRéservation "active" .
                    ?user mobility:réserve ?reservation .
                    ?reservation mobility:concerne ?vehicle .
                    ?user mobility:nom ?userName .
                    OPTIONAL { ?vehicle mobility:marque ?vehicleBrand }
                    OPTIONAL { ?reservation mobility:dateRéservation ?dateReservation }
                    OPTIONAL { ?reservation mobility:duréeRéservation ?dureeReservation }
                    OPTIONAL { ?reservation mobility:prixRéservation ?prix }
                }
                ORDER BY ?dateReservation
                """,
                "category": "Réservations"
            }
        }


# Instance globale du processeur IA
ai_processor = AIQueryProcessor()
