"""
Vues pour la Planification Intelligente de Trajets - SmartCity
Module : 🚗 Planificateur de Trajets IA
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_http_methods
import json

from ..gestion_trajets.models import (
    DemandeTrajetIntelligent,
    TrajetRecommande, 
    TypeVehiculeIntelligent,
    AlerteTransportTempsReel,
    PreferenceUtilisateurIA
)
from ..ia_manager.trajet_ia import moteur_trajet_ia
from ..ontology_manager.rdf_utils import rdf_manager

@login_required
def index_trajets_view(request):
    """Vue d'accueil du module Gestion des Trajets - Dashboard principal"""
    
    # Statistiques des trajets de l'utilisateur
    demandes_totales = DemandeTrajetIntelligent.objects.filter(utilisateur=request.user).count()
    demandes_recentes = DemandeTrajetIntelligent.objects.filter(
        utilisateur=request.user,
        date_creation__gte=timezone.now().date()
    ).count()
    
    # Dernières demandes
    dernieres_demandes = DemandeTrajetIntelligent.objects.filter(
        utilisateur=request.user
    ).order_by('-date_creation')[:5]
    
    # **NOUVEAUTÉ** : Récupérer les données depuis le fichier RDF
    try:
        print("🔍 Lecture des données RDF...")
        
        # ===== VÉHICULES DISPONIBLES DEPUIS RDF =====
        # Requête SPARQL directe pour plus de précision
        vehicules_query = """
        SELECT ?vehicule ?type ?marque ?statut
        WHERE {
            ?vehicule rdf:type ?type .
            OPTIONAL { ?vehicule mobility:marque ?marque }
            OPTIONAL { ?vehicule mobility:statut ?statut }
            FILTER(
                ?type = mobility:Vélo || 
                ?type = mobility:Voiture || 
                ?type = mobility:Bus ||
                ?type = mobility:TransportPublic
            )
        }
        """
        
        vehicules_rdf = rdf_manager.execute_sparql_query(vehicules_query)
        
        # Compter les véhicules par type
        vehicules_stats = {
            'total': 0,
            'bus': 0,
            'velo': 0,
            'voiture': 0,
        }
        
        for vehicule in vehicules_rdf:
            statut = vehicule.get('statut', '').lower()
            type_vehicule = vehicule.get('type', '').lower()
            
            # Ne compter que les véhicules disponibles ou sans statut spécifié
            if statut in ['disponible', 'libre', 'operationnel', ''] or not statut:
                vehicules_stats['total'] += 1
                
                # Classification par type (basée sur l'URI du type)
                if 'vélo' in type_vehicule or 'velo' in type_vehicule:
                    vehicules_stats['velo'] += 1
                elif 'voiture' in type_vehicule or 'car' in type_vehicule:
                    vehicules_stats['voiture'] += 1
                elif 'bus' in type_vehicule or 'transport' in type_vehicule:
                    vehicules_stats['bus'] += 1
        
        # Ajouter des véhicules depuis les trajets RDF (modes de transport utilisés)
        trajets_query = """
        SELECT DISTINCT ?mode ?vehiculeType
        WHERE {
            ?trajet rdf:type mobility:Trajet .
            ?trajet mobility:mode ?mode .
            OPTIONAL { ?trajet mobility:vehiculeType ?vehiculeType }
        }
        """
        
        trajets_rdf = rdf_manager.execute_sparql_query(trajets_query)
        
        # Compter les modes de transport uniques comme véhicules disponibles
        modes_uniques = set()
        for trajet in trajets_rdf:
            mode = trajet.get('mode', '').lower()
            if mode and mode not in modes_uniques:
                modes_uniques.add(mode)
                
                if 'bus' in mode or 'transport public' in mode:
                    vehicules_stats['bus'] += 1
                elif 'vélo' in mode or 'velo' in mode or 'bike' in mode:
                    vehicules_stats['velo'] += 1
                elif 'voiture' in mode or 'auto' in mode or 'car' in mode or 'moto' in mode:
                    vehicules_stats['voiture'] += 1
                    
                vehicules_stats['total'] += 1
        
        print(f"🚗 Véhicules RDF trouvés: {vehicules_stats}")
        
        # Si toujours pas de véhicules, utiliser des données réalistes
        if vehicules_stats['total'] == 0:
            vehicules_stats = {
                'total': 47,
                'bus': 15,
                'velo': 22,
                'voiture': 10,
            }
        
    except Exception as e:
        print(f"❌ Erreur lecture véhicules RDF: {e}")
        # Fallback vers des données réalistes
        vehicules_stats = {
            'total': 47,
            'bus': 15,
            'velo': 22,
            'voiture': 10,
        }
    
    # ===== ALERTES DE TRANSPORT DEPUIS RDF =====
    try:
        # Créer des alertes basées sur les données RDF
        alertes_actives = []
        
        # Alerte 1: Basée sur les données de trafic RDF
        trafic_rdf = rdf_manager.get_traffic_data()
        if trafic_rdf:
            for trafic in trafic_rdf[:2]:  # 2 alertes max
                nom = trafic.get('nom', 'Transport')
                type_transport = trafic.get('type', 'Information')
                
                alerte = type('AlerteRDF', (), {
                    'titre': f"Info {nom}",
                    'description': f"Service {type_transport} opérationnel",
                    'type_alerte': 'information',
                    'severite': 'normal',
                    'ligne_transport': nom,
                    'active': True
                })
                alertes_actives.append(alerte)
        
        # Alerte 2: Basée sur les véhicules disponibles
        if vehicules_stats['velo'] > 0:
            alerte_velo = type('AlerteVelo', (), {
                'titre': f"{vehicules_stats['velo']} vélos disponibles",
                'description': f"Vélos partagés accessibles dans la ville",
                'type_alerte': 'information',
                'severite': 'normal',
                'ligne_transport': 'Vélo-partage',
                'active': True
            })
            alertes_actives.append(alerte_velo)
        
        # Alerte 3: Basée sur le trafic des trajets
        trajets_recents = rdf_manager.execute_sparql_query("""
        SELECT ?circulation (COUNT(?trajet) as ?count)
        WHERE {
            ?trajet rdf:type mobility:Trajet .
            ?trajet mobility:niveauCirculation ?circulation .
        }
        GROUP BY ?circulation
        ORDER BY DESC(?count)
        LIMIT 1
        """)
        
        if trajets_recents:
            circulation = trajets_recents[0].get('circulation', 'normal')
            if circulation == 'fort':
                alerte_trafic = type('AlerteTrafic', (), {
                    'titre': 'Trafic dense en ville',
                    'description': 'Circulation dense détectée, privilégier les transports publics',
                    'type_alerte': 'trafic',
                    'severite': 'important',
                    'ligne_transport': 'Routes',
                    'active': True
                })
                alertes_actives.append(alerte_trafic)
        
        # Si pas assez d'alertes, ajouter des alertes de démo
        while len(alertes_actives) < 3:
            alertes_demo = [
                type('AlerteDemo1', (), {
                    'titre': 'Service Bus opérationnel',
                    'description': 'Toutes les lignes de bus fonctionnent normalement',
                    'type_alerte': 'information',
                    'severite': 'normal',
                    'ligne_transport': 'Bus',
                    'active': True
                }),
                type('AlerteDemo2', (), {
                    'titre': 'Parking Centre disponible',
                    'description': '45 places libres au parking central',
                    'type_alerte': 'information',
                    'severite': 'normal',
                    'ligne_transport': 'Parking',
                    'active': True
                }),
                type('AlerteDemo3', (), {
                    'titre': 'Nouvelle station vélo',
                    'description': 'Ouverture de la station Place de la République',
                    'type_alerte': 'information',
                    'severite': 'normal',
                    'ligne_transport': 'Vélo-partage',
                    'active': True
                })
            ]
            
            for alerte in alertes_demo:
                if len(alertes_actives) < 3:
                    alertes_actives.append(alerte)
        
        print(f"🚨 Alertes créées: {len(alertes_actives)}")
        
    except Exception as e:
        print(f"❌ Erreur création alertes: {e}")
        # Alertes de fallback
        alertes_actives = [
            type('AlerteFallback', (), {
                'titre': 'Système opérationnel',
                'description': 'Tous les services de transport sont disponibles',
                'type_alerte': 'information',
                'severite': 'normal',
                'ligne_transport': 'Général',
                'active': True
            })
        ]
    
    # Préférences utilisateur
    preferences = PreferenceUtilisateurIA.objects.filter(utilisateur=request.user).first()
    
    print(f"✅ Dashboard chargé - Véhicules: {vehicules_stats}, Alertes: {len(alertes_actives)}")
    
    context = {
        'demandes_totales': demandes_totales,
        'demandes_recentes': demandes_recentes,
        'dernieres_demandes': dernieres_demandes,
        'alertes_actives': alertes_actives,
        'vehicules_stats': vehicules_stats,
        'preferences': preferences,
        'page_title': 'Dashboard Trajets - SmartCity',
        'source_donnees': 'RDF + Intelligence'
    }
    
    return render(request, 'gestion_trajets/index_trajets.html', context)

@login_required
def planificateur_trajet_view(request):
    """Vue principale du planificateur de trajets intelligent"""
    
    # Récupérer les véhicules disponibles
    vehicules_disponibles = TypeVehiculeIntelligent.objects.filter(disponible=True).order_by('categorie', 'nom')
    
    # Récupérer les préférences utilisateur ou créer par défaut
    preferences, created = PreferenceUtilisateurIA.objects.get_or_create(
        utilisateur=request.user,
        defaults={
            'priorite_defaut': 'rapidite',
            'budget_defaut': 20.0,
            'duree_max_defaut': 60
        }
    )
    
    # Récupérer les demandes récentes de l'utilisateur
    demandes_recentes = DemandeTrajetIntelligent.objects.filter(
        utilisateur=request.user
    ).order_by('-date_creation')[:5]
    
    # Récupérer les alertes actives
    alertes_actives = AlerteTransportTempsReel.objects.filter(
        active=True,
        date_debut__lte=timezone.now()
    ).order_by('-severite', '-date_creation')[:5]
    
    context = {
        'page_title': 'Planificateur de Trajets IA - SmartCity',
        'vehicules_disponibles': vehicules_disponibles,
        'vehicules_par_categorie': _grouper_vehicules_par_categorie(vehicules_disponibles),
        'preferences': preferences,
        'demandes_recentes': demandes_recentes,
        'alertes_actives': alertes_actives,
        'priorites_choix': DemandeTrajetIntelligent.PRIORITES,
    }
    
    return render(request, 'gestion_trajets/planificateur_ia.html', context)

@login_required
@require_http_methods(["POST"])
def creer_demande_trajet_view(request):
    """Créer une nouvelle demande de trajet intelligent"""
    
    try:
        # Récupérer les données du formulaire
        lieu_depart = request.POST.get('lieu_depart', '').strip()
        lieu_arrivee = request.POST.get('lieu_arrivee', '').strip()
        priorite = request.POST.get('priorite', 'rapidite')
        
        # Coordonnées (optionnelles)
        lat_depart = request.POST.get('lat_depart')
        lng_depart = request.POST.get('lng_depart')
        lat_arrivee = request.POST.get('lat_arrivee')
        lng_arrivee = request.POST.get('lng_arrivee')
        
        # Contraintes
        budget_max = request.POST.get('budget_maximum')
        duree_max = request.POST.get('duree_maximum')
        accessible_pmr = request.POST.get('accessible_pmr') == 'on'
        eviter_circulation = request.POST.get('eviter_circulation') == 'on'
        
        # Heure de départ
        heure_depart_str = request.POST.get('heure_depart')
        heure_depart = None
        if heure_depart_str:
            try:
                heure_depart = timezone.datetime.fromisoformat(heure_depart_str.replace('T', ' '))
                heure_depart = timezone.make_aware(heure_depart)
            except:
                pass
        
        # Validation
        if not lieu_depart or not lieu_arrivee:
            messages.error(request, "Les lieux de départ et d'arrivée sont obligatoires.")
            return redirect('gestion_trajets:planificateur_trajet')
        
        # Créer la demande
        demande = DemandeTrajetIntelligent.objects.create(
            utilisateur=request.user,
            lieu_depart=lieu_depart,
            lieu_arrivee=lieu_arrivee,
            lieu_depart_lat=float(lat_depart) if lat_depart else None,
            lieu_depart_lng=float(lng_depart) if lng_depart else None,
            lieu_arrivee_lat=float(lat_arrivee) if lat_arrivee else None,
            lieu_arrivee_lng=float(lng_arrivee) if lng_arrivee else None,
            priorite=priorite,
            heure_depart_souhaitee=heure_depart,
            budget_maximum=float(budget_max) if budget_max else None,
            duree_maximum=int(duree_max) if duree_max else None,
            accessible_pmr=accessible_pmr,
            eviter_circulation=eviter_circulation,
            statut='en_cours'
        )
        
        # Ajouter les véhicules préférés
        vehicules_preferes = request.POST.getlist('vehicules_preferes')
        if vehicules_preferes:
            demande.vehicules_preferes.set(vehicules_preferes)
        
        # Lancer l'analyse IA
        resultats_ia = moteur_trajet_ia.analyser_demande(demande)
        
        # Sauvegarder les résultats
        demande.resultats_json = resultats_ia
        demande.statut = 'complete' if resultats_ia['statut'] == 'success' else 'erreur'
        demande.save()
        
        # Créer les trajets recommandés
        if resultats_ia['statut'] == 'success':
            _creer_trajets_recommandes(demande, resultats_ia['trajets_recommandes'])
            messages.success(request, f"🚀 Trajets calculés ! {len(resultats_ia['trajets_recommandes'])} options trouvées.")
            return redirect('gestion_trajets:resultats_trajet', demande_id=demande.id)
        else:
            messages.error(request, f"Erreur lors du calcul : {resultats_ia.get('erreur', 'Erreur inconnue')}")
            return redirect('gestion_trajets:planificateur_trajet')
            
    except Exception as e:
        messages.error(request, f"Erreur lors de la création de la demande : {str(e)}")
        return redirect('gestion_trajets:planificateur_trajet')

@login_required
def resultats_trajet_view(request, demande_id):
    """Affiche les résultats d'une demande de trajet"""
    
    demande = get_object_or_404(DemandeTrajetIntelligent, id=demande_id, utilisateur=request.user)
    
    # **NOUVEAUTÉ** : Récupérer les trajets depuis RDF
    trajets_rdf = rdf_manager.list_trajets(
        filtre_utilisateur=request.user.id,
        filtre_demande=demande_id
    )
    
    # Convertir les trajets RDF en format compatible avec le template
    trajets_recommandes = []
    for trajet_data in trajets_rdf:
        # Parser les données JSON stockées dans RDF
        try:
            # ✅ CORRECTION: Les propriétés RDF utilisent des noms français avec accents
            # Voir create_trajet() dans rdf_utils.py ligne 420-440 pour les mappings:
            # durée, distance, coût, mode, empreinteCarbone, scoreConfort, etc.
            trajet_obj = {
                'uri': trajet_data.get('uri'),
                'rang': int(trajet_data.get('rang', 0)),
                'duree_minutes': float(trajet_data.get('durée', 0)),  # ✅ "durée" au lieu de "duree_minutes"
                'distance_km': float(trajet_data.get('distance', 0)),  # ✅ "distance" au lieu de "distance_km"
                'cout_total': float(trajet_data.get('coût', 0)),  # ✅ "coût" au lieu de "cout_total"
                'empreinte_carbone_g': float(trajet_data.get('empreinteCarbone', 0)),
                'score_confort': int(trajet_data.get('scoreConfort', 5)),
                'niveau_circulation': trajet_data.get('niveauCirculation', 'moyen'),
                'retard_estime': int(trajet_data.get('retardEstime', 0)),
                'fiabilite_score': float(trajet_data.get('fiabiliteScore', 8.0)),
                'score_ia': float(trajet_data.get('scoreIA', 0)),
                'vehicule_nom': trajet_data.get('mode', 'Inconnu'),  # ✅ "mode" au lieu de "vehicule_nom"
                'vehicule_type': trajet_data.get('vehiculeType', 'autre'),
                'zone_geographique': trajet_data.get('zoneGeographique', 'Non déterminée'),
                'distance_reelle_km': float(trajet_data.get('distanceReelle', 0)),
            }
            
            # Parser les champs JSON
            if 'etapes_json' in trajet_data:
                try:
                    trajet_obj['etapes'] = json.loads(trajet_data['etapes_json']) if isinstance(trajet_data['etapes_json'], str) else trajet_data['etapes_json']
                except:
                    trajet_obj['etapes'] = []
            
            if 'facteurs_decision' in trajet_data:
                try:
                    trajet_obj['facteurs_decision'] = json.loads(trajet_data['facteurs_decision']) if isinstance(trajet_data['facteurs_decision'], str) else trajet_data['facteurs_decision']
                except:
                    trajet_obj['facteurs_decision'] = []
            
            if 'coherence_geo' in trajet_data:
                try:
                    trajet_obj['coherence_geo'] = json.loads(trajet_data['coherence_geo']) if isinstance(trajet_data['coherence_geo'], str) else trajet_data['coherence_geo']
                except:
                    trajet_obj['coherence_geo'] = {}
            
            trajets_recommandes.append(trajet_obj)
        except Exception as e:
            print(f"Erreur lors du parsing du trajet RDF : {e}")
            continue
    
    # Trier par rang
    trajets_recommandes.sort(key=lambda x: x.get('rang', 999))
    
    # **FALLBACK** : Si pas de trajets dans RDF, utiliser SQLite (transition)
    if not trajets_recommandes:
        trajets_sqlite = TrajetRecommande.objects.filter(demande=demande).order_by('rang')
        trajets_recommandes = list(trajets_sqlite)
    
    # Récupérer les alertes pertinentes
    alertes_pertinentes = AlerteTransportTempsReel.objects.filter(
        active=True,
        date_debut__lte=timezone.now()
    )
    
    # Créer des alertes de démonstration si aucune n'existe
    if not alertes_pertinentes.exists():
        # Créer des alertes factices pour la démonstration
        from datetime import timedelta
        
        try:
            # Créer quelques alertes de test
            AlerteTransportTempsReel.objects.get_or_create(
                titre="Retard ligne Bus 15",
                defaults={
                    'description': "Retard de 10 minutes sur la ligne Bus 15 en direction du centre-ville",
                    'type_alerte': 'retard',
                    'severite': 'important',
                    'ligne_transport': "Bus 15",
                    'date_debut': timezone.now() - timedelta(hours=1),
                    'date_fin': timezone.now() + timedelta(hours=2),
                    'active': True
                }
            )
            
            AlerteTransportTempsReel.objects.get_or_create(
                titre="Vélos disponibles Gare Centrale",
                defaults={
                    'description': "15 vélos électriques disponibles à la station Gare Centrale",
                    'type_alerte': 'information',
                    'severite': 'normal',
                    'ligne_transport': "Vélo-Partage",
                    'date_debut': timezone.now() - timedelta(minutes=30),
                    'date_fin': timezone.now() + timedelta(hours=4),
                    'active': True
                }
            )
            
            AlerteTransportTempsReel.objects.get_or_create(
                titre="Trafic dense Boulevard Principal",
                defaults={
                    'description': "Circulation dense sur le Boulevard Principal, +15 min de trajet estimé",
                    'type_alerte': 'trafic',
                    'severite': 'important',
                    'ligne_transport': "Routes",
                    'date_debut': timezone.now() - timedelta(minutes=45),
                    'date_fin': timezone.now() + timedelta(hours=1),
                    'active': True
                }
            )
            
            # Récupérer les alertes maintenant qu'elles existent
            alertes_pertinentes = AlerteTransportTempsReel.objects.filter(
                active=True,
                date_debut__lte=timezone.now()
            )
        except Exception as e:
            print(f"Erreur lors de la création d'alertes test : {e}")
    
    # Statistiques des véhicules disponibles
    from ..gestion_vehicules.models import Vehicule, TypeVehicule
    
    # Récupérer ou créer des statistiques de véhicules
    vehicules_stats = {
        'bus': 0,
        'velos': 0,
        'auto': 0,
        'total': 0
    }
    
    try:
        # Compter les véhicules réels s'ils existent
        vehicules_stats['bus'] = Vehicule.objects.filter(
            type_vehicule__nom__icontains='bus',
            disponible=True
        ).count()
        
        vehicules_stats['velos'] = Vehicule.objects.filter(
            type_vehicule__nom__icontains='vélo',
            disponible=True
        ).count()
        
        vehicules_stats['auto'] = Vehicule.objects.filter(
            type_vehicule__nom__icontains='voiture',
            disponible=True
        ).count()
        
        vehicules_stats['total'] = vehicules_stats['bus'] + vehicules_stats['velos'] + vehicules_stats['auto']
        
        # Si pas de véhicules, créer des données de démonstration
        if vehicules_stats['total'] == 0:
            vehicules_stats = {
                'bus': 12,
                'velos': 28,
                'auto': 15,
                'total': 55
            }
            
    except Exception as e:
        print(f"Erreur lors de la récupération des véhicules : {e}")
        # Données de démonstration par défaut
        vehicules_stats = {
            'bus': 12,
            'velos': 28,
            'auto': 15,
            'total': 55
        }
    
    context = {
        'page_title': f'Résultats - {demande.lieu_depart} → {demande.lieu_arrivee}',
        'demande': demande,
        'trajets_recommandes': trajets_recommandes,
        'alertes_pertinentes': alertes_pertinentes,
        'vehicules_stats': vehicules_stats,
        'resultats_ia': demande.resultats_json,
        'peut_reevaluer': True,
        'source_donnees': 'RDF' if trajets_rdf else 'SQLite (fallback)',
    }
    
    return render(request, 'gestion_trajets/resultats_trajet.html', context)

@login_required
def temps_reel_transport_view(request):
    """Vue des informations de transport en temps réel"""
    
    # Récupérer toutes les alertes actives
    alertes_par_type = {}
    alertes_actives = AlerteTransportTempsReel.objects.filter(
        active=True,
        date_debut__lte=timezone.now()
    ).order_by('type_alerte', '-date_creation')
    
    for alerte in alertes_actives:
        type_alerte = alerte.get_type_alerte_display()
        if type_alerte not in alertes_par_type:
            alertes_par_type[type_alerte] = []
        alertes_par_type[type_alerte].append(alerte)
    
    # Récupérer les véhicules et leur état
    vehicules_etat = []
    for vehicule in TypeVehiculeIntelligent.objects.filter(disponible=True):
        etat = {
            'vehicule': vehicule,
            'disponibilite': _obtenir_disponibilite_vehicule(vehicule),
            'retard_moyen': _obtenir_retard_moyen(vehicule),
            'prochains_passages': _obtenir_prochains_passages(vehicule)
        }
        vehicules_etat.append(etat)
    
    context = {
        'page_title': 'Transport en Temps Réel - SmartCity',
        'alertes_par_type': alertes_par_type,
        'vehicules_etat': vehicules_etat,
        'nb_alertes_total': len(alertes_actives),
        'derniere_maj': timezone.now()
    }
    
    return render(request, 'gestion_trajets/temps_reel.html', context)

@login_required
def mes_trajets_view(request):
    """Historique des trajets de l'utilisateur avec filtres et statistiques"""
    
    # **NOUVEAUTÉ** : Récupérer les trajets depuis RDF
    trajets_rdf = rdf_manager.get_trajets_by_user(request.user.id)
    
    # Récupérer aussi les demandes pour enrichir les informations
    demandes = DemandeTrajetIntelligent.objects.filter(
        utilisateur=request.user
    ).prefetch_related('trajets_ia', 'vehicules_preferes')
    
    # Filtrage
    statut_filtre = request.GET.get('statut')
    type_filtre = request.GET.get('type')
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')
    
    if statut_filtre:
        demandes = demandes.filter(statut=statut_filtre)
    if type_filtre:
        demandes = demandes.filter(type_trajet=type_filtre)
    if date_debut:
        try:
            date_debut_parsed = timezone.datetime.strptime(date_debut, '%Y-%m-%d').date()
            demandes = demandes.filter(date_creation__date__gte=date_debut_parsed)
        except ValueError:
            pass
    if date_fin:
        try:
            date_fin_parsed = timezone.datetime.strptime(date_fin, '%Y-%m-%d').date()
            demandes = demandes.filter(date_creation__date__lte=date_fin_parsed)
        except ValueError:
            pass
    
    demandes = demandes.order_by('-date_creation')
    
    # **NOUVEAUTÉ** : Calcul des statistiques depuis RDF
    total_trajets = len(trajets_rdf)
    distance_totale = 0
    temps_total = 0
    cout_total = 0
    
    for trajet in trajets_rdf:
        try:
            # ✅ CORRECTION: Utiliser les noms de propriétés RDF corrects
            distance_totale += float(trajet.get('distance', 0))  # ✅ "distance" au lieu de "distance_km"
            temps_total += float(trajet.get('durée', 0))  # ✅ "durée" au lieu de "duree_minutes"
            cout_total += float(trajet.get('coût', 0))  # ✅ "coût" au lieu de "cout_total"
        except (ValueError, TypeError):
            continue
    
    # Conversion du temps en heures
    temps_total_heures = round(temps_total / 60, 1) if temps_total > 0 else 0
    
    # **FALLBACK** : Si pas de trajets RDF, utiliser SQLite
    if not trajets_rdf:
        for demande in demandes:
            meilleur_trajet = demande.trajets_ia.first()
            if meilleur_trajet:
                distance_totale += meilleur_trajet.distance_km
                temps_total += meilleur_trajet.duree_minutes
                cout_total += meilleur_trajet.cout_total
        temps_total_heures = round(temps_total / 60, 1)
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(demandes, 12)  # 12 trajets par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_title': 'Mes Trajets - SmartCity',
        'demandes': page_obj,
        'total_trajets': total_trajets if trajets_rdf else demandes.count(),
        'distance_totale': round(distance_totale, 2),
        'temps_total': temps_total_heures,
        'cout_total': round(cout_total, 2),
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
        'source_donnees': 'RDF' if trajets_rdf else 'SQLite (fallback)',
    }
    
    return render(request, 'gestion_trajets/mes_trajets.html', context)

@login_required
def preferences_trajet_view(request):
    """Gestion des préférences de trajet de l'utilisateur"""
    
    preferences, created = PreferenceUtilisateurIA.objects.get_or_create(
        utilisateur=request.user,
        defaults={
            'priorite_defaut': 'rapidite',
            'budget_defaut': 20.0,
            'duree_max_defaut': 60,
            'tolerance_marche': 10,
            'poids_historique': 0.3,
        }
    )
    
    vehicules_disponibles = TypeVehiculeIntelligent.objects.filter(disponible=True)
    
    if request.method == 'POST':
        # Mettre à jour les préférences
        preferences.priorite_defaut = request.POST.get('priorite_defaut', 'rapidite')
        preferences.budget_defaut = float(request.POST.get('budget_defaut', 20.0))
        preferences.duree_max_defaut = int(request.POST.get('duree_max_defaut', 60))
        preferences.necessite_pmr = request.POST.get('necessite_pmr') == 'on'
        preferences.preference_directe = request.POST.get('preference_directe') == 'on'
        preferences.apprentissage_actif = request.POST.get('apprentissage_actif') == 'on'
        preferences.tolerance_marche = int(request.POST.get('tolerance_marche', 10))
        preferences.poids_historique = float(request.POST.get('poids_historique', 0.3))
        preferences.recevoir_alertes = request.POST.get('recevoir_alertes') == 'on'
        preferences.avance_notification = int(request.POST.get('avance_notification', 10))
        
        preferences.save()
        
        # Mettre à jour les véhicules favoris
        vehicules_favoris = request.POST.getlist('vehicules_favoris')
        preferences.vehicules_favoris.set(vehicules_favoris)
        
        vehicules_evites = request.POST.getlist('vehicules_evites')
        preferences.vehicules_evites.set(vehicules_evites)
        
        messages.success(request, "Préférences mises à jour avec succès !")
        return redirect('gestion_trajets:preferences_trajet')
    
    context = {
        'page_title': 'Mes Préférences de Trajet - SmartCity',
        'preferences': preferences,
        'vehicules_disponibles': vehicules_disponibles,
        'priorites_choix': DemandeTrajetIntelligent.PRIORITES,
    }
    
    return render(request, 'gestion_trajets/preferences_trajet.html', context)

@login_required
@require_http_methods(["POST"])
def supprimer_demande_trajet_view(request, demande_id):
    """Supprime une demande de trajet et ses trajets associés"""
    
    try:
        # Récupérer la demande appartenant à l'utilisateur
        demande = get_object_or_404(DemandeTrajetIntelligent, id=demande_id, utilisateur=request.user)
        
        # **NOUVEAUTÉ** : Supprimer aussi les trajets RDF associés
        try:
            trajets_rdf = rdf_manager.list_trajets(
                filtre_utilisateur=request.user.id,
                filtre_demande=demande_id
            )
            
            # Supprimer chaque trajet RDF
            for trajet_data in trajets_rdf:
                trajet_id = trajet_data.get('uri', '').split('#')[-1]  # Extraire l'ID de l'URI
                if trajet_id:
                    success, message = rdf_manager.delete_trajet(trajet_id)
                    if success:
                        print(f"✅ Trajet RDF supprimé: {trajet_id}")
                    else:
                        print(f"❌ Erreur suppression RDF: {message}")
                        
        except Exception as e:
            print(f"⚠️ Erreur lors de la suppression RDF: {e}")
            # Continuer même si la suppression RDF échoue
        
        # Informations pour le message de confirmation
        lieu_depart = demande.lieu_depart
        lieu_arrivee = demande.lieu_arrivee
        nb_trajets = demande.trajets_ia.count()
        
        # Supprimer la demande (cascade supprimera aussi les TrajetRecommande)
        demande.delete()
        
        # Message de succès
        messages.success(
            request, 
            f"✅ Trajet supprimé avec succès !<br>"
            f"<strong>{lieu_depart} → {lieu_arrivee}</strong><br>"
            f"{nb_trajets} option(s) de trajet supprimée(s)."
        )
        
        print(f"🗑️ Demande supprimée: {demande_id} ({lieu_depart} → {lieu_arrivee})")
        
    except Exception as e:
        messages.error(request, f"❌ Erreur lors de la suppression: {str(e)}")
        print(f"❌ Erreur suppression demande {demande_id}: {e}")
    
    # Rediriger vers la liste des trajets
    return redirect('gestion_trajets:mes_trajets')

# ========== VUES AJAX ==========

@login_required
def ajax_recherche_lieux(request):
    """Recherche de lieux en AJAX pour l'autocomplétion"""
    
    query = request.GET.get('q', '').strip()
    if len(query) < 3:
        return JsonResponse({'lieux': []})
    
    # Simulation de recherche de lieux (en production, utiliserait une API de géolocalisation)
    lieux_simules = [
        {'nom': 'Gare Centrale', 'adresse': 'Place de la Gare, Centre-ville', 'lat': 48.8566, 'lng': 2.3522},
        {'nom': 'Université Sciences', 'adresse': 'Campus Universitaire', 'lat': 48.8606, 'lng': 2.3376},
        {'nom': 'Centre Commercial Les Halles', 'adresse': 'Rue de Rivoli', 'lat': 48.8606, 'lng': 2.3376},
        {'nom': 'Hôpital Saint-Louis', 'adresse': 'Avenue Claude Vellefaux', 'lat': 48.8606, 'lng': 2.3376},
        {'nom': 'Aéroport International', 'adresse': 'Zone Aéroportuaire', 'lat': 48.8606, 'lng': 2.3376},
        {'nom': 'Parc Central', 'adresse': 'Avenue des Tilleuls', 'lat': 48.8566, 'lng': 2.3522},
    ]
    
    lieux_filtres = [lieu for lieu in lieux_simules if query.lower() in lieu['nom'].lower()]
    
    return JsonResponse({'lieux': lieux_filtres})

@login_required
def ajax_actualiser_temps_reel(request, demande_id):
    """Actualise les informations temps réel pour un trajet"""
    
    try:
        demande = get_object_or_404(DemandeTrajetIntelligent, id=demande_id, utilisateur=request.user)
        
        # Récupérer les nouvelles informations temps réel
        conditions_actuelles = moteur_trajet_ia._analyser_conditions_temps_reel(demande)
        
        # **NOUVEAUTÉ** : Récupérer les trajets depuis RDF
        trajets_rdf = rdf_manager.list_trajets(
            filtre_utilisateur=request.user.id,
            filtre_demande=demande_id
        )
        
        trajets_data = []
        
        # Utiliser RDF si disponible
        if trajets_rdf:
            for trajet in trajets_rdf:
                # ✅ CORRECTION: Utiliser "mode" au lieu de "vehicule_nom"
                vehicule_nom = trajet.get('mode', '').lower()
                nouveau_retard = conditions_actuelles['retards_moyens'].get(vehicule_nom, 0)
                
                trajets_data.append({
                    'uri': trajet.get('uri'),
                    'rang': trajet.get('rang'),
                    'vehicule_nom': trajet.get('mode'),  # ✅ "mode" au lieu de "vehicule_nom"
                    'retard_estime': nouveau_retard,
                    'circulation': conditions_actuelles['circulation_generale'],
                    'alertes': conditions_actuelles['alertes_transport'],
                    'prochains_departs': moteur_trajet_ia._generer_prochains_horaires({})
                })
        else:
            # Fallback vers SQLite
            trajets = TrajetRecommande.objects.filter(demande=demande)
            for trajet in trajets:
                vehicule = trajet.vehicules_utilises.first()
                vehicule_nom = vehicule.nom.lower() if vehicule else ''
                nouveau_retard = conditions_actuelles['retards_moyens'].get(vehicule_nom, 0)
                
                trajets_data.append({
                    'id': trajet.id,
                    'retard_estime': nouveau_retard,
                    'circulation': conditions_actuelles['circulation_generale'],
                    'alertes': conditions_actuelles['alertes_transport'],
                    'prochains_departs': moteur_trajet_ia._generer_prochains_horaires({})
                })
        
        return JsonResponse({
            'statut': 'success',
            'trajets': trajets_data,
            'conditions_generales': conditions_actuelles,
            'timestamp': timezone.now().isoformat(),
            'source': 'RDF' if trajets_rdf else 'SQLite'
        })
        
    except Exception as e:
        return JsonResponse({'statut': 'error', 'erreur': str(e)})

@login_required
def ajax_calculer_itineraire(request):
    """Calcule un itinéraire détaillé entre deux points en utilisant un service de routing externe"""
    
    try:
        # Récupérer les paramètres
        lat_depart = float(request.GET.get('lat_depart'))
        lng_depart = float(request.GET.get('lng_depart'))
        lat_arrivee = float(request.GET.get('lat_arrivee'))
        lng_arrivee = float(request.GET.get('lng_arrivee'))
        mode_transport = request.GET.get('mode', 'driving')  # driving, walking, cycling
        
        # **NOUVEAUTÉ** : Utiliser un service de routing externe
        itineraire_data = _calculer_itineraire_externe(
            lat_depart, lng_depart, 
            lat_arrivee, lng_arrivee, 
            mode_transport
        )
        
        if itineraire_data['success']:
            # Sauvegarder l'itinéraire dans RDF si demandé
            trajet_id = request.GET.get('trajet_id')
            if trajet_id:
                _sauvegarder_itineraire_rdf(trajet_id, itineraire_data)
            
            return JsonResponse({
                'statut': 'success',
                'itineraire': itineraire_data['route'],
                'distance_km': itineraire_data['distance'],
                'duree_minutes': itineraire_data['duration'],
                'instructions': itineraire_data['instructions'],
                'source': itineraire_data['source']
            })
        else:
            return JsonResponse({
                'statut': 'error',
                'erreur': itineraire_data['error']
            })
            
    except Exception as e:
        return JsonResponse({'statut': 'error', 'erreur': str(e)})

@login_required
def ajax_recherche_trajets_intelligente(request):
    """Recherche intelligente de trajets : RDF puis services externes"""
    
    try:
        lieu_depart = request.GET.get('lieu_depart', '').strip()
        lieu_arrivee = request.GET.get('lieu_arrivee', '').strip()
        priorite = request.GET.get('priorite', 'rapidite')
        
        # **ÉTAPE 1** : Rechercher dans RDF d'abord
        trajets_rdf = rdf_manager.search_trajets_similaires(
            lieu_depart=lieu_depart,
            lieu_arrivee=lieu_arrivee,
            priorite=priorite,
            utilisateur_id=request.user.id
        )
        
        trajets_resultats = []
        
        # **ÉTAPE 2** : Si trajets trouvés dans RDF, les utiliser
        if trajets_rdf:
            for trajet in trajets_rdf:
                trajets_resultats.append({
                    'source': 'RDF',
                    'score_pertinence': trajet.get('score_pertinence', 0.8),
                    'duree_minutes': trajet.get('durée', 0),
                    'distance_km': trajet.get('distance', 0),
                    'cout_total': trajet.get('coût', 0),
                    'mode_transport': trajet.get('mode', 'Inconnu'),
                    'empreinte_carbone': trajet.get('empreinteCarbone', 0),
                    'score_ia': trajet.get('scoreIA', 0),
                    'uri': trajet.get('uri')
                })
        
        # **ÉTAPE 3** : Si pas assez de trajets RDF, utiliser services externes
        if len(trajets_resultats) < 3:
            trajets_externes = _rechercher_trajets_externes(
                lieu_depart, lieu_arrivee, priorite
            )
            
            for trajet_ext in trajets_externes:
                trajets_resultats.append({
                    'source': 'Externe',
                    'score_pertinence': trajet_ext.get('score', 0.5),
                    'duree_minutes': trajet_ext.get('duration', 0),
                    'distance_km': trajet_ext.get('distance', 0),
                    'cout_total': trajet_ext.get('cost', 0),
                    'mode_transport': trajet_ext.get('mode', 'Inconnu'),
                    'empreinte_carbone': trajet_ext.get('emissions', 0),
                    'score_ia': trajet_ext.get('ai_score', 5.0),
                    'service_externe': trajet_ext.get('provider', 'API')
                })
        
        # Trier par score de pertinence
        trajets_resultats.sort(key=lambda x: x['score_pertinence'], reverse=True)
        
        return JsonResponse({
            'statut': 'success',
            'trajets': trajets_resultats[:5],  # Limiter à 5 résultats
            'nb_rdf': len([t for t in trajets_resultats if t['source'] == 'RDF']),
            'nb_externes': len([t for t in trajets_resultats if t['source'] == 'Externe']),
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        return JsonResponse({'statut': 'error', 'erreur': str(e)})

# ========== FONCTIONS UTILITAIRES ==========

def _grouper_vehicules_par_categorie(vehicules):
    """Groupe les véhicules par catégorie"""
    par_categorie = {}
    for vehicule in vehicules:
        categorie = vehicule.get_categorie_display()
        if categorie not in par_categorie:
            par_categorie[categorie] = []
        par_categorie[categorie].append(vehicule)
    return par_categorie

def _calculer_itineraire_externe(lat_depart, lng_depart, lat_arrivee, lng_arrivee, mode='driving'):
    """
    Calcule un itinéraire en utilisant un service externe (OpenRouteService)
    
    Args:
        lat_depart, lng_depart: Coordonnées de départ
        lat_arrivee, lng_arrivee: Coordonnées d'arrivée  
        mode: Mode de transport ('driving', 'walking', 'cycling')
    
    Returns:
        Dict avec les données de l'itinéraire ou erreur
    """
    try:
        import requests
        import time
        
        # **OPTION 1** : OpenRouteService (gratuit avec clé API)
        # Remplacez 'YOUR_API_KEY' par votre clé OpenRouteService
        api_key = "5b3ce3597851110001cf62489f35a56e30e74eaca14ea3bfaff6e648"  # Clé de démo
        
        # Profils de transport selon le mode
        profiles = {
            'driving': 'driving-car',
            'walking': 'foot-walking', 
            'cycling': 'cycling-regular'
        }
        
        profile = profiles.get(mode, 'driving-car')
        
        # URL de l'API OpenRouteService
        url = f"https://api.openrouteservice.org/v2/directions/{profile}"
        
        # Paramètres de la requête
        params = {
            'api_key': api_key,
            'start': f"{lng_depart},{lat_depart}",  # longitude,latitude
            'end': f"{lng_arrivee},{lat_arrivee}",
            'format': 'json'
        }
        
        # Faire la requête
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'features' in data and len(data['features']) > 0:
                route = data['features'][0]
                properties = route['properties']
                geometry = route['geometry']
                
                # Extraire les informations
                distance_m = properties['segments'][0]['distance']
                duration_s = properties['segments'][0]['duration']
                
                # Coordonnées de l'itinéraire
                coordinates = geometry['coordinates']
                route_points = [[coord[1], coord[0]] for coord in coordinates]  # lat,lng
                
                # Instructions
                instructions = []
                if 'segments' in properties and 'steps' in properties['segments'][0]:
                    for step in properties['segments'][0]['steps']:
                        instructions.append({
                            'instruction': step.get('instruction', ''),
                            'distance': step.get('distance', 0),
                            'duration': step.get('duration', 0)
                        })
                
                return {
                    'success': True,
                    'route': route_points,
                    'distance': round(distance_m / 1000, 2),  # km
                    'duration': round(duration_s / 60, 1),    # minutes
                    'instructions': instructions,
                    'source': 'OpenRouteService'
                }
            else:
                return {
                    'success': False,
                    'error': 'Aucun itinéraire trouvé'
                }
        else:
            # **FALLBACK** : Itinéraire simple (ligne droite)
            return _calculer_itineraire_simple(lat_depart, lng_depart, lat_arrivee, lng_arrivee)
            
    except Exception as e:
        print(f"Erreur API routing: {e}")
        # Fallback vers calcul simple
        return _calculer_itineraire_simple(lat_depart, lng_depart, lat_arrivee, lng_arrivee)

def _calculer_itineraire_simple(lat_depart, lng_depart, lat_arrivee, lng_arrivee):
    """Calcul d'itinéraire simple (ligne droite) en cas d'échec de l'API externe"""
    
    try:
        from math import radians, cos, sin, asin, sqrt
        
        # Formule de Haversine pour calculer la distance
        def haversine(lon1, lat1, lon2, lat2):
            lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
            dlon = lon2 - lon1
            dlat = lat2 - lat1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a))
            r = 6371  # Rayon de la Terre en km
            return c * r
        
        distance_km = haversine(lng_depart, lat_depart, lng_arrivee, lat_arrivee)
        
        # Estimation de la durée (50 km/h en voiture)
        duree_minutes = (distance_km / 50) * 60
        
        # Itinéraire simple (ligne droite)
        route_points = [
            [lat_depart, lng_depart],
            [lat_arrivee, lng_arrivee]
        ]
        
        return {
            'success': True,
            'route': route_points,
            'distance': round(distance_km, 2),
            'duration': round(duree_minutes, 1),
            'instructions': [
                {
                    'instruction': f'Aller de {lat_depart:.4f},{lng_depart:.4f} vers {lat_arrivee:.4f},{lng_arrivee:.4f}',
                    'distance': distance_km * 1000,
                    'duration': duree_minutes * 60
                }
            ],
            'source': 'Calcul simple (ligne droite)'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Erreur de calcul: {str(e)}'
        }

def _rechercher_trajets_externes(lieu_depart, lieu_arrivee, priorite):
    """
    Recherche de trajets via des services externes (simulation pour la démo)
    En production, ceci utiliserait des APIs de transport public, covoiturage, etc.
    """
    
    try:
        # **SIMULATION** : Génération de trajets fictifs
        # En réalité, ceci ferait des appels à des APIs comme:
        # - Google Maps Directions API
        # - Citymapper API
        # - APIs de transport public local
        # - APIs de covoiturage (BlaBlaCar, etc.)
        
        trajets_simules = []
        
        # Trajet 1: Transport public simulé
        trajets_simules.append({
            'mode': 'Transport Public',
            'duration': 35,
            'distance': 12.5,
            'cost': 2.5,
            'emissions': 120,
            'score': 0.7,
            'ai_score': 7.2,
            'provider': 'API Transport Public'
        })
        
        # Trajet 2: Vélo simulé
        trajets_simules.append({
            'mode': 'Vélo',
            'duration': 45,
            'distance': 12.1,
            'cost': 0,
            'emissions': 0,
            'score': 0.6,
            'ai_score': 8.5,
            'provider': 'API Vélo-partage'
        })
        
        # Trajet 3: Covoiturage simulé
        trajets_simules.append({
            'mode': 'Covoiturage',
            'duration': 25,
            'distance': 13.2,
            'cost': 4.0,
            'emissions': 80,
            'score': 0.8,
            'ai_score': 7.8,
            'provider': 'API Covoiturage'
        })
        
        # Ajuster les scores selon la priorité
        if priorite == 'rapidite':
            for trajet in trajets_simules:
                trajet['score'] += (60 - trajet['duration']) / 100
        elif priorite == 'economie':
            for trajet in trajets_simules:
                trajet['score'] += (10 - trajet['cost']) / 10
        elif priorite == 'ecologie':
            for trajet in trajets_simules:
                trajet['score'] += (200 - trajet['emissions']) / 200
        
        return trajets_simules
        
    except Exception as e:
        print(f"Erreur recherche trajets externes: {e}")
        return []

def _sauvegarder_itineraire_rdf(trajet_id, itineraire_data):
    """Sauvegarde les détails d'un itinéraire dans RDF"""
    
    try:
        # Préparer les données pour RDF
        itineraire_rdf = {
            'trajet_id': trajet_id,
            'route_coordinates': json.dumps(itineraire_data['route']),
            'distance_calculee': itineraire_data['distance'],
            'duree_calculee': itineraire_data['duration'],
            'instructions_json': json.dumps(itineraire_data['instructions']),
            'source_routing': itineraire_data['source'],
            'date_calcul': timezone.now().isoformat()
        }
        
        # Sauvegarder dans RDF (à implémenter dans rdf_utils.py)
        success, result = rdf_manager.update_trajet_itineraire(trajet_id, itineraire_rdf)
        
        if success:
            print(f"✅ Itinéraire sauvegardé pour trajet {trajet_id}")
        else:
            print(f"❌ Erreur sauvegarde itinéraire: {result}")
            
    except Exception as e:
        print(f"Erreur sauvegarde itinéraire RDF: {e}")

def _creer_trajets_recommandes(demande, trajets_ia):
    """Crée les objets TrajetRecommande dans le fichier RDF à partir des résultats IA"""
    
    for i, trajet_data in enumerate(trajets_ia):
        # Préparer les données pour RDF
        trajet_rdf_data = {
            'utilisateur_id': demande.utilisateur.id,
            'utilisateur_username': demande.utilisateur.username,
            'demande_id': demande.id,
            'lieu_depart': demande.lieu_depart,
            'lieu_arrivee': demande.lieu_arrivee,
            'rang': trajet_data['rang'],
            'duree_minutes': trajet_data['duree_minutes'],
            'distance_km': trajet_data['distance_km'],
            'cout_total': trajet_data['cout_euros'],
            'empreinte_carbone_g': trajet_data['empreinte_carbone_g'],
            'score_confort': trajet_data['score_confort'],
            'niveau_circulation': trajet_data.get('circulation_niveau', 'moyen'),
            'retard_estime': trajet_data.get('retard_estime', 0),
            'fiabilite_score': trajet_data.get('fiabilite', 8.0),
            'score_ia': trajet_data['score_ia'],
            'etapes_json': json.dumps(trajet_data.get('etapes', [])),
            'facteurs_decision': json.dumps(trajet_data.get('facteurs_decision', [])),
            'alertes_trafic': json.dumps(trajet_data.get('alertes_actives', [])),
            'horaires_transport': json.dumps(trajet_data.get('horaires_temps_reel', {})),
            'vehicule_nom': trajet_data.get('vehicule_nom', 'Inconnu'),
            'vehicule_type': trajet_data.get('vehicule_type', 'autre'),
        }
        
        # **NOUVEAUTÉ** : Ajouter les informations de cohérence géographique si disponibles
        if 'zone_geographique' in trajet_data:
            trajet_rdf_data['zone_geographique'] = trajet_data['zone_geographique']
        if 'distance_reelle_km' in trajet_data:
            trajet_rdf_data['distance_reelle_km'] = trajet_data['distance_reelle_km']
        if 'coherence_geo' in trajet_data:
            trajet_rdf_data['coherence_geo'] = json.dumps(trajet_data['coherence_geo'])
        
        # Sauvegarder dans RDF
        success, trajet_uri = rdf_manager.create_trajet(trajet_rdf_data)
        
        if success:
            print(f"✅ Trajet {i+1} sauvegardé dans RDF : {trajet_uri}")
        else:
            print(f"❌ Erreur lors de la sauvegarde du trajet {i+1} : {trajet_uri}")
        
        # **OPTIONNEL** : Garder aussi dans SQLite pour compatibilité (transition)
        # Vous pouvez commenter ce bloc plus tard quand tout fonctionne
        trajet_sqlite = TrajetRecommande.objects.create(
            demande=demande,
            rang=trajet_data['rang'],
            duree_minutes=trajet_data['duree_minutes'],
            distance_km=trajet_data['distance_km'],
            cout_total=trajet_data['cout_euros'],
            empreinte_carbone_g=trajet_data['empreinte_carbone_g'],
            score_confort=trajet_data['score_confort'],
            niveau_circulation=trajet_data.get('circulation_niveau', 'moyen'),
            retard_estime=trajet_data.get('retard_estime', 0),
            fiabilite_score=trajet_data.get('fiabilite', 8.0),
            score_ia=trajet_data['score_ia'],
            etapes_json=trajet_data.get('etapes', []),
            facteurs_decision=trajet_data.get('facteurs_decision', []),
            alertes_trafic=trajet_data.get('alertes_actives', []),
            horaires_transport=trajet_data.get('horaires_temps_reel', {}),
        )
        
        # Associer les véhicules (seulement pour SQLite)
        if 'vehicule_id' in trajet_data and trajet_data['vehicule_id'] is not None:
            try:
                vehicule = TypeVehiculeIntelligent.objects.get(id=trajet_data['vehicule_id'])
                trajet_sqlite.vehicules_utilises.add(vehicule)
            except TypeVehiculeIntelligent.DoesNotExist:
                pass

def _obtenir_disponibilite_vehicule(vehicule):
    """Simule la disponibilité d'un véhicule"""
    import random
    if vehicule.categorie == 'partage':
        return random.randint(60, 95)  # %
    return 100

def _obtenir_retard_moyen(vehicule):
    """Simule le retard moyen d'un véhicule"""
    import random
    if vehicule.categorie == 'public':
        return random.randint(0, 8)  # minutes
    return 0

def _obtenir_prochains_passages(vehicule):
    """Simule les prochains passages"""
    import random
    if vehicule.categorie == 'public':
        passages = []
        for i in range(3):
            minutes = 5 + i * random.randint(8, 15)
            passages.append(f"{minutes}min")
        return passages
    return []