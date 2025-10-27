"""
Gestionnaire RDF spécialisé pour les véhicules
Extension du RDFManager pour les opérations CRUD sur les véhicules
"""

import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from rdflib import Literal, XSD
from .rdf_utils import RDFManager

logger = logging.getLogger(__name__)

class VehicleRDFManager(RDFManager):
    """Gestionnaire RDF spécialisé pour les véhicules"""
    
    def __init__(self):
        super().__init__()
        self.vehicle_classes = [
            'Véhicule', 'Vélo', 'Voiture', 'Moto', 'Bus', 'Métro', 'Tramway'
        ]
    
    def get_vehicle_classes(self) -> List[str]:
        """Récupère toutes les classes de véhicules disponibles"""
        return self.vehicle_classes
    
    def create_vehicle(self, vehicle_data: Dict) -> Tuple[bool, str]:
        """
        Crée un nouveau véhicule dans l'ontologie RDF
        
        Args:
            vehicle_data: Dictionnaire avec les données du véhicule
                - type_vehicule: Type de véhicule (Vélo, Voiture, etc.)
                - marque: Marque du véhicule
                - modele: Modèle du véhicule
                - couleur: Couleur du véhicule
                - statut: Statut du véhicule (actif, maintenance, etc.)
                - localisation: Localisation actuelle
                - latitude: Latitude (optionnel)
                - longitude: Longitude (optionnel)
                - niveau_batterie: Niveau de batterie (pour véhicules électriques)
                - capacite_passagers: Capacité en passagers
                - emission_co2: Émissions CO2
                - accessible_pmr: Accessible PMR (bool)
        
        Returns:
            Tuple (success: bool, vehicle_uri: str)
        """
        try:
            import time
            
            # Générer un ID unique pour le véhicule
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            microsec = int(time.time() * 1000000) % 1000
            vehicle_id = f"{vehicle_data.get('type_vehicule', 'Vehicule')}{timestamp}_{microsec}"
            vehicle_uri = self.mobility_ns[vehicle_id]
            
            # Vérifier si le véhicule existe déjà
            if (vehicle_uri, None, None) in self.graph:
                vehicle_id = f"{vehicle_data.get('type_vehicule', 'Vehicule')}{int(time.time() * 1000000)}"
                vehicle_uri = self.mobility_ns[vehicle_id]
            
            # Déterminer la classe du véhicule
            vehicle_type = vehicle_data.get('type_vehicule', 'Véhicule')
            if vehicle_type not in self.vehicle_classes:
                vehicle_type = 'Véhicule'
            
            # Ajouter le type
            self.graph.add((vehicle_uri, self.rdf_ns.type, self.mobility_ns[vehicle_type]))
            
            # Ajouter le label
            label = f"{vehicle_data.get('marque', 'Véhicule')} {vehicle_data.get('modele', '')}"
            self.graph.add((vehicle_uri, self.rdfs_ns.label, Literal(label, lang='fr')))
            
            # Mapping des propriétés
            property_mappings = {
                'marque': (self.mobility_ns.marque, XSD.string),
                'modele': (self.mobility_ns.modèle, XSD.string),
                'couleur': (self.mobility_ns.couleur, XSD.string),
                'statut': (self.mobility_ns.statut, XSD.string),
                'localisation': (self.mobility_ns.localisation, XSD.string),
                'latitude': (self.mobility_ns.latitude, XSD.float),
                'longitude': (self.mobility_ns.longitude, XSD.float),
                'niveau_batterie': (self.mobility_ns.niveauBatterie, XSD.float),
                'capacite_passagers': (self.mobility_ns.capacité, XSD.integer),
                'emission_co2': (self.mobility_ns.emissionCO2, XSD.float),
                'accessible_pmr': (self.mobility_ns.accessiblePMR, XSD.boolean),
                'type_vehicule': (self.mobility_ns.typeVéhicule, XSD.string),
            }
            
            # Ajouter toutes les propriétés présentes
            for key, (predicate, datatype) in property_mappings.items():
                if key in vehicle_data and vehicle_data[key] is not None:
                    value = vehicle_data[key]
                    
                    # Conversion de type si nécessaire
                    if datatype == XSD.float:
                        value = float(value)
                    elif datatype == XSD.integer:
                        value = int(value)
                    elif datatype == XSD.boolean:
                        value = bool(value)
                    elif datatype == XSD.string:
                        value = str(value)
                    
                    self.graph.add((vehicle_uri, predicate, Literal(value, datatype=datatype)))
            
            # Ajouter des propriétés par défaut
            if 'statut' not in vehicle_data:
                self.graph.add((vehicle_uri, self.mobility_ns.statut, Literal("actif", datatype=XSD.string)))
            
            # Ajouter la date de création
            self.graph.add((vehicle_uri, self.mobility_ns.dateCreation, 
                          Literal(datetime.now().isoformat(), datatype=XSD.dateTime)))
            
            # Sauvegarder dans le fichier RDF
            if self.save_ontology():
                logger.info(f"Vehicule cree avec succes: {vehicle_id}")
                return True, str(vehicle_uri)
            else:
                return False, "Erreur lors de la sauvegarde"
                
        except Exception as e:
            logger.error(f"Erreur lors de la creation du vehicule: {e}")
            return False, str(e)
    
    def update_vehicle(self, vehicle_id: str, vehicle_data: Dict) -> Tuple[bool, str]:
        """
        Met à jour un véhicule existant dans l'ontologie
        
        Args:
            vehicle_id: Identifiant du véhicule à modifier
            vehicle_data: Nouvelles données
        
        Returns:
            Tuple (success: bool, message: str)
        """
        try:
            vehicle_uri = self.mobility_ns[vehicle_id]
            
            # Vérifier que le véhicule existe
            vehicle_exists = False
            for vehicle_class in self.vehicle_classes:
                if (vehicle_uri, self.rdf_ns.type, self.mobility_ns[vehicle_class]) in self.graph:
                    vehicle_exists = True
                    break
            
            if not vehicle_exists:
                return False, f"Le véhicule {vehicle_id} n'existe pas"
            
            # Mapping des propriétés à mettre à jour
            property_mappings = {
                'marque': (self.mobility_ns.marque, XSD.string),
                'modele': (self.mobility_ns.modèle, XSD.string),
                'couleur': (self.mobility_ns.couleur, XSD.string),
                'statut': (self.mobility_ns.statut, XSD.string),
                'localisation': (self.mobility_ns.localisation, XSD.string),
                'latitude': (self.mobility_ns.latitude, XSD.float),
                'longitude': (self.mobility_ns.longitude, XSD.float),
                'niveau_batterie': (self.mobility_ns.niveauBatterie, XSD.float),
                'capacite_passagers': (self.mobility_ns.capacité, XSD.integer),
                'emission_co2': (self.mobility_ns.emissionCO2, XSD.float),
                'accessible_pmr': (self.mobility_ns.accessiblePMR, XSD.boolean),
            }
            
            # Mettre à jour les propriétés
            for key, (predicate, datatype) in property_mappings.items():
                if key in vehicle_data:
                    # Supprimer l'ancienne valeur
                    self.graph.remove((vehicle_uri, predicate, None))
                    
                    # Ajouter la nouvelle valeur
                    value = vehicle_data[key]
                    if datatype == XSD.float:
                        value = float(value)
                    elif datatype == XSD.integer:
                        value = int(value)
                    elif datatype == XSD.boolean:
                        value = bool(value)
                    elif datatype == XSD.string:
                        value = str(value)
                    
                    self.graph.add((vehicle_uri, predicate, Literal(value, datatype=datatype)))
            
            # Mettre à jour la date de modification
            self.graph.remove((vehicle_uri, self.mobility_ns.dateModification, None))
            self.graph.add((vehicle_uri, self.mobility_ns.dateModification, 
                          Literal(datetime.now().isoformat(), datatype=XSD.dateTime)))
            
            # Sauvegarder
            if self.save_ontology():
                logger.info(f"Véhicule mis à jour: {vehicle_id}")
                return True, "Véhicule mis à jour avec succès"
            else:
                return False, "Erreur lors de la sauvegarde"
                
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du véhicule: {e}")
            return False, str(e)
    
    def delete_vehicle(self, vehicle_id: str) -> Tuple[bool, str]:
        """
        Supprime un véhicule de l'ontologie
        
        Args:
            vehicle_id: Identifiant du véhicule à supprimer
        
        Returns:
            Tuple (success: bool, message: str)
        """
        try:
            vehicle_uri = self.mobility_ns[vehicle_id]
            
            # Vérifier que le véhicule existe
            vehicle_exists = False
            for vehicle_class in self.vehicle_classes:
                if (vehicle_uri, self.rdf_ns.type, self.mobility_ns[vehicle_class]) in self.graph:
                    vehicle_exists = True
                    break
            
            if not vehicle_exists:
                return False, f"Le véhicule {vehicle_id} n'existe pas"
            
            # Supprimer tous les triplets où le véhicule est sujet
            self.graph.remove((vehicle_uri, None, None))
            
            # Supprimer tous les triplets où le véhicule est objet
            self.graph.remove((None, None, vehicle_uri))
            
            # Sauvegarder
            if self.save_ontology():
                logger.info(f"Véhicule supprimé: {vehicle_id}")
                return True, "Véhicule supprimé avec succès"
            else:
                return False, "Erreur lors de la sauvegarde"
                
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du véhicule: {e}")
            return False, str(e)
    
    def get_vehicle_by_id(self, vehicle_id: str) -> Optional[Dict]:
        """
        Récupère un véhicule spécifique par son ID
        
        Args:
            vehicle_id: Identifiant du véhicule
        
        Returns:
            Dictionnaire avec les données du véhicule ou None
        """
        try:
            vehicle_uri = self.mobility_ns[vehicle_id]
            
            # Vérifier que le véhicule existe
            vehicle_exists = False
            vehicle_type = None
            for vehicle_class in self.vehicle_classes:
                if (vehicle_uri, self.rdf_ns.type, self.mobility_ns[vehicle_class]) in self.graph:
                    vehicle_exists = True
                    vehicle_type = vehicle_class
                    break
            
            if not vehicle_exists:
                return None
            
            vehicle_data = {
                'id': vehicle_id, 
                'uri': str(vehicle_uri),
                'type_vehicule': vehicle_type
            }
            
            # Récupérer toutes les propriétés
            for s, p, o in self.graph.triples((vehicle_uri, None, None)):
                predicate_name = str(p).split('#')[-1]
                vehicle_data[predicate_name] = str(o)
            
            return vehicle_data
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du véhicule: {e}")
            return None
    
    def get_all_vehicles(self) -> List[Dict]:
        """
        Récupère tous les véhicules de l'ontologie
        
        Returns:
            Liste de dictionnaires avec les données des véhicules
        """
        try:
            vehicles = []
            
            for vehicle_class in self.vehicle_classes:
                query = f"""
                SELECT ?vehicle ?marque ?modele ?couleur ?statut ?type
                WHERE {{
                    ?vehicle rdf:type mobility:{vehicle_class} .
                    OPTIONAL {{ ?vehicle mobility:marque ?marque }}
                    OPTIONAL {{ ?vehicle mobility:modèle ?modele }}
                    OPTIONAL {{ ?vehicle mobility:couleur ?couleur }}
                    OPTIONAL {{ ?vehicle mobility:statut ?statut }}
                    BIND("{vehicle_class}" as ?type)
                }}
                ORDER BY ?marque
                """
                
                results = self.execute_sparql_query(query)
                for result in results:
                    result['type_vehicule'] = vehicle_class
                    vehicles.append(result)
            
            return vehicles
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des véhicules: {e}")
            return []
    
    def get_vehicles_by_type(self, vehicle_type: str) -> List[Dict]:
        """
        Récupère tous les véhicules d'un type spécifique
        
        Args:
            vehicle_type: Type de véhicule (Vélo, Voiture, etc.)
        
        Returns:
            Liste de véhicules du type spécifié
        """
        try:
            if vehicle_type not in self.vehicle_classes:
                return []
            
            query = f"""
            SELECT ?vehicle ?marque ?modele ?couleur ?statut ?localisation ?niveauBatterie
            WHERE {{
                ?vehicle rdf:type mobility:{vehicle_type} .
                OPTIONAL {{ ?vehicle mobility:marque ?marque }}
                OPTIONAL {{ ?vehicle mobility:modèle ?modele }}
                OPTIONAL {{ ?vehicle mobility:couleur ?couleur }}
                OPTIONAL {{ ?vehicle mobility:statut ?statut }}
                OPTIONAL {{ ?vehicle mobility:localisation ?localisation }}
                OPTIONAL {{ ?vehicle mobility:niveauBatterie ?niveauBatterie }}
            }}
            ORDER BY ?marque
            """
            
            results = self.execute_sparql_query(query)
            for result in results:
                result['type_vehicule'] = vehicle_type
            
            return results
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des véhicules de type {vehicle_type}: {e}")
            return []
    
    def get_vehicles_by_status(self, status: str) -> List[Dict]:
        """
        Récupère tous les véhicules avec un statut spécifique
        
        Args:
            status: Statut du véhicule (actif, maintenance, etc.)
        
        Returns:
            Liste de véhicules avec le statut spécifié
        """
        try:
            vehicles = []
            
            for vehicle_class in self.vehicle_classes:
                query = f"""
                SELECT ?vehicle ?marque ?modele ?couleur ?statut ?type
                WHERE {{
                    ?vehicle rdf:type mobility:{vehicle_class} .
                    ?vehicle mobility:statut "{status}" .
                    OPTIONAL {{ ?vehicle mobility:marque ?marque }}
                    OPTIONAL {{ ?vehicle mobility:modèle ?modele }}
                    OPTIONAL {{ ?vehicle mobility:couleur ?couleur }}
                    BIND("{vehicle_class}" as ?type)
                }}
                ORDER BY ?marque
                """
                
                results = self.execute_sparql_query(query)
                for result in results:
                    result['type_vehicule'] = vehicle_class
                    vehicles.append(result)
            
            return vehicles
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des véhicules avec statut {status}: {e}")
            return []
    
    def search_vehicles(self, keyword: str) -> List[Dict]:
        """
        Recherche des véhicules par mot-clé
        
        Args:
            keyword: Mot-clé de recherche
        
        Returns:
            Liste de véhicules correspondants
        """
        try:
            keyword_lower = keyword.lower()
            vehicles = []
            
            for vehicle_class in self.vehicle_classes:
                query = f"""
                SELECT ?vehicle ?marque ?modele ?couleur ?statut ?type
                WHERE {{
                    ?vehicle rdf:type mobility:{vehicle_class} .
                    OPTIONAL {{ ?vehicle mobility:marque ?marque }}
                    OPTIONAL {{ ?vehicle mobility:modèle ?modele }}
                    OPTIONAL {{ ?vehicle mobility:couleur ?couleur }}
                    OPTIONAL {{ ?vehicle mobility:statut ?statut }}
                    BIND("{vehicle_class}" as ?type)
                    FILTER(
                        CONTAINS(LCASE(COALESCE(?marque, "")), "{keyword_lower}") ||
                        CONTAINS(LCASE(COALESCE(?modele, "")), "{keyword_lower}") ||
                        CONTAINS(LCASE(COALESCE(?couleur, "")), "{keyword_lower}")
                    )
                }}
                ORDER BY ?marque
                """
                
                results = self.execute_sparql_query(query)
                for result in results:
                    result['type_vehicule'] = vehicle_class
                    vehicles.append(result)
            
            return vehicles
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche de véhicules: {e}")
            return []
    
    def get_vehicle_statistics(self) -> Dict:
        """
        Récupère des statistiques sur les véhicules
        
        Returns:
            Dictionnaire avec les statistiques
        """
        try:
            stats = {
                'total_vehicles': 0,
                'vehicles_by_type': {},
                'vehicles_by_status': {},
                'electric_vehicles': 0,
                'accessible_vehicles': 0
            }
            
            # Compter le total des véhicules
            total_query = """
            SELECT (COUNT(?vehicle) as ?count)
            WHERE {
                ?vehicle rdf:type ?type .
                FILTER(?type IN (mobility:Véhicule, mobility:Vélo, mobility:Voiture, mobility:Moto, mobility:Bus, mobility:Métro, mobility:Tramway))
            }
            """
            total_result = self.execute_sparql_query(total_query)
            if total_result and 'count' in total_result[0]:
                stats['total_vehicles'] = int(total_result[0]['count'])
            
            # Compter par type
            for vehicle_class in self.vehicle_classes:
                type_query = f"""
                SELECT (COUNT(?vehicle) as ?count)
                WHERE {{
                    ?vehicle rdf:type mobility:{vehicle_class} .
                }}
                """
                type_result = self.execute_sparql_query(type_query)
                if type_result and 'count' in type_result[0]:
                    stats['vehicles_by_type'][vehicle_class] = int(type_result[0]['count'])
            
            # Compter par statut
            status_query = """
            SELECT ?statut (COUNT(?vehicle) as ?count)
            WHERE {
                ?vehicle rdf:type ?type .
                ?vehicle mobility:statut ?statut .
                FILTER(?type IN (mobility:Véhicule, mobility:Vélo, mobility:Voiture, mobility:Moto, mobility:Bus, mobility:Métro, mobility:Tramway))
            }
            GROUP BY ?statut
            """
            status_results = self.execute_sparql_query(status_query)
            for result in status_results:
                if 'statut' in result and 'count' in result:
                    stats['vehicles_by_status'][result['statut']] = int(result['count'])
            
            # Compter les véhicules électriques (avec niveau de batterie)
            electric_query = """
            SELECT (COUNT(?vehicle) as ?count)
            WHERE {
                ?vehicle rdf:type ?type .
                ?vehicle mobility:niveauBatterie ?battery .
                FILTER(?type IN (mobility:Véhicule, mobility:Vélo, mobility:Voiture, mobility:Moto, mobility:Bus, mobility:Métro, mobility:Tramway))
            }
            """
            electric_result = self.execute_sparql_query(electric_query)
            if electric_result and 'count' in electric_result[0]:
                stats['electric_vehicles'] = int(electric_result[0]['count'])
            
            # Compter les véhicules accessibles PMR
            accessible_query = """
            SELECT (COUNT(?vehicle) as ?count)
            WHERE {
                ?vehicle rdf:type ?type .
                ?vehicle mobility:accessiblePMR true .
                FILTER(?type IN (mobility:Véhicule, mobility:Vélo, mobility:Voiture, mobility:Moto, mobility:Bus, mobility:Métro, mobility:Tramway))
            }
            """
            accessible_result = self.execute_sparql_query(accessible_query)
            if accessible_result and 'count' in accessible_result[0]:
                stats['accessible_vehicles'] = int(accessible_result[0]['count'])
            
            return stats
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des statistiques des véhicules: {e}")
            return {
                'total_vehicles': 0,
                'vehicles_by_type': {},
                'vehicles_by_status': {},
                'electric_vehicles': 0,
                'accessible_vehicles': 0
            }


# Instance globale du gestionnaire de véhicules RDF
vehicle_rdf_manager = VehicleRDFManager()
