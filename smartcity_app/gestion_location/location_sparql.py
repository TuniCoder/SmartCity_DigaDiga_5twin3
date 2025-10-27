"""
Module contenant les requêtes SPARQL pour la gestion des locations
"""

# Définition des requêtes SPARQL pour la gestion des locations
SPARQL_QUERIES = {
    # Requête pour obtenir toutes les locations
    'get_all_locations': """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX sc: <http://www.semanticweb.org/smartcity/ontology#>
        
        SELECT ?location ?numeroLocation ?dateDebut ?dateFin ?statut ?prixTotal ?utilisateur ?vehicule
        WHERE {
            ?location rdf:type sc:Location ;
                      sc:numeroLocation ?numeroLocation ;
                      sc:dateDebutLocation ?dateDebut ;
                      sc:dateFinLocation ?dateFin ;
                      sc:statutLocation ?statut ;
                      sc:prixTotalCalcule ?prixTotal ;
                      sc:estReserveePar ?utilisateur ;
                      sc:concerne ?vehicule .
        }
    """,
    
    # Requête pour obtenir une location par ID
    'get_location_by_id': """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX sc: <http://www.semanticweb.org/smartcity/ontology#>
        
        SELECT ?location ?numeroLocation ?dateDebut ?dateFin ?statut ?prixTotal ?utilisateur ?vehicule
        WHERE {
            ?location rdf:type sc:Location ;
                      sc:id ?id ;
                      sc:numeroLocation ?numeroLocation ;
                      sc:dateDebutLocation ?dateDebut ;
                      sc:dateFinLocation ?dateFin ;
                      sc:statutLocation ?statut ;
                      sc:prixTotalCalcule ?prixTotal ;
                      sc:estReserveePar ?utilisateur ;
                      sc:concerne ?vehicule .
            FILTER(?id = "%s")
        }
    """,
    
    # Requête pour obtenir une location par numéro
    'get_location_by_numero': """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX sc: <http://www.semanticweb.org/smartcity/ontology#>
        
        SELECT ?location ?numeroLocation ?dateDebut ?dateFin ?statut ?prixTotal ?utilisateur ?vehicule
        WHERE {
            ?location rdf:type sc:Location ;
                      sc:numeroLocation ?numeroLocation ;
                      sc:dateDebutLocation ?dateDebut ;
                      sc:dateFinLocation ?dateFin ;
                      sc:statutLocation ?statut ;
                      sc:prixTotalCalcule ?prixTotal ;
                      sc:estReserveePar ?utilisateur ;
                      sc:concerne ?vehicule .
            FILTER(?numeroLocation = "%s")
        }
    """,
    
    # Requête pour obtenir les locations d'un utilisateur
    'get_locations_by_user': """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX sc: <http://www.semanticweb.org/smartcity/ontology#>
        
        SELECT ?location ?numeroLocation ?dateDebut ?dateFin ?statut ?prixTotal ?vehicule
        WHERE {
            ?location rdf:type sc:Location ;
                      sc:numeroLocation ?numeroLocation ;
                      sc:dateDebutLocation ?dateDebut ;
                      sc:dateFinLocation ?dateFin ;
                      sc:statutLocation ?statut ;
                      sc:prixTotalCalcule ?prixTotal ;
                      sc:estReserveePar ?utilisateur ;
                      sc:concerne ?vehicule .
            ?utilisateur sc:id ?userId .
            FILTER(?userId = "%s")
        }
    """,
    
    # Requête pour créer une nouvelle location
    'create_location': """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX sc: <http://www.semanticweb.org/smartcity/ontology#>
        
        INSERT DATA {
            <%s> rdf:type sc:Location ;
                 sc:id "%s" ;
                 sc:numeroLocation "%s" ;
                 sc:dateDebutLocation "%s" ;
                 sc:dateFinLocation "%s" ;
                 sc:statutLocation "%s" ;
                 sc:prixTotalCalcule "%s" ;
                 sc:lieuPrise "%s" ;
                 sc:lieuRetour "%s" ;
                 sc:estReserveePar <%s> ;
                 sc:concerne <%s> .
        }
    """,
    
    # Requête pour mettre à jour le statut d'une location
    'update_location_status': """
        PREFIX sc: <http://www.semanticweb.org/smartcity/ontology#>
        
        DELETE {
            ?location sc:statutLocation ?oldStatus .
        }
        INSERT {
            ?location sc:statutLocation "%s" .
        }
        WHERE {
            ?location sc:id "%s" ;
                     sc:statutLocation ?oldStatus .
        }
    """
}