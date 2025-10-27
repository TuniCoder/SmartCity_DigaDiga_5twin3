"""
Gestionnaire IA pour interpréter les questions en langage naturel 
et générer des requêtes SPARQL correspondantes
"""

import openai
import os
import re
import logging
from typing import Dict, List, Optional, Tuple
from django.conf import settings

# Import des requêtes SPARQL pour les locations
from ..gestion_location.location_sparql import SPARQL_QUERIES as LOCATION_SPARQL_QUERIES

logger = logging.getLogger(__name__)

# Configuration OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

def ask_ai(prompt):
    """Fonction utilitaire pour interroger OpenAI"""
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


class AIQueryProcessor:
    """Processeur IA pour convertir langage naturel en SPARQL - Version complète"""
    
    def __init__(self):
        self.entity_patterns = {
            'utilisateur': ['utilisateur', 'user', 'personne', 'client', 'usager'],
            'voiture': ['voiture', 'voitures', 'auto', 'car', 'automobile', 'véhicule particulier'],
            'velo': ['vélo', 'vélos', 'velo', 'velos', 'bike', 'bicyclette', 'cyclisme'],
            'bus': ['bus', 'autobus', 'transport en commun', 'transport public'],
            'moto': ['moto', 'motos', 'motocyclette', 'motorcycle'],
            'trottinette': ['trottinette', 'trottinettes', 'scooter électrique', 'e-scooter'],
            'camion': ['camion', 'camions', 'truck', 'poids lourd', 'utilitaire'],
            'vehicule': ['véhicule', 'véhicules', 'vehicle', 'vehicles', 'tous les véhicules'],
            'station': ['station', 'arrêt', 'stop', 'parking', 'borne', 'gare'],
            'trajet': ['trajet', 'voyage', 'trip', 'parcours', 'route', 'itinéraire'],
            'trafic': ['trafic', 'traffic', 'circulation', 'transport', 'ligne'],
            'capteur': ['capteur', 'sensor', 'détecteur', 'capteurs', 'sensors'],
            'zone_trafic': ['zone', 'zone de trafic', 'zone trafic', 'secteur', 'région'],
            'location': ['location', 'rental', 'réservation', 'reservation']
        }

        self.action_patterns = {
            'lister': ['liste', 'lister', 'affiche', 'montre', 'voir', 'trouver', 'chercher', 'show', 'get'],
            'compter': ['compte', 'combien', 'nombre', 'total', 'quantité', 'count'],
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
    
    def __call__(self, prompt):
        """Allow AIQueryProcessor to be called as a function for backward compatibility"""
        return ask_ai(prompt)
    
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
        
        # Détection de couleurs
        couleurs = ['rouge', 'bleu', 'vert', 'blanc', 'noir', 'jaune', 'orange', 'violet', 'rose', 'gris']
        for couleur in couleurs:
            if couleur in question.lower():
                filters.append({'property': 'couleur', 'value': couleur, 'operator': '='})
        
        # Détection de marques courantes
        marques = ['toyota', 'peugeot', 'renault', 'ford', 'volkswagen', 'bmw', 'mercedes', 'audi', 'citroën', 'hyundai']
        for marque in marques:
            if marque in question.lower():
                filters.append({'property': 'marque', 'value': marque.capitalize(), 'operator': '='})
        
        # Recherche de noms spécifiques (mots en majuscules ou entre guillemets)
        name_matches = re.findall(r'[A-Z][a-z]+|"([^"]*)"', question)
        for match in name_matches:
            name = match if isinstance(match, str) else match[0]
            if len(name) > 2 and name.lower() not in marques and name.lower() not in couleurs:  # Éviter les duplicatas
                filters.append({'property': 'nom', 'value': name, 'operator': 'contains'})
        
        return filters
    
    def _generate_sparql(self, entity: str, action: str, properties: List[str], filters: List[Dict]) -> str:
        """Génère la requête SPARQL basée sur les éléments détectés"""

        # Mappage des entités vers les classes RDF
        entity_mapping = {
            'utilisateur': 'mobility:Utilisateur',
            'voiture': 'mobility:Voiture',
            'velo': 'mobility:Vélo', 
            'bus': 'mobility:Bus',
            'moto': 'mobility:Moto',
            'trottinette': 'mobility:Trottinette',
            'camion': 'mobility:Camion',
            'vehicule': 'mobility:Véhicule',  # Sera géré spécialement pour tous les véhicules
            'station': 'mobility:Station',
            'trajet': 'mobility:Trajet',
            'trafic': 'mobility:Route',
            'capteur': 'mobility:CapteurTrafic',
            'zone_trafic': 'mobility:ZoneTrafic',
            'general': 'owl:Thing',
            'location': 'mobility:Location'
        }

        # Mappage des propriétés vers RDF
        property_mapping = {
            'nom': {
                'utilisateur': 'mobility:nom',
                'station': 'mobility:nomStation',
                'trajet': 'mobility:pointDépart',
                'capteur': 'mobility:nomCapteur',
                'vehicule': 'mobility:nom',
                'voiture': 'mobility:nom',
                'velo': 'mobility:nom',
                'bus': 'mobility:nom',
                'moto': 'mobility:nom',
                'trottinette': 'mobility:nom',
                'camion': 'mobility:nom'
            },
            'type': {
                'vehicule': 'mobility:typeVéhicule',
                'voiture': 'mobility:typeVéhicule',
                'velo': 'mobility:typeVéhicule',
                'bus': 'mobility:typeVéhicule',
                'moto': 'mobility:typeVéhicule',
                'trottinette': 'mobility:typeVéhicule',
                'camion': 'mobility:typeVéhicule',
                'station': 'mobility:typeStation',
                'capteur': 'mobility:typeCapteur'
            },
            'statut': {
                'vehicule': 'mobility:statut',
                'voiture': 'mobility:statut',
                'velo': 'mobility:statut',
                'bus': 'mobility:statut',
                'moto': 'mobility:statut',
                'trottinette': 'mobility:statut',
                'camion': 'mobility:statut',
                'capteur': 'mobility:statutCapteur'
            },
            'marque': {
                'vehicule': 'mobility:marque',
                'voiture': 'mobility:marque',
                'velo': 'mobility:marque',
                'bus': 'mobility:marque',
                'moto': 'mobility:marque',
                'trottinette': 'mobility:marque',
                'camion': 'mobility:marque'
            },
            'modele': {
                'vehicule': 'mobility:modèle',
                'voiture': 'mobility:modèle',
                'velo': 'mobility:modèle',
                'bus': 'mobility:modèle',
                'moto': 'mobility:modèle',
                'trottinette': 'mobility:modèle',
                'camion': 'mobility:modèle'
            },
            'couleur': {
                'vehicule': 'mobility:couleur',
                'voiture': 'mobility:couleur',
                'velo': 'mobility:couleur',
                'bus': 'mobility:couleur',
                'moto': 'mobility:couleur',
                'trottinette': 'mobility:couleur',
                'camion': 'mobility:couleur'
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
        
        # Classe principale - traitement spécial pour les véhicules
        if entity == 'vehicule':
            # Pour les véhicules, utiliser une union de toutes les classes de véhicules
            vehicle_classes = ['mobility:Voiture', 'mobility:Vélo', 'mobility:Bus', 'mobility:Moto', 'mobility:Trottinette', 'mobility:Camion']
            union_clauses = []
            for vc in vehicle_classes:
                union_clauses.append(f'{{ {main_var} rdf:type {vc} }}')
            where_clauses.append('{ ' + ' UNION '.join(union_clauses) + ' }')
        elif entity in ['voiture', 'velo', 'bus', 'moto', 'trottinette', 'camion']:
            # Type spécifique de véhicule
            rdf_class = entity_mapping.get(entity, 'owl:Thing')
            where_clauses.append(f'{main_var} rdf:type {rdf_class} .')
        else:
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
            PREFIX mobility: <http://example.org/mobility-ontology/2025/09#>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX owl: <http://www.w3.org/2002/07/owl#>
            SELECT (COUNT(DISTINCT {main_var}) as ?count)
            WHERE {{
                {' '.join(where_clauses)}
            }}
            """
        else:
            sparql_query = f"""
            PREFIX mobility: <http://example.org/mobility-ontology/2025/09#>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX owl: <http://www.w3.org/2002/07/owl#>
            SELECT DISTINCT {' '.join(select_vars)}
            WHERE {{
                {' '.join(where_clauses)}
            }}
            ORDER BY {main_var}
            LIMIT 20
            """
        
        return sparql_query.strip()
    
    def _generate_simple_sparql(self, question):
        """Generate a simple SPARQL query based on the question - For backward compatibility"""
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
            PREFIX mobility: <http://example.org/mobility-ontology/2025/09#>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            SELECT ?vehicule ?marque ?modele ?statut ?type WHERE {
                {
                    ?vehicule rdf:type mobility:Voiture .
                } UNION {
                    ?vehicule rdf:type mobility:Vélo .
                } UNION {
                    ?vehicule rdf:type mobility:Bus .
                } UNION {
                    ?vehicule rdf:type mobility:Moto .
                } UNION {
                    ?vehicule rdf:type mobility:Trottinette .
                } UNION {
                    ?vehicule rdf:type mobility:Camion .
                }
                OPTIONAL { ?vehicule mobility:marque ?marque }
                OPTIONAL { ?vehicule mobility:modèle ?modele }
                OPTIONAL { ?vehicule mobility:statut ?statut }
                ?vehicule rdf:type ?type .
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
        """Detect entity type from question - For backward compatibility"""
        question_lower = question.lower()
        if 'station' in question_lower or 'gare' in question_lower:
            return 'StationTransport'
        elif 'véhicule' in question_lower or 'vehicle' in question_lower:
            return 'Vehicule'
        elif 'route' in question_lower or 'street' in question_lower:
            return 'Route'
        return None
    
    def _generate_explanation(self, entity: str, action: str, properties: List[str], filters: List[Dict]) -> str:
        """Génère une explication de la requête générée"""
        entity_names = {
            'utilisateur': 'utilisateurs',
            'vehicule': 'véhicules', 
            'station': 'stations',
            'trajet': 'trajets',
            'trafic': 'données de trafic',
            'capteur': 'capteurs de trafic',
            'zone_trafic': 'zones de trafic',
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
            "Quel est le coût moyen des trajets?",
            "Quelles sont les stations de métro près de moi ?",
            "Combien de vélos sont disponibles dans la ville ?",
            "Quels sont les itinéraires pour aller à l'aéroport ?",
            "Y a-t-il des embouteillages sur la route principale ?",
            "Quels transports sont accessibles aux personnes à mobilité réduite ?"
        ]



class SampleQueries:
    """Classe contenant des requêtes SPARQL prédéfinies pour différents cas d'usage - Version fusionnée"""
    
    @staticmethod
    def get_predefined_queries() -> Dict[str, Dict]:
        """Retourne un dictionnaire de requêtes SPARQL prédéfinies fusionnées"""
        return {
            # ===== REQUÊTES DE BASE (Version simplifiée) =====
            'station-1': {
                'name': 'Stations de transport',
                'description': 'Liste des stations de transport disponibles',
                'query': '''
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
                'description': 'Quels véhicules sont disponibles',
                'query': '''
                PREFIX mobility: <http://example.org/mobility-ontology/2025/09#>
                SELECT ?vehicule ?marque ?modele ?type ?statut
                WHERE {
                    {
                        ?vehicule a mobility:Voiture .
                    } UNION {
                        ?vehicule a mobility:Vélo .
                    } UNION {
                        ?vehicule a mobility:Bus .
                    } UNION {
                        ?vehicule a mobility:Moto .
                    } UNION {
                        ?vehicule a mobility:Trottinette .
                    } UNION {
                        ?vehicule a mobility:Camion .
                    }
                    OPTIONAL { ?vehicule mobility:marque ?marque }
                    OPTIONAL { ?vehicule mobility:modèle ?modele }
                    OPTIONAL { ?vehicule mobility:typeVéhicule ?type }
                    OPTIONAL { ?vehicule mobility:statut ?statut }
                }
                LIMIT 20
                ''',
                'category': 'Véhicules'
            },
            'route-1': {
                'name': 'Routes disponibles',
                'description': 'Liste des routes dans la ville',
                'query': '''
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
                'description': 'Combien d\'utilisateurs sont actifs',
                'query': '''
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
                'description': 'Quel est l\'état du trafic',
                'query': '''
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
            },

            # ===== REQUÊTES AVANCÉES (Version complète) =====
            "all_users": {
                "name": "Tous les utilisateurs",
                "description": "Liste tous les utilisateurs avec leurs informations de base",
                "query": """
                PREFIX mobility: <http://example.org/mobility-ontology/2025/09#>
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
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
                PREFIX mobility: <http://example.org/mobility-ontology/2025/09#>
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                SELECT ?vehicle ?marque ?modele ?couleur ?type ?statut
                WHERE {
                    {
                        ?vehicle rdf:type mobility:Voiture .
                    } UNION {
                        ?vehicle rdf:type mobility:Vélo .
                    } UNION {
                        ?vehicle rdf:type mobility:Bus .
                    } UNION {
                        ?vehicle rdf:type mobility:Moto .
                    } UNION {
                        ?vehicle rdf:type mobility:Trottinette .
                    } UNION {
                        ?vehicle rdf:type mobility:Camion .
                    }
                    OPTIONAL { ?vehicle mobility:marque ?marque }
                    OPTIONAL { ?vehicle mobility:modèle ?modele }
                    OPTIONAL { ?vehicle mobility:couleur ?couleur }
                    OPTIONAL { ?vehicle mobility:statut ?statut }
                    ?vehicle rdf:type ?type .
                    FILTER(?statut = "disponible" || ?statut = "actif")
                }
                ORDER BY ?marque
                """,
                "category": "Véhicules"
            },
            
            "stations_with_location": {
                "name": "Stations avec localisation",
                "description": "Liste toutes les stations avec leurs coordonnées",
                "query": """
                PREFIX mobility: <http://example.org/mobility-ontology/2025/09#>
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
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
                PREFIX mobility: <http://example.org/mobility-ontology/2025/09#>
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
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
                PREFIX mobility: <http://example.org/mobility-ontology/2025/09#>
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                SELECT ?type (COUNT(?vehicle) as ?count)
                WHERE {
                    ?vehicle rdf:type ?type .
                    FILTER(?type = mobility:Vélo || ?type = mobility:Voiture || ?type = mobility:Bus || ?type = mobility:Moto || ?type = mobility:Trottinette || ?type = mobility:Camion)
                }
                GROUP BY ?type
                ORDER BY DESC(?count)
                """,
                "category": "Statistiques"
            },

            # ===== REQUÊTES VÉHICULES SPÉCIFIQUES =====
            
            "electric_vehicles": {
                "name": "Véhicules électriques",
                "description": "Liste tous les véhicules électriques",
                "query": """
                PREFIX mobility: <http://example.org/mobility-ontology/2025/09#>
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                SELECT ?vehicle ?marque ?modele ?type ?batterie ?statut
                WHERE {
                    {
                        ?vehicle rdf:type mobility:Voiture .
                    } UNION {
                        ?vehicle rdf:type mobility:Vélo .
                    } UNION {
                        ?vehicle rdf:type mobility:Bus .
                    } UNION {
                        ?vehicle rdf:type mobility:Moto .
                    } UNION {
                        ?vehicle rdf:type mobility:Trottinette .
                    }
                    ?vehicle mobility:typeVéhicule ?typeVeh .
                    FILTER(CONTAINS(LCASE(?typeVeh), "électrique"))
                    OPTIONAL { ?vehicle mobility:marque ?marque }
                    OPTIONAL { ?vehicle mobility:modèle ?modele }
                    OPTIONAL { ?vehicle mobility:niveauBatterie ?batterie }
                    OPTIONAL { ?vehicle mobility:statut ?statut }
                    ?vehicle rdf:type ?type .
                }
                ORDER BY ?marque
                """,
                "category": "Véhicules"
            },

            "cars_only": {
                "name": "Voitures uniquement",
                "description": "Liste toutes les voitures",
                "query": """
                PREFIX mobility: <http://example.org/mobility-ontology/2025/09#>
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                SELECT ?voiture ?marque ?modele ?couleur ?immatriculation ?statut ?typeVeh
                WHERE {
                    ?voiture rdf:type mobility:Voiture .
                    OPTIONAL { ?voiture mobility:marque ?marque }
                    OPTIONAL { ?voiture mobility:modèle ?modele }
                    OPTIONAL { ?voiture mobility:couleur ?couleur }
                    OPTIONAL { ?voiture mobility:immatriculation ?immatriculation }
                    OPTIONAL { ?voiture mobility:statut ?statut }
                    OPTIONAL { ?voiture mobility:typeVéhicule ?typeVeh }
                }
                ORDER BY ?marque ?modele
                """,
                "category": "Véhicules"
            },

            "bikes_only": {
                "name": "Vélos uniquement",
                "description": "Liste tous les vélos",
                "query": """
                PREFIX mobility: <http://example.org/mobility-ontology/2025/09#>
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                SELECT ?velo ?marque ?modele ?couleur ?statut ?batterie ?station
                WHERE {
                    ?velo rdf:type mobility:Vélo .
                    OPTIONAL { ?velo mobility:marque ?marque }
                    OPTIONAL { ?velo mobility:modèle ?modele }
                    OPTIONAL { ?velo mobility:couleur ?couleur }
                    OPTIONAL { ?velo mobility:statut ?statut }
                    OPTIONAL { ?velo mobility:niveauBatterie ?batterie }
                    OPTIONAL { ?velo mobility:disponibleÀ ?station }
                }
                ORDER BY ?marque ?modele
                """,
                "category": "Véhicules"
            },

            "buses_only": {
                "name": "Bus uniquement", 
                "description": "Liste tous les bus",
                "query": """
                PREFIX mobility: <http://example.org/mobility-ontology/2025/09#>
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                SELECT ?bus ?marque ?modele ?ligne ?capacite ?statut ?localisation
                WHERE {
                    ?bus rdf:type mobility:Bus .
                    OPTIONAL { ?bus mobility:marque ?marque }
                    OPTIONAL { ?bus mobility:modèle ?modele }
                    OPTIONAL { ?bus mobility:ligne ?ligne }
                    OPTIONAL { ?bus mobility:capacité ?capacite }
                    OPTIONAL { ?bus mobility:statut ?statut }
                    OPTIONAL { ?bus mobility:localisation ?localisation }
                }
                ORDER BY ?ligne ?marque
                """,
                "category": "Véhicules"
            },

            # ===== REQUÊTES GESTION TRAFIC =====

            "all_traffic_sensors": {
                "name": "Tous les capteurs de trafic",
                "description": "Liste tous les capteurs de trafic avec leurs informations",
                "query": """
                PREFIX mobility: <http://example.org/mobility-ontology/2025/09#>
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
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
                PREFIX mobility: <http://example.org/mobility-ontology/2025/09#>
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
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
                PREFIX mobility: <http://example.org/mobility-ontology/2025/09#>
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
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
                PREFIX mobility: <http://example.org/mobility-ontology/2025/09#>
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
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

            "high_precision_sensors": {
                "name": "Capteurs haute précision",
                "description": "Liste les capteurs avec une précision de détection > 90%",
                "query": """
                PREFIX mobility: <http://example.org/mobility-ontology/2025/09#>
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
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
                PREFIX mobility: <http://example.org/mobility-ontology/2025/09#>
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
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
            
            "reservations_active": {
                "name": "Réservations actives",
                "description": "Liste toutes les réservations actives",
                "query": """
                PREFIX mobility: <http://example.org/mobility-ontology/2025/09#>
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
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
    
    @staticmethod
    def _get_example_questions():
        """Return example questions for the AI assistant - Fusionné"""
        # Deux exemples simples et robustes par type d'entité, basés sur la structure
        # présente dans `mobility_ontology_clean.rdf` (instances et propriétés courantes).
        return [
            # Utilisateurs
            "Liste tous les utilisateurs",
            "Montre les utilisateurs ayant le rôle 'Administrateur'",

            # Véhicules
         "Montre-moi les voitures",
        "Quels sont les vélos disponibles?",
        "Liste les bus de la ville",

            # Stations
            "Liste les stations avec leurs coordonnées",
            "Montre les stations de type 'StationCentre'",

            # Trajets
            "Liste les trajets dont la distance est supérieure à 5",
            "Montre les trajets dont le pointDépart contient 'paris'",

            # Capteurs
            "Liste les capteurs de trafic actifs",
            "Montre les capteurs avec une précision élevée",

            # Trafic / Routes / Zones
            "Liste les routes où le niveauCirculation est 'fort'",
            "Montre les zones de trafic contenant 'centre'",

            # Locations / Réservations
            "Liste les locations actives",
            "Montre les réservations pour l'utilisateur avec id 2",

            # Autres (général / fallback)
            "Donne-moi quelques exemples d'individus (ex. Trajet, Location, Véhicule)",
            "Affiche les propriétés (labels) associées à une instance donnée"
        ]


# Instances globales pour la compatibilité
ai_processor = AIQueryProcessor()
