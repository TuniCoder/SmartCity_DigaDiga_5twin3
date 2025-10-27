"""
Gestionnaire RDF pour l'ontologie de mobilité urbaine
Utilise rdflib pour charger, interroger et manipuler les données RDF
"""

import os
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from rdflib import Graph, Namespace, URIRef, Literal, BNode, XSD
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
    
    def save_ontology(self) -> bool:
        """Sauvegarde l'ontologie RDF dans le fichier"""
        try:
            # Créer un backup avant de sauvegarder
            if os.path.exists(settings.ONTOLOGY_PATH):
                backup_path = str(settings.ONTOLOGY_PATH) + '.backup'
                import shutil
                shutil.copy2(settings.ONTOLOGY_PATH, backup_path)
                logger.info(f"Backup créé: {backup_path}")
            
            # Sauvegarder le graphe
            self.graph.serialize(destination=str(settings.ONTOLOGY_PATH), format='xml', encoding='utf-8')
            logger.info(f"Ontologie sauvegardée avec succès: {len(self.graph)} triplets")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de l'ontologie: {e}")
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
            'entities_by_type': {}
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
        
        # Compter les entités par type
        entities_by_type_query = """
        SELECT ?type (COUNT(?individual) as ?count)
        WHERE {
            ?individual rdf:type ?type .
            ?type rdf:type owl:Class .
        }
        GROUP BY ?type
        ORDER BY DESC(?count)
        """
        try:
            results = self.execute_sparql_query(entities_by_type_query)
            entities_by_type = {}
            for result in results:
                if 'type' in result and 'count' in result:
                    # Extraire le nom de la classe (après le #)
                    type_name = result['type'].split('#')[-1] if '#' in result['type'] else result['type']
                    entities_by_type[type_name] = int(result['count'])
            stats['entities_by_type'] = entities_by_type
        except Exception as e:
            logger.warning(f"Erreur lors du comptage des entités par type: {e}")
            stats['entities_by_type'] = {}

        return stats
    
    def get_transport_modes_from_rdf(self) -> List[str]:
        """Récupère toutes les valeurs uniques de mode de transport depuis l'ontologie"""
        query = """
        SELECT DISTINCT ?mode
        WHERE {
            ?trajet rdf:type mobility:Trajet .
            ?trajet mobility:mode ?mode .
        }
        ORDER BY ?mode
        """
        try:
            results = self.execute_sparql_query(query)
            modes = [result['mode'] for result in results if 'mode' in result and result['mode']]
            return sorted(list(set(modes)))  # Retirer les doublons et trier
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des modes de transport: {e}")
            return []
    
    def get_vehicle_types_from_rdf(self) -> List[str]:
        """Récupère toutes les valeurs uniques de type de véhicule depuis l'ontologie"""
        query = """
        SELECT DISTINCT ?vehiculeType
        WHERE {
            ?trajet rdf:type mobility:Trajet .
            ?trajet mobility:vehiculeType ?vehiculeType .
        }
        ORDER BY ?vehiculeType
        """
        try:
            results = self.execute_sparql_query(query)
            types = [result['vehiculeType'] for result in results if 'vehiculeType' in result and result['vehiculeType']]
            return sorted(list(set(types)))  # Retirer les doublons et trier
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des types de véhicules: {e}")
            return []


    # ==========================================
    # MÉTHODES CRUD POUR TRAJETS (Web Sémantique)
    # ==========================================
    
    def create_trajet(self, trajet_data: Dict) -> Tuple[bool, str]:
        """
        Crée un nouveau trajet dans l'ontologie RDF
        
        Args:
            trajet_data: Dictionnaire avec les données du trajet
                - Nouvelles propriétés (depuis migration RDF):
                  - utilisateur_id, utilisateur_username, demande_id
                  - lieu_depart, lieu_arrivee, rang
                  - duree_minutes, distance_km, cout_total
                  - empreinte_carbone_g, score_confort, niveau_circulation
                  - retard_estime, fiabilite_score, score_ia
                  - vehicule_nom, vehicule_type
                  - zone_geographique, distance_reelle_km
                  - etapes_json, facteurs_decision, alertes_trafic, horaires_transport, coherence_geo
        
        Returns:
            Tuple (success: bool, trajet_uri: str)
        """
        try:
            import time
            from datetime import datetime
            
            # Créer un ID unique avec timestamp + microsecondes + rang pour éviter les doublons
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            microsec = int(time.time() * 1000000) % 1000  # Microsecondes
            rang = trajet_data.get('rang', 0)
            trajet_id = trajet_data.get('id_unique', f"Trajet_{timestamp}_{microsec}_{rang}")
            trajet_uri = self.mobility_ns[trajet_id]
            
            # Vérifier si le trajet existe déjà
            if (trajet_uri, None, None) in self.graph:
                # Régénérer avec un nouveau timestamp
                trajet_id = f"Trajet_{int(time.time() * 1000000)}"
                trajet_uri = self.mobility_ns[trajet_id]
            
            # Ajouter le type
            self.graph.add((trajet_uri, self.rdf_ns.type, self.mobility_ns.Trajet))
            
            # Ajouter le label
            label = f"{trajet_data.get('lieu_depart', 'Départ')} → {trajet_data.get('lieu_arrivee', 'Arrivée')}"
            self.graph.add((trajet_uri, self.rdfs_ns.label, Literal(label, lang='fr')))
            
            # **NOUVELLES PROPRIÉTÉS** : Mapping des champs vers les propriétés RDF
            property_mappings = {
                'utilisateur_id': (self.mobility_ns.utilisateurId, XSD.string),
                'utilisateur_username': (self.mobility_ns.utilisateurUsername, XSD.string),
                'demande_id': (self.mobility_ns.demandeId, XSD.string),
                'lieu_depart': (self.mobility_ns.pointDépart, XSD.string),
                'lieu_arrivee': (self.mobility_ns.pointArrivée, XSD.string),
                'rang': (self.mobility_ns.rang, XSD.integer),
                'duree_minutes': (self.mobility_ns.durée, XSD.float),
                'distance_km': (self.mobility_ns.distance, XSD.float),
                'cout_total': (self.mobility_ns.coût, XSD.float),
                'empreinte_carbone_g': (self.mobility_ns.empreinteCarbone, XSD.float),
                'score_confort': (self.mobility_ns.scoreConfort, XSD.integer),
                'niveau_circulation': (self.mobility_ns.niveauCirculation, XSD.string),
                'retard_estime': (self.mobility_ns.retardEstime, XSD.integer),
                'fiabilite_score': (self.mobility_ns.fiabiliteScore, XSD.float),
                'score_ia': (self.mobility_ns.scoreIA, XSD.float),
                'vehicule_nom': (self.mobility_ns.mode, XSD.string),
                'vehicule_type': (self.mobility_ns.vehiculeType, XSD.string),
                'zone_geographique': (self.mobility_ns.zoneGeographique, XSD.string),
                'distance_reelle_km': (self.mobility_ns.distanceReelle, XSD.float),
                'etapes_json': (self.mobility_ns.etapesJson, XSD.string),
                'facteurs_decision': (self.mobility_ns.facteursDecision, XSD.string),
                'alertes_trafic': (self.mobility_ns.alertesTrafic, XSD.string),
                'horaires_transport': (self.mobility_ns.horairesTransport, XSD.string),
                'coherence_geo': (self.mobility_ns.coherenceGeo, XSD.string),
            }
            
            # Ajouter toutes les propriétés présentes
            for key, (predicate, datatype) in property_mappings.items():
                if key in trajet_data and trajet_data[key] is not None:
                    value = trajet_data[key]
                    
                    # Conversion de type si nécessaire
                    if datatype == XSD.float:
                        value = float(value)
                    elif datatype == XSD.integer:
                        value = int(value)
                    elif datatype == XSD.string:
                        value = str(value)
                    
                    self.graph.add((trajet_uri, predicate, Literal(value, datatype=datatype)))
            
            # Sauvegarder dans le fichier RDF
            if self.save_ontology():
                logger.info(f"✅ Trajet créé avec succès: {trajet_id}")
                return True, str(trajet_uri)
            else:
                return False, "Erreur lors de la sauvegarde"
                
        except Exception as e:
            logger.error(f"❌ Erreur lors de la création du trajet: {e}")
            return False, str(e)
    
    def update_trajet(self, trajet_id: str, trajet_data: Dict) -> Tuple[bool, str]:
        """
        Met à jour un trajet existant dans l'ontologie
        
        Args:
            trajet_id: Identifiant du trajet à modifier
            trajet_data: Nouvelles données (mêmes clés que create_trajet)
        
        Returns:
            Tuple (success: bool, message: str)
        """
        try:
            trajet_uri = self.mobility_ns[trajet_id]
            
            # Vérifier que le trajet existe
            if (trajet_uri, self.rdf_ns.type, self.mobility_ns.Trajet) not in self.graph:
                return False, f"Le trajet {trajet_id} n'existe pas"
            
            # Supprimer les anciennes valeurs et ajouter les nouvelles
            properties_map = {
                'point_depart': (self.mobility_ns.pointDépart, XSD.string),
                'point_arrivee': (self.mobility_ns.pointArrivée, XSD.string),
                'distance': (self.mobility_ns.distance, XSD.float),
                'duree': (self.mobility_ns.durée, XSD.float),
                'mode': (self.mobility_ns.mode, XSD.string),
                'cout': (self.mobility_ns.coût, XSD.float),
                'heure_debut': (self.mobility_ns.heureDebut, XSD.dateTime),
            }
            
            for key, (predicate, datatype) in properties_map.items():
                if key in trajet_data:
                    # Supprimer l'ancienne valeur
                    self.graph.remove((trajet_uri, predicate, None))
                    
                    # Ajouter la nouvelle valeur
                    value = trajet_data[key]
                    if datatype in [XSD.float, XSD.int]:
                        value = float(value) if datatype == XSD.float else int(value)
                    self.graph.add((trajet_uri, predicate, Literal(value, datatype=datatype)))
            
            # Mettre à jour la relation utilisateur si fournie
            if 'utilisateur_uri' in trajet_data:
                self.graph.remove((trajet_uri, self.mobility_ns.effectuéPar, None))
                user_uri = URIRef(trajet_data['utilisateur_uri'])
                self.graph.add((trajet_uri, self.mobility_ns.effectuéPar, user_uri))
            
            # Sauvegarder
            if self.save_ontology():
                logger.info(f"Trajet mis à jour: {trajet_id}")
                return True, "Trajet mis à jour avec succès"
            else:
                return False, "Erreur lors de la sauvegarde"
                
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du trajet: {e}")
            return False, str(e)
    
    def delete_trajet(self, trajet_id: str) -> Tuple[bool, str]:
        """
        Supprime un trajet de l'ontologie
        
        Args:
            trajet_id: Identifiant du trajet à supprimer
        
        Returns:
            Tuple (success: bool, message: str)
        """
        try:
            trajet_uri = self.mobility_ns[trajet_id]
            
            # Vérifier que le trajet existe
            if (trajet_uri, self.rdf_ns.type, self.mobility_ns.Trajet) not in self.graph:
                return False, f"Le trajet {trajet_id} n'existe pas"
            
            # Supprimer tous les triplets où le trajet est sujet
            self.graph.remove((trajet_uri, None, None))
            
            # Supprimer tous les triplets où le trajet est objet
            self.graph.remove((None, None, trajet_uri))
            
            # Sauvegarder
            if self.save_ontology():
                logger.info(f"Trajet supprimé: {trajet_id}")
                return True, "Trajet supprimé avec succès"
            else:
                return False, "Erreur lors de la sauvegarde"
                
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du trajet: {e}")
            return False, str(e)
    
    def get_trajet_by_id(self, trajet_id: str) -> Optional[Dict]:
        """
        Récupère un trajet spécifique par son ID
        
        Args:
            trajet_id: Identifiant du trajet
        
        Returns:
            Dictionnaire avec les données du trajet ou None
        """
        try:
            trajet_uri = self.mobility_ns[trajet_id]
            
            # Vérifier que le trajet existe
            if (trajet_uri, self.rdf_ns.type, self.mobility_ns.Trajet) not in self.graph:
                return None
            
            trajet_data = {'id': trajet_id, 'uri': str(trajet_uri)}
            
            # Récupérer toutes les propriétés
            for s, p, o in self.graph.triples((trajet_uri, None, None)):
                predicate_name = str(p).split('#')[-1]
                trajet_data[predicate_name] = str(o)
            
            return trajet_data
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du trajet: {e}")
            return None
    
    def get_trajets_by_user(self, user_id: str) -> List[Dict]:
        """
        Récupère tous les trajets d'un utilisateur spécifique
        
        Args:
            user_id: Identifiant de l'utilisateur
        
        Returns:
            Liste de trajets
        """
        query = f"""
        SELECT ?trajet ?pointDepart ?pointArrivee ?distance ?duree ?mode ?cout ?heureDebut
        WHERE {{
            ?trajet rdf:type mobility:Trajet .
            ?trajet mobility:effectuéPar mobility:{user_id} .
            OPTIONAL {{ ?trajet mobility:pointDépart ?pointDepart }}
            OPTIONAL {{ ?trajet mobility:pointArrivée ?pointArrivee }}
            OPTIONAL {{ ?trajet mobility:distance ?distance }}
            OPTIONAL {{ ?trajet mobility:durée ?duree }}
            OPTIONAL {{ ?trajet mobility:mode ?mode }}
            OPTIONAL {{ ?trajet mobility:coût ?cout }}
            OPTIONAL {{ ?trajet mobility:heureDebut ?heureDebut }}
        }}
        ORDER BY DESC(?heureDebut)
        """
        return self.execute_sparql_query(query)


    def list_trajets(self, filtre_utilisateur=None, filtre_demande=None):
        """Liste tous les trajets avec filtres optionnels"""
        try:
            trajets = []
            for trajet_uri in self.graph.subjects(self.rdf_ns.type, self.mobility_ns.Trajet):
                trajet_data = {'uri': str(trajet_uri)}
                for s, p, o in self.graph.triples((trajet_uri, None, None)):
                    predicate_name = str(p).split('#')[-1]
                    trajet_data[predicate_name] = str(o)
                if filtre_utilisateur is not None:
                    if 'utilisateurId' not in trajet_data or str(trajet_data['utilisateurId']) != str(filtre_utilisateur):
                        continue
                if filtre_demande is not None:
                    if 'demandeId' not in trajet_data or str(trajet_data['demandeId']) != str(filtre_demande):
                        continue
                trajets.append(trajet_data)
            return trajets
        except Exception as e:
            return []

    def add_trajet_to_rdf(self, trajet_data: Dict) -> Tuple[bool, str]:
        """
        Ajoute un nouveau trajet dans l'ontologie RDF
        
        Args:
            trajet_data: Dictionnaire contenant les données du trajet
        
        Returns:
            Tuple (succès, message/uri)
        """
        try:
            import time
            import random
            
            # Générer un URI unique pour le trajet
            timestamp = str(int(time.time()))
            random_id = str(random.randint(100, 999))
            trajet_id = f"Trajet_{timestamp}_{random_id}"
            trajet_uri = self.mobility_ns[trajet_id]
            
            # Ajouter le type du trajet
            self.graph.add((trajet_uri, self.rdf_ns.type, self.mobility_ns.Trajet))
            
            # Ajouter le label français
            label = f"{trajet_data.get('pointDepart', 'Départ')} → {trajet_data.get('pointArrivee', 'Arrivée')}"
            self.graph.add((trajet_uri, self.rdfs_ns.label, Literal(label, lang="fr")))
            
            # Mapping des propriétés
            property_mappings = {
                'utilisateurUsername': 'utilisateurUsername',
                'pointDepart': 'pointDépart',
                'pointArrivee': 'pointArrivée',
                'duree': 'durée',
                'distance': 'distance',
                'cout': 'coût',
                'mode': 'mode',
                'vehiculeType': 'vehiculeType',
                'empreinteCarbone': 'empreinteCarbone',
                'scoreConfort': 'scoreConfort',
                'niveauCirculation': 'niveauCirculation',
                'scoreIA': 'scoreIA',
                'fiabiliteScore': 'fiabiliteScore',
                'zoneGeographique': 'zoneGeographique',
                'etapesJson': 'etapesJson'
            }
            
            # Ajouter les propriétés du trajet
            for input_key, rdf_property in property_mappings.items():
                if input_key in trajet_data and trajet_data[input_key] is not None:
                    value = trajet_data[input_key]
                    property_uri = self.mobility_ns[rdf_property]
                    
                    # Typage des données selon la propriété
                    if input_key in ['duree', 'distance', 'cout', 'empreinteCarbone', 'scoreIA', 'fiabiliteScore']:
                        # Propriétés numériques flottantes
                        literal_value = Literal(float(value), datatype="http://www.w3.org/2001/XMLSchema#float")
                    elif input_key in ['scoreConfort']:
                        # Propriétés entières
                        literal_value = Literal(int(value), datatype="http://www.w3.org/2001/XMLSchema#integer")
                    else:
                        # Propriétés textuelles
                        literal_value = Literal(str(value), datatype="http://www.w3.org/2001/XMLSchema#string")
                    
                    self.graph.add((trajet_uri, property_uri, literal_value))
            
            # Ajouter des propriétés calculées et par défaut
            self.graph.add((trajet_uri, self.mobility_ns.rang, Literal(1, datatype="http://www.w3.org/2001/XMLSchema#integer")))
            self.graph.add((trajet_uri, self.mobility_ns.retardEstime, Literal(0, datatype="http://www.w3.org/2001/XMLSchema#integer")))
            
            # Calculer la distance réelle (égale à la distance pour simplifier)
            if 'distance' in trajet_data:
                self.graph.add((trajet_uri, self.mobility_ns.distanceReelle, 
                              Literal(float(trajet_data['distance']), datatype="http://www.w3.org/2001/XMLSchema#float")))
            
            # Ajouter des listes JSON par défaut si non fournies
            default_lists = {
                'facteursDecision': '["Trajet manuel"]',
                'alertesTrafic': '[]',
                'horairesTransport': '{}'
            }
            
            for prop, default_value in default_lists.items():
                if prop not in trajet_data:
                    self.graph.add((trajet_uri, self.mobility_ns[prop], 
                                  Literal(default_value, datatype="http://www.w3.org/2001/XMLSchema#string")))
            
            # Ajouter la cohérence géographique par défaut
            coherence_geo = '{"est_adapte": true, "raison": "Trajet ajouté manuellement", "zone": "locale", "explication": "✅ Trajet validé par utilisateur"}'
            self.graph.add((trajet_uri, self.mobility_ns.coherenceGeo, 
                          Literal(coherence_geo, datatype="http://www.w3.org/2001/XMLSchema#string")))
            
            # Sauvegarder l'ontologie
            if self.save_ontology():
                logger.info(f"Trajet ajouté avec succès: {trajet_id}")
                return True, str(trajet_uri)
            else:
                return False, "Erreur lors de la sauvegarde"
                
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout du trajet: {e}")
            return False, str(e)

    def add_user_to_rdf(self, user_id: str, nom: str, prenom: str, email: str, 
                       telephone: str = "", role: str = "user") -> bool:
        """
        Ajoute un utilisateur à l'ontologie RDF
        
        Args:
            user_id: Identifiant unique de l'utilisateur
            nom: Nom de famille
            prenom: Prénom
            email: Adresse email
            telephone: Numéro de téléphone (optionnel)
            role: Rôle de l'utilisateur (user, admin)
        
        Returns:
            bool: True si l'ajout a réussi, False sinon
        """
        try:
            # Créer l'URI de l'utilisateur
            user_uri = self.mobility_ns[f"Utilisateur{user_id}"]
            
            # Vérifier si l'utilisateur existe déjà
            if (user_uri, None, None) in self.graph:
                logger.warning(f"L'utilisateur {user_id} existe déjà dans le RDF")
                return True
            
            # Ajouter le type
            self.graph.add((user_uri, self.rdf_ns.type, self.mobility_ns.Utilisateur))
            
            # Ajouter les propriétés de base
            self.graph.add((user_uri, self.mobility_ns.utilisateurId, 
                          Literal(user_id, datatype="http://www.w3.org/2001/XMLSchema#string")))
            self.graph.add((user_uri, self.mobility_ns.nom, 
                          Literal(nom, datatype="http://www.w3.org/2001/XMLSchema#string")))
            self.graph.add((user_uri, self.mobility_ns.prenom, 
                          Literal(prenom, datatype="http://www.w3.org/2001/XMLSchema#string")))
            self.graph.add((user_uri, self.mobility_ns.email, 
                          Literal(email, datatype="http://www.w3.org/2001/XMLSchema#string")))
            
            # Ajouter le téléphone si fourni
            if telephone:
                self.graph.add((user_uri, self.mobility_ns.telephone, 
                              Literal(telephone, datatype="http://www.w3.org/2001/XMLSchema#string")))
            
            # Ajouter le rôle
            self.graph.add((user_uri, self.mobility_ns.role, 
                          Literal(role, datatype="http://www.w3.org/2001/XMLSchema#string")))
            
            # Ajouter des propriétés par défaut
            self.graph.add((user_uri, self.mobility_ns.dateInscription, 
                          Literal(str(datetime.now().isoformat()), datatype="http://www.w3.org/2001/XMLSchema#dateTime")))
            self.graph.add((user_uri, self.mobility_ns.statut, 
                          Literal("actif", datatype="http://www.w3.org/2001/XMLSchema#string")))
            self.graph.add((user_uri, self.mobility_ns.preferencesTrajet, 
                          Literal('{"mode_prefere": "auto", "distance_max": 50}', datatype="http://www.w3.org/2001/XMLSchema#string")))
            
            # Sauvegarder l'ontologie
            if self.save_ontology():
                logger.info(f"Utilisateur {user_id} ajouté avec succès au RDF")
                return True
            else:
                logger.error(f"Erreur lors de la sauvegarde de l'utilisateur {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout de l'utilisateur {user_id} au RDF: {e}")
            return False

    def update_user_role_in_rdf(self, user_id: str, new_role: str) -> bool:
        """
        Met à jour le rôle d'un utilisateur dans l'ontologie RDF
        
        Args:
            user_id: Identifiant de l'utilisateur
            new_role: Nouveau rôle (user, admin)
        
        Returns:
            bool: True si la mise à jour a réussi, False sinon
        """
        try:
            # Créer l'URI de l'utilisateur
            user_uri = self.mobility_ns[f"Utilisateur{user_id}"]
            
            # Vérifier si l'utilisateur existe
            if (user_uri, self.rdf_ns.type, self.mobility_ns.Utilisateur) not in self.graph:
                logger.warning(f"L'utilisateur {user_id} n'existe pas dans le RDF")
                return False
            
            # Supprimer l'ancien rôle
            old_role_triples = list(self.graph.triples((user_uri, self.mobility_ns.role, None)))
            for triple in old_role_triples:
                self.graph.remove(triple)
            
            # Ajouter le nouveau rôle
            self.graph.add((user_uri, self.mobility_ns.role, 
                          Literal(new_role, datatype="http://www.w3.org/2001/XMLSchema#string")))
            
            # Mettre à jour la date de modification
            # Supprimer l'ancienne date de modification si elle existe
            old_date_triples = list(self.graph.triples((user_uri, self.mobility_ns.dateModification, None)))
            for triple in old_date_triples:
                self.graph.remove(triple)
            
            # Ajouter la nouvelle date
            self.graph.add((user_uri, self.mobility_ns.dateModification, 
                          Literal(str(datetime.now().isoformat()), datatype="http://www.w3.org/2001/XMLSchema#dateTime")))
            
            # Sauvegarder l'ontologie
            if self.save_ontology():
                logger.info(f"Rôle de l'utilisateur {user_id} mis à jour vers '{new_role}' dans le RDF")
                return True
            else:
                logger.error(f"Erreur lors de la sauvegarde du changement de rôle pour l'utilisateur {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du rôle de l'utilisateur {user_id} dans le RDF: {e}")
            return False

    def get_user_from_rdf(self, user_id: str) -> dict:
        """
        Récupère les informations d'un utilisateur depuis l'ontologie RDF
        
        Args:
            user_id: Identifiant de l'utilisateur
        
        Returns:
            dict: Informations de l'utilisateur ou dict vide si non trouvé
        """
        try:
            user_uri = self.mobility_ns[f"Utilisateur{user_id}"]
            
            # Vérifier si l'utilisateur existe
            if (user_uri, self.rdf_ns.type, self.mobility_ns.Utilisateur) not in self.graph:
                return {}
            
            # Requête pour récupérer toutes les propriétés de l'utilisateur
            query = f"""
            SELECT ?property ?value
            WHERE {{
                <{user_uri}> ?property ?value .
            }}
            """
            
            results = self.execute_sparql_query(query)
            user_data = {'user_id': user_id, 'uri': str(user_uri)}
            
            for result in results:
                if 'property' in result and 'value' in result:
                    # Extraire le nom de la propriété
                    prop_name = result['property'].split('#')[-1] if '#' in result['property'] else result['property']
                    user_data[prop_name] = result['value']
            
            return user_data
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'utilisateur {user_id} depuis le RDF: {e}")
            return {}

    def sync_user_to_rdf(self, user_django) -> bool:
        """
        Synchronise un utilisateur Django vers l'ontologie RDF
        
        Args:
            user_django: Instance de User Django
        
        Returns:
            bool: True si la synchronisation a réussi, False sinon
        """
        try:
            # Récupérer le profil utilisateur
            from ..gestion_utilisateurs.models import ProfilUtilisateur
            try:
                profil = ProfilUtilisateur.objects.get(user=user_django)
                role = profil.role
                telephone = profil.telephone or ""
            except ProfilUtilisateur.DoesNotExist:
                role = "user"
                telephone = ""
            
            # Vérifier si l'utilisateur existe déjà dans le RDF
            existing_user = self.get_user_from_rdf(str(user_django.id))
            
            if existing_user:
                # Mettre à jour le rôle si nécessaire
                current_role = existing_user.get('role', 'user')
                if current_role != role:
                    return self.update_user_role_in_rdf(str(user_django.id), role)
                return True
            else:
                # Ajouter l'utilisateur
                return self.add_user_to_rdf(
                    user_id=str(user_django.id),
                    nom=user_django.last_name,
                    prenom=user_django.first_name,
                    email=user_django.email,
                    telephone=telephone,
                    role=role
                )
                
        except Exception as e:
            logger.error(f"Erreur lors de la synchronisation de l'utilisateur {user_django.username} vers le RDF: {e}")
            return False

    def delete_user_from_rdf(self, user_id: str) -> bool:
        """
        Supprime un utilisateur de l'ontologie RDF
        
        Args:
            user_id: Identifiant de l'utilisateur à supprimer
        
        Returns:
            bool: True si la suppression a réussi, False sinon
        """
        try:
            # Créer l'URI de l'utilisateur
            user_uri = self.mobility_ns[f"Utilisateur{user_id}"]
            
            # Vérifier si l'utilisateur existe
            if (user_uri, self.rdf_ns.type, self.mobility_ns.Utilisateur) not in self.graph:
                logger.warning(f"L'utilisateur {user_id} n'existe pas dans le RDF")
                return True  # Considéré comme succès si déjà absent
            
            # Supprimer tous les triplets liés à cet utilisateur
            triples_to_remove = list(self.graph.triples((user_uri, None, None)))
            for triple in triples_to_remove:
                self.graph.remove(triple)
            
            # Supprimer aussi les triplets où l'utilisateur est objet
            triples_as_object = list(self.graph.triples((None, None, user_uri)))
            for triple in triples_as_object:
                self.graph.remove(triple)
            
            # Sauvegarder l'ontologie
            if self.save_ontology():
                logger.info(f"Utilisateur {user_id} supprimé avec succès du RDF")
                return True
            else:
                logger.error(f"Erreur lors de la sauvegarde après suppression de l'utilisateur {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de l'utilisateur {user_id} du RDF: {e}")
            return False


    # ==========================================
    # MÉTHODES CRUD POUR LOCATIONS (Web Sémantique)
    # ==========================================
    
    def _get_location_uri_by_numero(self, numero_location: str) -> Optional[URIRef]:
        """
        Helper function to get the URI of a location by its numeroLocation.
        """
        query = """
            SELECT ?location_uri
            WHERE {
                ?location_uri mobility:numeroLocation ?numero .
            }
            """
        
        prepared_query = prepareQuery(query, initNs={"mobility": self.mobility_ns})
        
        for row in self.graph.query(prepared_query, initBindings={'numero': Literal(numero_location, datatype=XSD.string)}):
            return row.location_uri
        
        return None

    def create_location(self, location_data: Dict) -> Tuple[bool, str]:
        """
        Crée une nouvelle location dans l'ontologie RDF
        
        Args:
            location_data: Dictionnaire avec les données de la location
                - Propriétés principales:
                  - utilisateur_id, utilisateur_username, vehicule_id
                  - numero_location, type_location, statut
                  - date_debut, date_fin, lieu_prise, lieu_retour
                  - conducteur_principal, prix_total_calcule
                  - kilometrage_depart, etat_depart
                  - options_choisies, services_additionnels
                  - assurance_comprise, franchise_assurance
        
        Returns:
            Tuple (success: bool, location_uri: str)
        """
        try:
            import time
            from datetime import datetime
            
            # Créer un ID unique avec timestamp + microsecondes
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            microsec = int(time.time() * 1000000) % 1000
            location_id = location_data.get('id_unique', f"Location_{timestamp}_{microsec}")
            location_uri = self.mobility_ns[location_id]
            
            # Vérifier si la location existe déjà
            if (location_uri, None, None) in self.graph:
                location_id = f"Location_{int(time.time() * 1000000)}"
                location_uri = self.mobility_ns[location_id]
            
            # Ajouter le type
            self.graph.add((location_uri, self.rdf_ns.type, self.mobility_ns.Location))
            
            # Ajouter le label
            label = f"Location {location_data.get('numero_location', 'N/A')} - {location_data.get('conducteur_principal', 'Client')}"
            self.graph.add((location_uri, self.rdfs_ns.label, Literal(label, lang='fr')))
            
            # **NOUVELLES PROPRIÉTÉS** : Mapping des champs vers les propriétés RDF
            property_mappings = {
                'utilisateur_id': (self.mobility_ns.utilisateurId, XSD.string),
                'utilisateur_username': (self.mobility_ns.utilisateurUsername, XSD.string),
                'vehicule_id': (self.mobility_ns.vehiculeId, XSD.string),
                'numero_location': (self.mobility_ns.numeroLocation, XSD.string),
                'type_location': (self.mobility_ns.typeLocation, XSD.string),
                'statut': (self.mobility_ns.statutLocation, XSD.string),
                'date_debut': (self.mobility_ns.dateDebutLocation, XSD.dateTime),
                'date_fin': (self.mobility_ns.dateFinLocation, XSD.dateTime),
                'lieu_prise': (self.mobility_ns.lieuPrise, XSD.string),
                'lieu_retour': (self.mobility_ns.lieuRetour, XSD.string),
                'conducteur_principal': (self.mobility_ns.conducteurPrincipal, XSD.string),
                'conducteur_secondaire': (self.mobility_ns.conducteurSecondaire, XSD.string),
                'numero_permis': (self.mobility_ns.numeroPermis, XSD.string),
                'prix_total_calcule': (self.mobility_ns.prixTotalCalcule, XSD.float),
                'prix_total_final': (self.mobility_ns.prixTotalFinal, XSD.float),
                'caution_payee': (self.mobility_ns.cautionPayee, XSD.float),
                'caution_rendue': (self.mobility_ns.cautionRendue, XSD.float),
                'kilometrage_depart': (self.mobility_ns.kilometrageDepart, XSD.float),
                'kilometrage_retour': (self.mobility_ns.kilometrageRetour, XSD.float),
                'kilometrage_total': (self.mobility_ns.kilometrageTotal, XSD.float),
                'etat_depart': (self.mobility_ns.etatDepart, XSD.string),
                'etat_retour': (self.mobility_ns.etatRetour, XSD.string),
                'dommages_signales': (self.mobility_ns.dommagesSignales, XSD.string),
                'options_choisies': (self.mobility_ns.optionsChoisies, XSD.string),
                'services_additionnels': (self.mobility_ns.servicesAdditionnels, XSD.string),
                'assurance_comprise': (self.mobility_ns.assuranceComprise, XSD.boolean),
                'franchise_assurance': (self.mobility_ns.franchiseAssurance, XSD.float),
                'assurance_supplementaire': (self.mobility_ns.assuranceSupplementaire, XSD.boolean),
                'commentaires_client': (self.mobility_ns.commentairesClient, XSD.string),
                'note_experience': (self.mobility_ns.noteExperience, XSD.integer),
                'est_recurrente': (self.mobility_ns.estRecurrente, XSD.boolean),
                'frequence_recurrence': (self.mobility_ns.frequenceRecurrence, XSD.string),
                'cree_par_admin': (self.mobility_ns.creeParAdmin, XSD.boolean),
            }
            
            # Ajouter toutes les propriétés présentes
            for key, (predicate, datatype) in property_mappings.items():
                if key in location_data and location_data[key] is not None:
                    value = location_data[key]
                    
                    # Conversion de type si nécessaire
                    if datatype == XSD.float:
                        value = float(value)
                    elif datatype == XSD.integer:
                        value = int(value)
                    elif datatype == XSD.boolean:
                        value = bool(value)
                    elif datatype == XSD.string:
                        value = str(value)
                    
                    self.graph.add((location_uri, predicate, Literal(value, datatype=datatype)))
            
            # Sauvegarder dans le fichier RDF
            if self.save_ontology():
                logger.info(f"✅ Location créée avec succès: {location_id}")
                return True, str(location_uri)
            else:
                return False, "Erreur lors de la sauvegarde"
                
        except Exception as e:
            logger.error(f"❌ Erreur lors de la création de la location: {e}")
            return False, str(e)
    
    def get_locations_by_user(self, user_id: str) -> List[Dict]:
        """
        Récupère toutes les locations d'un utilisateur spécifique
        
        Args:
            user_id: Identifiant de l'utilisateur
        
        Returns:
            Liste de locations
        """
        # Lecture directe du graphe pour robustesse (évite les problèmes de comparaison
        # entre littéraux typés et littéraux simples dans SPARQL).
        try:
            locations = []
            for location_uri in self.graph.subjects(self.rdf_ns.type, self.mobility_ns.Location):
                # Chercher la propriété utilisateurId
                utilisateur_vals = list(self.graph.objects(location_uri, self.mobility_ns.utilisateurId))
                if not utilisateur_vals:
                    continue

                # Comparer la valeur en str() pour supporter les littéraux typés
                if not any(str(val) == str(user_id) for val in utilisateur_vals):
                    continue

                loc = {'location': str(location_uri)}
                for s, p, o in self.graph.triples((location_uri, None, None)):
                    predicate_name = str(p).split('#')[-1]
                    loc[predicate_name] = str(o)

                locations.append(loc)

            # Trier par dateDebutLocation si présent (descendant)
            try:
                locations.sort(key=lambda x: x.get('dateDebutLocation', ''), reverse=True)
            except Exception:
                pass

            logger.info(f"Found {len(locations)} locations for user {user_id}")
            return locations
        except Exception as e:
            logger.error(f"Erreur lors de la lecture des locations depuis le graphe: {e}")
            return []
    
    def get_all_locations(self) -> List[Dict]:
        """
        Récupère toutes les locations (pour l'admin)
        
        Returns:
            Liste de toutes les locations
        """
        logger.info(f"Taille du graphe avant récupération des locations: {len(self.graph)}")
        # Lecture directe du graphe pour lister toutes les locations
        try:
            locations = []
            for location_uri in self.graph.subjects(self.rdf_ns.type, self.mobility_ns.Location):
                loc = {'location': str(location_uri)}
                for s, p, o in self.graph.triples((location_uri, None, None)):
                    predicate_name = str(p).split('#')[-1]
                    loc[predicate_name] = str(o)
                locations.append(loc)

            # Trier par dateDebutLocation si présent (descendant)
            try:
                locations.sort(key=lambda x: x.get('dateDebutLocation', ''), reverse=True)
            except Exception:
                pass

            return locations
        except Exception as e:
            logger.error(f"Erreur lors de la lecture de toutes les locations depuis le graphe: {e}")
            return []

    def update_location(self, location_id: str, location_data: Dict) -> Tuple[bool, str]:
        """
        Met à jour génériquement une location existante dans l'ontologie.
        
        Args:
            location_id: Identifiant de la location à modifier (numeroLocation).
            location_data: Dictionnaire avec les nouvelles données.
        
        Returns:
            Tuple (success: bool, message: str)
        """
        try:
            location_uri = self._get_location_uri_by_numero(location_id)

            if location_uri is None:
                return False, f"La location avec le numeroLocation '{location_id}' n'existe pas"

            # Mapping des propriétés pour la mise à jour
            property_mappings = {
                'lieu_prise': (self.mobility_ns.lieuPrise, XSD.string),
                'lieu_retour': (self.mobility_ns.lieuRetour, XSD.string),
                'conducteur_principal': (self.mobility_ns.conducteurPrincipal, XSD.string),
                'conducteur_secondaire': (self.mobility_ns.conducteurSecondaire, XSD.string),
                'statut': (self.mobility_ns.statutLocation, XSD.string),
                # Ajoutez d'autres champs modifiables ici
            }

            for key, (predicate, datatype) in property_mappings.items():
                if key in location_data:
                    # Supprimer l'ancienne valeur
                    self.graph.remove((location_uri, predicate, None))
                    
                    # Ajouter la nouvelle valeur
                    value = location_data[key]
                    literal_value = Literal(value, datatype=datatype)
                    self.graph.add((location_uri, predicate, literal_value))

            # Sauvegarder les changements
            if self.save_ontology():
                logger.info(f"Location {location_id} mise à jour avec succès.")
                return True, "Location mise à jour avec succès"
            else:
                return False, "Erreur lors de la sauvegarde de l'ontologie"

        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de la location {location_id}: {e}")
            return False, str(e)
    
    def update_location_status(self, location_id: str, new_status: str) -> Tuple[bool, str]:
        """
        Met à jour le statut d'une location
        
        Args:
            location_id: Identifiant de la location (numeroLocation)
            new_status: Nouveau statut
        
        Returns:
            Tuple (success: bool, message: str)
        """
        try:
            location_uri = self._get_location_uri_by_numero(location_id)
            
            if location_uri is None:
                return False, f"La location {location_id} n'existe pas"
            
            # Supprimer l'ancien statut
            self.graph.remove((location_uri, self.mobility_ns.statutLocation, None))
            
            # Ajouter le nouveau statut
            self.graph.add((location_uri, self.mobility_ns.statutLocation, 
                          Literal(new_status, datatype=XSD.string)))
            
            # Sauvegarder
            if self.save_ontology():
                logger.info(f"Statut de location mis à jour: {location_id} -> {new_status}")
                return True, "Statut mis à jour avec succès"
            else:
                return False, "Erreur lors de la sauvegarde"
                
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du statut: {e}")
            return False, str(e)
    
    def delete_location(self, location_id: str) -> Tuple[bool, str]:
        """
        Supprime une location de l'ontologie
        
        Args:
            location_id: Identifiant de la location à supprimer (numeroLocation)
        
        Returns:
            Tuple (success: bool, message: str)
        """
        try:
            location_uri = self._get_location_uri_by_numero(location_id)
            
            if location_uri is None:
                return False, f"La location {location_id} n'existe pas"

            # Supprimer tous les triplets où la location est sujet
            self.graph.remove((location_uri, None, None))
            
            # Supprimer tous les triplets où la location est objet
            self.graph.remove((None, None, location_uri))
            
            # Sauvegarder
            if self.save_ontology():
                logger.info(f"Location supprimée: {location_id}")
                return True, "Location supprimée avec succès"
            else:
                return False, "Erreur lors de la sauvegarde"
                
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de la location: {e}")
            return False, str(e)
    
    def get_location_by_id(self, location_id: str) -> Optional[Dict]:
        """
        Récupère une location spécifique par son ID (numeroLocation)
        
        Args:
            location_id: Identifiant de la location (numeroLocation)
        
        Returns:
            Dictionnaire avec les données de la location ou None
        """
        try:
            location_uri = self._get_location_uri_by_numero(location_id)

            if location_uri is None:
                return None
            
            location_data = {'id': location_id, 'uri': str(location_uri)}
            
            # Récupérer toutes les propriétés
            for s, p, o in self.graph.triples((location_uri, None, None)):
                predicate_name = str(p).split('#')[-1]
                location_data[predicate_name] = str(o)
            
            return location_data
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la location par ID '{location_id}': {e}")
            return None

    def get_location_by_numero(self, numero_location: str) -> Optional[Dict]:
        """
        Récupère une location spécifique par son numeroLocation.

        Args:
            numero_location: Le numéro de la location à trouver.

        Returns:
            Dictionnaire avec les données de la location ou None.
        """
        return self.get_location_by_id(numero_location)


# Instance globale du gestionnaire RDF
rdf_manager = RDFManager()
