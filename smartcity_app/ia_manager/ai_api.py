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
