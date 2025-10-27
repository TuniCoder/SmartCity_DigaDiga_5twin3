from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS

# Define namespaces
LOCATION = Namespace("http://smartcity.org/location/")
SCHEMA = Namespace("http://schema.org/")

MOBILITY = Namespace("http://example.org/mobility-ontology/2025/09#")

class LocationService:
    def __init__(self):
        self.g = Graph()
        self.g.parse("ontology/mobility_ontology_clean.rdf", format="xml")

    def create_location(self, location_data):
        location_uri = URIRef(LOCATION[str(location_data['id'])])
        
        self.g.add((location_uri, RDF.type, SCHEMA.Place))
        self.g.add((location_uri, SCHEMA.name, Literal(location_data['name'])))
        self.g.add((location_uri, SCHEMA.address, Literal(location_data['address'])))
        self.g.add((location_uri, SCHEMA.latitude, Literal(location_data['latitude'])))
        self.g.add((location_uri, SCHEMA.longitude, Literal(location_data['longitude'])))
        
        self.g.serialize("locations.ttl", format="turtle")
        return location_data

    def get_all_locations(self):
        query = """
        SELECT ?id ?name ?address ?latitude ?longitude
        WHERE {
            ?location rdf:type schema:Place ;
                     schema:name ?name ;
                     schema:address ?address ;
                     schema:latitude ?latitude ;
                     schema:longitude ?longitude .
            BIND(STRAFTER(STR(?location), "http://smartcity.org/location/") AS ?id)
        }
        """
        results = self.g.query(query)
        return [
            {
                'id': str(row.id),
                'name': str(row.name),
                'address': str(row.address),
                'latitude': float(row.latitude),
                'longitude': float(row.longitude)
            }
            for row in results
        ]

    def get_location_by_id(self, location_id):
        query = """
        SELECT ?name ?address ?latitude ?longitude
        WHERE {
            ?location rdf:type schema:Place ;
                     schema:name ?name ;
                     schema:address ?address ;
                     schema:latitude ?latitude ;
                     schema:longitude ?longitude .
            FILTER(STRAFTER(STR(?location), "http://smartcity.org/location/") = "%s")
        }
        """ % location_id
        results = list(self.g.query(query))
        if results:
            row = results[0]
            return {
                'id': location_id,
                'name': str(row.name),
                'address': str(row.address),
                'latitude': float(row.latitude),
                'longitude': float(row.longitude)
            }
        return None

    def update_location(self, location_id, location_data):
        location_uri = URIRef(LOCATION[str(location_id)])
        
        # Remove existing triples
        self.g.remove((location_uri, None, None))
        
        # Add updated triples
        self.g.add((location_uri, RDF.type, SCHEMA.Place))
        self.g.add((location_uri, SCHEMA.name, Literal(location_data['name'])))
        self.g.add((location_uri, SCHEMA.address, Literal(location_data['address'])))
        self.g.add((location_uri, SCHEMA.latitude, Literal(location_data['latitude'])))
        self.g.add((location_uri, SCHEMA.longitude, Literal(location_data['longitude'])))
        
        self.g.serialize("locations.ttl", format="turtle")
        return location_data

    def delete_location(self, location_id):
        location_uri = URIRef(LOCATION[str(location_id)])
        self.g.remove((location_uri, None, None))
        self.g.serialize("locations.ttl", format="turtle")
        return True

    # Additional SPARQL queries
    def get_locations_by_area(self, min_lat, max_lat, min_lon, max_lon):
        query = """
        SELECT ?id ?name ?address ?latitude ?longitude
        WHERE {
            ?location rdf:type schema:Place ;
                     schema:name ?name ;
                     schema:address ?address ;
                     schema:latitude ?latitude ;
                     schema:longitude ?longitude .
            BIND(STRAFTER(STR(?location), "http://smartcity.org/location/") AS ?id)
            FILTER(?latitude >= %f && ?latitude <= %f && ?longitude >= %f && ?longitude <= %f)
        }
        """ % (min_lat, max_lat, min_lon, max_lon)
        results = self.g.query(query)
        return [
            {
                'id': str(row.id),
                'name': str(row.name),
                'address': str(row.address),
                'latitude': float(row.latitude),
                'longitude': float(row.longitude)
            }
            for row in results
        ]

    def search_locations_by_name(self, name_query):
        query = """
        SELECT ?id ?name ?address ?latitude ?longitude
        WHERE {
            ?location rdf:type schema:Place ;
                     schema:name ?name ;
                     schema:address ?address ;
                     schema:latitude ?latitude ;
                     schema:longitude ?longitude .
            BIND(STRAFTER(STR(?location), "http://smartcity.org/location/") AS ?id)
            FILTER(CONTAINS(LCASE(?name), LCASE("%s")))
        }
        """ % name_query
        results = self.g.query(query)
        return [
            {
                'id': str(row.id),
                'name': str(row.name),
                'address': str(row.address),
                'latitude': float(row.latitude),
                'longitude': float(row.longitude)
            }
            for row in results
        ]

    def get_all_reservations(self):
        query = """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX mobility: <http://example.org/mobility-ontology/2025/09#>
        
        SELECT DISTINCT ?id ?customer ?pickupLoc ?returnLoc ?startDate ?endDate ?price ?deposit ?status
        WHERE {
            ?location rdf:type mobility:Location ;
                     mobility:numeroLocation ?id ;
                     mobility:conducteurPrincipal ?customer ;
                     mobility:lieuPrise ?pickupLoc ;
                     mobility:lieuRetour ?returnLoc ;
                     mobility:dateDebutLocation ?startDate ;
                     mobility:dateFinLocation ?endDate ;
                     mobility:prixTotalCalcule ?price ;
                     mobility:cautionPayee ?deposit ;
                     mobility:statutLocation ?status .
        }
        ORDER BY ?startDate
        """
        results = self.g.query(query)
        locations = [
            {
                'id': str(row.id),
                'customer': str(row.customer),
                'fromLocation': str(row.pickupLoc),
                'toLocation': str(row.returnLoc),
                'startDate': str(row.startDate),
                'endDate': str(row.endDate),
                'price': float(row.price),
                'deposit': float(row.deposit),
                'status': str(row.status)
            }
            for row in results
        ]
        print("Found locations:", len(locations))  # Debug line
        return locations

    def get_reservation_by_id(self, reservation_id):
        query = """
        PREFIX mobility: <http://example.org/mobility-ontology/2025/09#>
        SELECT ?customer ?pickupLoc ?returnLoc ?startDate ?endDate ?price ?deposit ?status
        WHERE {
            ?location rdf:type mobility:Location ;
                     mobility:numeroLocation ?id ;
                     mobility:conducteurPrincipal ?customer ;
                     mobility:lieuPrise ?pickupLoc ;
                     mobility:lieuRetour ?returnLoc ;
                     mobility:dateDebutLocation ?startDate ;
                     mobility:dateFinLocation ?endDate ;
                     mobility:prixTotalCalcule ?price ;
                     mobility:cautionPayee ?deposit ;
                     mobility:statutLocation ?status .
            FILTER(?id = "%s")
        }
        """ % reservation_id
        results = list(self.g.query(query))
        if results:
            row = results[0]
            return {
                'id': reservation_id,
                'customer': str(row.customer),
                'fromLocation': str(row.pickupLoc),
                'toLocation': str(row.returnLoc),
                'startDate': str(row.startDate),
                'endDate': str(row.endDate),
                'price': float(row.price),
                'deposit': float(row.deposit),
                'status': str(row.status)
            }
        return None

    def update_reservation_status(self, reservation_id, new_status):
        query = """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX mobility: <http://example.org/mobility-ontology/2025/09#>
        
        DELETE {
            ?location mobility:statutLocation ?oldStatus
        }
        INSERT {
            ?location mobility:statutLocation "%s"
        }
        WHERE {
            ?location rdf:type mobility:Location ;
                     mobility:numeroLocation "%s" ;
                     mobility:statutLocation ?oldStatus .
        }
        """ % (new_status, reservation_id)
        
        try:
            # First check if the reservation exists
            check_query = """
            PREFIX mobility: <http://example.org/mobility-ontology/2025/09#>
            ASK {
                ?location rdf:type mobility:Location ;
                         mobility:numeroLocation "%s" .
            }
            """ % reservation_id
            
            if not list(self.g.query(check_query))[0]:
                raise Exception(f"Location {reservation_id} not found in the ontology")
            
            self.g.update(query)
            self.g.serialize("ontology/mobility_ontology_clean.rdf", format="xml")
            return True
        except Exception as e:
            print(f"Error updating status in RDF: {e}")
            return False