from django.contrib import admin
from django.shortcuts import render, redirect
from django.urls import path, reverse
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
from ..ontology_manager.rdf_utils import RDFUtils

class StationAdmin(admin.ModelAdmin):
    """Admin personnalisé pour la gestion des stations via l'interface d'administration"""
    
    def get_urls(self):
        """URLs personnalisées pour l'admin des stations"""
        urls = super().get_urls()
        custom_urls = [
            path('ajouter-station/', self.admin_site.admin_view(self.ajouter_station_view), 
                 name='gestion_stations_station_ajouter'),
            path('liste-stations/', self.admin_site.admin_view(self.liste_stations_view),
                 name='gestion_stations_station_liste'),
            path('api/stations/', self.admin_site.admin_view(self.api_stations), 
                 name='gestion_stations_station_api'),
        ]
        return custom_urls + urls
    
    def ajouter_station_view(self, request):
        """Vue pour ajouter une station depuis l'admin"""
        if request.method == 'POST':
            try:
                nom = request.POST.get('nom')
                latitude = float(request.POST.get('latitude'))
                longitude = float(request.POST.get('longitude'))
                adresse = request.POST.get('adresse', '')
                capacite = int(request.POST.get('capacite', 0))
                type_station = request.POST.get('type_station', 'Standard')
                
                # Valider les données
                if not nom or not latitude or not longitude:
                    messages.error(request, "Nom, latitude et longitude sont obligatoires")
                    return render(request, 'admin/gestion_stations/ajouter_station.html')
                
                # Ajouter la station via RDF
                rdf_utils = RDFUtils()
                station_uri = rdf_utils.add_station(nom, latitude, longitude, adresse, capacite, type_station)
                
                if station_uri:
                    messages.success(request, f"Station '{nom}' ajoutée avec succès")
                    return redirect('admin:gestion_stations_station_liste')
                else:
                    messages.error(request, "Erreur lors de l'ajout de la station")
                    
            except (ValueError, TypeError) as e:
                messages.error(request, f"Erreur de validation : {str(e)}")
            except Exception as e:
                messages.error(request, f"Erreur : {str(e)}")
        
        return render(request, 'admin/gestion_stations/ajouter_station.html')
    
    def liste_stations_view(self, request):
        """Vue pour lister les stations depuis l'admin"""
        try:
            rdf_utils = RDFUtils()
            stations = rdf_utils.get_all_stations()
            
            context = {
                'title': 'Gestion des Stations',
                'stations': stations,
                'opts': {'verbose_name_plural': 'Stations'}
            }
            return render(request, 'admin/gestion_stations/liste_stations.html', context)
        except Exception as e:
            messages.error(request, f"Erreur lors du chargement des stations : {str(e)}")
            return render(request, 'admin/gestion_stations/liste_stations.html', {
                'title': 'Gestion des Stations',
                'stations': [],
                'opts': {'verbose_name_plural': 'Stations'}
            })
    
    @method_decorator(csrf_exempt)
    def api_stations(self, request):
        """API pour récupérer les stations (pour la carte)"""
        try:
            rdf_utils = RDFUtils()
            stations = rdf_utils.get_all_stations()
            
            stations_data = []
            for station in stations:
                stations_data.append({
                    'id': station.get('uri', ''),
                    'nom': station.get('nom', ''),
                    'latitude': float(station.get('latitude', 0)),
                    'longitude': float(station.get('longitude', 0)),
                    'adresse': station.get('adresse', ''),
                    'capacite': int(station.get('capacite', 0)),
                    'type_station': station.get('type_station', 'Standard')
                })
            
            return JsonResponse({'stations': stations_data})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

# Proxy model pour l'admin
class Station:
    """Modèle proxy pour l'administration des stations"""
    class Meta:
        verbose_name = "Station"
        verbose_name_plural = "Stations"
        app_label = 'gestion_stations'

# Enregistrer l'admin
admin.site.register(Station, StationAdmin)