"""
Gestionnaire RDF pour l'ontologie de mobilité urbaine
Utilise rdflib pour charger, interroger et manipuler les données RDF
"""

import os
import logging
from typing import List, Dict, Optional, Tuple
from rdflib import Graph, Namespace, URIRef, Literal, BNode
from rdflib.plugins.sparql import prepareQuery
from django.conf import settings

logger = logging.getLogger(__name__)

class RDFManager:
    """Gestionnaire principal pour les opérations RDF"""
    
    def __init__(self):
        self.graph = Graph()
        self.mobility_ns = Namespace(settings.ONTOLOGY_NAMESPACE)
        self.rdf_ns = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
        self.rdfs_ns = Namespace("http://www.w3.org/2000/01/rdf-schema#")
        self.owl_ns = Namespace("http://www.w3.org/2002/07/owl#")
        
        # Bind namespaces for cleaner queries
        self.graph.bind("mobility", self.mobility_ns)
        self.graph.bind("rdf", self.rdf_ns)
        self.graph.bind("rdfs", self.rdfs_ns)
        self.graph.bind("owl", self.owl_ns)
        
        self.load_ontology()
    
    def load_ontology(self) -> bool:
        """Charge l'ontologie RDF depuis le fichier"""
        try:
            if os.path.exists(settings.ONTOLOGY_PATH):
                self.graph.parse(settings.ONTOLOGY_PATH, format="xml")
                logger.info(f"Ontologie chargée avec succès: {len(self.graph)} triplets")
                return True
            else:
                logger.error(f"Fichier ontologie non trouvé: {settings.ONTOLOGY_PATH}")
                return False
        except Exception as e:
            logger.error(f"Erreur lors du chargement de l'ontologie: {e}")
            return False
    
    def get_classes(self) -> List[Dict]:
        """Récupère toutes les classes de l'ontologie"""
        query = """
        SELECT DISTINCT ?cls ?label ?comment
        WHERE {
            ?cls rdf:type owl:Class .
            OPTIONAL { ?cls rdfs:label ?label }
            OPTIONAL { ?cls rdfs:comment ?comment }
        }
        ORDER BY ?cls
        """
        results = []
        for row in self.graph.query(query):
            results.append({
                'uri': str(row.cls),
                'label': str(row.label) if row.label else str(row.cls).split('#')[-1],
                'comment': str(row.comment) if row.comment else ''
            })
        return results
    
    def get_properties(self) -> List[Dict]:
        """Récupère toutes les propriétés (object et data properties)"""
        query = """
        SELECT DISTINCT ?property ?label ?comment ?domain ?range
        WHERE {
            {
                ?property rdf:type owl:ObjectProperty .
            }
            UNION
            {
                ?property rdf:type owl:DatatypeProperty .
            }
            OPTIONAL { ?property rdfs:label ?label }
            OPTIONAL { ?property rdfs:comment ?comment }
            OPTIONAL { ?property rdfs:domain ?domain }
            OPTIONAL { ?property rdfs:range ?range }
        }
        ORDER BY ?property
        """
        results = []
        for row in self.graph.query(query):
            results.append({
                'uri': str(row.property),
                'label': str(row.label) if row.label else str(row.property).split('#')[-1],
                'comment': str(row.comment) if row.comment else '',
                'domain': str(row.domain) if row.domain else '',
                'range': str(row.range) if row.range else ''
            })
        return results
    
    def get_individuals(self, class_uri: Optional[str] = None) -> List[Dict]:
        """Récupère tous les individus ou ceux d'une classe spécifique"""
        if class_uri:
            query = f"""
            SELECT DISTINCT ?individual ?label ?type
            WHERE {{
                ?individual rdf:type <{class_uri}> .
                OPTIONAL {{ ?individual rdfs:label ?label }}
                ?individual rdf:type ?type .
            }}
            ORDER BY ?individual
            """
        else:
            query = """
            SELECT DISTINCT ?individual ?label ?type
            WHERE {
                ?individual rdf:type ?type .
                ?type rdf:type owl:Class .
                OPTIONAL { ?individual rdfs:label ?label }
                FILTER(?type != owl:Class && ?type != owl:ObjectProperty && ?type != owl:DatatypeProperty)
            }
            ORDER BY ?individual
            """
        
        results = []
        for row in self.graph.query(query):
            results.append({
                'uri': str(row.individual),
                'label': str(row.label) if row.label else str(row.individual).split('#')[-1],
                'type': str(row.type) if row.type else ''
            })
        return results
    
    def execute_sparql_query(self, sparql_query: str) -> List[Dict]:
        """Exécute une requête SPARQL personnalisée"""
        try:
            results = []
            query_result = self.graph.query(sparql_query)
            
            # Get column names from the query result
            if hasattr(query_result, 'vars'):
                columns = [str(var) for var in query_result.vars]
            else:
                # Fallback: try to extract from first result
                columns = []
                if query_result:
                    first_result = next(iter(query_result), None)
                    if first_result:
                        columns = [f"col_{i}" for i in range(len(first_result))]
            
            for row in query_result:
                result_dict = {}
                for i, value in enumerate(row):
                    col_name = columns[i] if i < len(columns) else f"col_{i}"
                    if value:
                        result_dict[col_name] = str(value)
                    else:
                        result_dict[col_name] = ""
                results.append(result_dict)
            
            return results
            
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution de la requête SPARQL: {e}")
            raise e
    
    def get_user_data(self) -> List[Dict]:
        """Récupère les données des utilisateurs"""
        query = """
        SELECT ?user ?nom ?email ?typeUtilisateur ?age ?telephone
        WHERE {
            ?user rdf:type mobility:Utilisateur .
            OPTIONAL { ?user mobility:nom ?nom }
            OPTIONAL { ?user mobility:email ?email }
            OPTIONAL { ?user mobility:typeUtilisateur ?typeUtilisateur }
            OPTIONAL { ?user mobility:âge ?age }
            OPTIONAL { ?user mobility:téléphone ?telephone }
        }
        ORDER BY ?nom
        """
        return self.execute_sparql_query(query)
    
    def get_vehicles_data(self) -> List[Dict]:
        """Récupère les données des véhicules"""
        query = """
        SELECT ?vehicle ?marque ?modele ?couleur ?statut ?type
        WHERE {
            {
                ?vehicle rdf:type mobility:Véhicule .
            }
            UNION
            {
                ?vehicle rdf:type mobility:Vélo .
            }
            UNION
            {
                ?vehicle rdf:type mobility:Voiture .
            }
            OPTIONAL { ?vehicle mobility:marque ?marque }
            OPTIONAL { ?vehicle mobility:modèle ?modele }
            OPTIONAL { ?vehicle mobility:couleur ?couleur }
            OPTIONAL { ?vehicle mobility:statut ?statut }
            ?vehicle rdf:type ?type .
        }
        ORDER BY ?marque
        """
        return self.execute_sparql_query(query)
    
    def get_stations_data(self) -> List[Dict]:
        """Récupère les données des stations"""
        query = """
        SELECT ?station ?nomStation ?latitude ?longitude ?adresse ?capacite ?typeStation
        WHERE {
            ?station rdf:type mobility:Station .
            OPTIONAL { ?station mobility:nomStation ?nomStation }
            OPTIONAL { ?station mobility:latitude ?latitude }
            OPTIONAL { ?station mobility:longitude ?longitude }
            OPTIONAL { ?station mobility:adresse ?adresse }
            OPTIONAL { ?station mobility:capacité ?capacite }
            OPTIONAL { ?station mobility:typeStation ?typeStation }
        }
        ORDER BY ?nomStation
        """
        return self.execute_sparql_query(query)
    
    def get_trips_data(self) -> List[Dict]:
        """Récupère les données des trajets"""
        query = """
        SELECT ?trajet ?pointDepart ?pointArrivee ?distance ?duree ?mode ?cout ?utilisateur
        WHERE {
            ?trajet rdf:type mobility:Trajet .
            OPTIONAL { ?trajet mobility:pointDépart ?pointDepart }
            OPTIONAL { ?trajet mobility:pointArrivée ?pointArrivee }
            OPTIONAL { ?trajet mobility:distance ?distance }
            OPTIONAL { ?trajet mobility:durée ?duree }
            OPTIONAL { ?trajet mobility:mode ?mode }
            OPTIONAL { ?trajet mobility:coût ?cout }
            OPTIONAL { ?trajet mobility:effectuéPar ?utilisateur }
        }
        ORDER BY ?pointDepart
        """
        return self.execute_sparql_query(query)
    
    def get_traffic_data(self) -> List[Dict]:
        """Récupère les données de trafic (routes et transport public)"""
        query = """
        SELECT ?entity ?nom ?type ?distance ?temps ?statut
        WHERE {
            {
                ?entity rdf:type mobility:Route .
                OPTIONAL { ?entity mobility:nomRoute ?nom }
                OPTIONAL { ?entity mobility:distanceRoute ?distance }
                OPTIONAL { ?entity mobility:tempsEstimé ?temps }
                OPTIONAL { ?entity mobility:typeRoute ?type }
                BIND("Route" as ?statut)
            }
            UNION
            {
                ?entity rdf:type mobility:TransportPublic .
                OPTIONAL { ?entity mobility:ligne ?nom }
                OPTIONAL { ?entity mobility:typeTransport ?type }
                BIND("Transport Public" as ?statut)
            }
        }
        ORDER BY ?nom
        """
        return self.execute_sparql_query(query)
    
    def search_by_keyword(self, keyword: str) -> List[Dict]:
        """Recherche par mot-clé dans l'ontologie"""
        keyword_lower = keyword.lower()
        query = f"""
        SELECT DISTINCT ?subject ?predicate ?object ?type
        WHERE {{
            ?subject ?predicate ?object .
            ?subject rdf:type ?type .
            FILTER(
                CONTAINS(LCASE(STR(?subject)), "{keyword_lower}") ||
                CONTAINS(LCASE(STR(?object)), "{keyword_lower}") ||
                CONTAINS(LCASE(STR(?predicate)), "{keyword_lower}")
            )
            FILTER(?type != owl:Class && ?type != owl:ObjectProperty && ?type != owl:DatatypeProperty)
        }}
        LIMIT 50
        """
        return self.execute_sparql_query(query)
    
    def get_statistics(self) -> Dict:
        """Récupère des statistiques sur l'ontologie"""
        stats = {
            'total_triples': len(self.graph),
            'total_classes': 0,
            'total_properties': 0,
            'total_individuals': 0,
        }
        
        # Compter les classes
        classes_query = """
        SELECT (COUNT(DISTINCT ?class) as ?count)
        WHERE {
            ?class rdf:type owl:Class .
        }
        """
        try:
            result = list(self.graph.query(classes_query))
            if result and result[0]:
                stats['total_classes'] = int(result[0][0])
        except Exception as e:
            logger.warning(f"Erreur lors du comptage des classes: {e}")
        
        # Compter les propriétés
        properties_query = """
        SELECT (COUNT(DISTINCT ?property) as ?count)
        WHERE {
            {
                ?property rdf:type owl:ObjectProperty .
            }
            UNION
            {
                ?property rdf:type owl:DatatypeProperty .
            }
        }
        """
        try:
            result = list(self.graph.query(properties_query))
            if result and result[0]:
                stats['total_properties'] = int(result[0][0])
        except Exception as e:
            logger.warning(f"Erreur lors du comptage des propriétés: {e}")
        
        # Compter les individus (instances de classes)
        individuals_query = """
        SELECT (COUNT(DISTINCT ?individual) as ?count)
        WHERE {
            ?individual rdf:type ?class .
            ?class rdf:type owl:Class .
        }
        """
        try:
            result = list(self.graph.query(individuals_query))
            if result and result[0]:
                stats['total_individuals'] = int(result[0][0])
        except Exception as e:
            logger.warning(f"Erreur lors du comptage des individus: {e}")
        
        return stats


# Instance globale du gestionnaire RDF
rdf_manager = RDFManager()