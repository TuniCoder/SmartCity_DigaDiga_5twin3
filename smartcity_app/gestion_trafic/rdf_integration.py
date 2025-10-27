"""
Module d'intégration RDF pour les capteurs de trafic
Automatise l'insertion des nouveaux capteurs dans mobility_ontology_clean.rdf
"""

import os
import xml.etree.ElementTree as ET
from datetime import datetime
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import CapteurTrafic

# Chemin vers le fichier RDF
RDF_FILE_PATH = os.path.join(settings.BASE_DIR, 'ontology', 'mobility_ontology_clean.rdf')

def generate_capteur_rdf_id(capteur):
    """Génère un ID unique pour le capteur dans le RDF"""
    return f"CapteurTrafic_{capteur.id}_{capteur.code_capteur.replace('-', '_')}"

def create_capteur_rdf_element(capteur):
    """Crée l'élément RDF pour un capteur"""
    
    # Générer l'ID unique
    capteur_id = generate_capteur_rdf_id(capteur)
    
    # Créer l'élément Description
    description = ET.Element('rdf:Description')
    description.set('rdf:about', f'http://example.org/mobility-ontology/2025/09#{capteur_id}')
    
    # Type de ressource
    type_elem = ET.SubElement(description, 'rdf:type')
    type_elem.set('rdf:resource', 'http://example.org/mobility-ontology/2025/09#CapteurTrafic')
    
    # Label
    label_elem = ET.SubElement(description, 'rdfs:label')
    label_elem.set('xml:lang', 'fr')
    label_elem.text = f"Capteur {capteur.nom}"
    
    # Propriétés du capteur
    properties = [
        ('mobility:nomCapteur', capteur.nom),
        ('mobility:codeCapteur', capteur.code_capteur),
        ('mobility:typeCapteur', capteur.type_capteur),
        ('mobility:latitude', str(capteur.latitude)),
        ('mobility:longitude', str(capteur.longitude)),
        ('mobility:directionMesure', capteur.direction_mesure),
        ('mobility:statutCapteur', capteur.statut),
        ('mobility:frequenceMesure', str(capteur.frequence_mesure)),
        ('mobility:precisionDetection', str(capteur.precision_detection)),
        ('mobility:vitesseMinDetection', str(capteur.vitesse_min_detection)),
        ('mobility:vitesseMaxDetection', str(capteur.vitesse_max_detection)),
        ('mobility:dateInstallation', capteur.date_installation.strftime('%Y-%m-%d')),
        ('mobility:fournisseur', capteur.fournisseur or ''),
        ('mobility:modele', capteur.modele or ''),
        ('mobility:zoneTrafic', capteur.zone_trafic.nom),
        ('mobility:dateCreation', capteur.date_creation.strftime('%Y-%m-%dT%H:%M:%S')),
    ]
    
    for prop_name, prop_value in properties:
        if prop_value:  # Ne pas ajouter les valeurs vides
            prop_elem = ET.SubElement(description, prop_name)
            prop_elem.set('rdf:datatype', 'http://www.w3.org/2001/XMLSchema#string')
            prop_elem.text = str(prop_value)
    
    # Ajouter les propriétés spécifiques pour les coordonnées et dates
    if capteur.latitude:
        lat_elem = ET.SubElement(description, 'mobility:latitude')
        lat_elem.set('rdf:datatype', 'http://www.w3.org/2001/XMLSchema#float')
        lat_elem.text = str(capteur.latitude)
    
    if capteur.longitude:
        lng_elem = ET.SubElement(description, 'mobility:longitude')
        lng_elem.set('rdf:datatype', 'http://www.w3.org/2001/XMLSchema#float')
        lng_elem.text = str(capteur.longitude)
    
    if capteur.frequence_mesure:
        freq_elem = ET.SubElement(description, 'mobility:frequenceMesure')
        freq_elem.set('rdf:datatype', 'http://www.w3.org/2001/XMLSchema#int')
        freq_elem.text = str(capteur.frequence_mesure)
    
    if capteur.precision_detection:
        prec_elem = ET.SubElement(description, 'mobility:precisionDetection')
        prec_elem.set('rdf:datatype', 'http://www.w3.org/2001/XMLSchema#float')
        prec_elem.text = str(capteur.precision_detection)
    
    return description

def add_capteur_to_rdf(capteur):
    """Ajoute un capteur au fichier RDF de manière optimisée (solution rapide)"""
    import logging
    logger = logging.getLogger(__name__)

    try:
        # Vérifier que le fichier RDF existe
        if not os.path.exists(RDF_FILE_PATH):
            logger.error(f"Fichier RDF introuvable : {RDF_FILE_PATH}")
            return False

        # Générer l'ID unique
        capteur_id = generate_capteur_rdf_id(capteur)
        capteur_uri = f"http://example.org/mobility-ontology/2025/09#{capteur_id}"

        logger.debug(f"Tentative d'ajout du capteur {capteur.nom} avec URI: {capteur_uri}")

        # Vérification rapide : chercher dans les 30 dernières lignes seulement
        try:
            with open(RDF_FILE_PATH, 'rb') as f:
                # Aller à la fin du fichier (moins les 50 dernières lignes)
                file_size = f.seek(0, 2)
                seek_pos = max(0, file_size - 5000)
                f.seek(seek_pos)
                tail_content = f.read().decode('utf-8', errors='ignore')

                if capteur_uri in tail_content:
                    logger.info(f"Capteur {capteur.nom} déjà présent dans le RDF")
                    return True  # Déjà présent
        except Exception as e:
            logger.warning(f"Erreur lors de la vérification de duplication : {e}")

        # Échapper les caractères XML spéciaux
        def escape_xml(text):
            if text is None:
                return ''
            return str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&apos;')

        # Fonction pour formater les dates (gère les strings et les objets date)
        def format_date(date_obj):
            if date_obj is None:
                return ''
            if isinstance(date_obj, str):
                return date_obj  # Déjà formatée
            return date_obj.strftime('%Y-%m-%d')

        def format_datetime(datetime_obj):
            if datetime_obj is None:
                return ''
            if isinstance(datetime_obj, str):
                return datetime_obj  # Déjà formatée
            return datetime_obj.strftime('%Y-%m-%dT%H:%M:%S')

        # Créer le contenu RDF pour le capteur
        capteur_rdf = f'''  <rdf:Description rdf:about="http://example.org/mobility-ontology/2025/09#{capteur_id}">
    <rdf:type rdf:resource="http://example.org/mobility-ontology/2025/09#CapteurTrafic"/>
    <rdfs:label xml:lang="fr">Capteur {escape_xml(capteur.nom)}</rdfs:label>
    <mobility:nomCapteur rdf:datatype="http://www.w3.org/2001/XMLSchema#string">{escape_xml(capteur.nom)}</mobility:nomCapteur>
    <mobility:codeCapteur rdf:datatype="http://www.w3.org/2001/XMLSchema#string">{escape_xml(capteur.code_capteur)}</mobility:codeCapteur>
    <mobility:typeCapteur rdf:datatype="http://www.w3.org/2001/XMLSchema#string">{escape_xml(capteur.type_capteur)}</mobility:typeCapteur>
    <mobility:latitude rdf:datatype="http://www.w3.org/2001/XMLSchema#float">{capteur.latitude}</mobility:latitude>
    <mobility:longitude rdf:datatype="http://www.w3.org/2001/XMLSchema#float">{capteur.longitude}</mobility:longitude>
    <mobility:directionMesure rdf:datatype="http://www.w3.org/2001/XMLSchema#string">{escape_xml(capteur.direction_mesure)}</mobility:directionMesure>
    <mobility:statutCapteur rdf:datatype="http://www.w3.org/2001/XMLSchema#string">{escape_xml(capteur.statut)}</mobility:statutCapteur>
    <mobility:frequenceMesure rdf:datatype="http://www.w3.org/2001/XMLSchema#int">{capteur.frequence_mesure}</mobility:frequenceMesure>
    <mobility:precisionDetection rdf:datatype="http://www.w3.org/2001/XMLSchema#float">{capteur.precision_detection}</mobility:precisionDetection>
    <mobility:vitesseMinDetection rdf:datatype="http://www.w3.org/2001/XMLSchema#int">{capteur.vitesse_min_detection}</mobility:vitesseMinDetection>
    <mobility:vitesseMaxDetection rdf:datatype="http://www.w3.org/2001/XMLSchema#int">{capteur.vitesse_max_detection}</mobility:vitesseMaxDetection>
    <mobility:dateInstallation rdf:datatype="http://www.w3.org/2001/XMLSchema#date">{format_date(capteur.date_installation)}</mobility:dateInstallation>
    <mobility:fournisseur rdf:datatype="http://www.w3.org/2001/XMLSchema#string">{escape_xml(capteur.fournisseur or '')}</mobility:fournisseur>
    <mobility:modele rdf:datatype="http://www.w3.org/2001/XMLSchema#string">{escape_xml(capteur.modele or '')}</mobility:modele>
    <mobility:zoneTrafic rdf:datatype="http://www.w3.org/2001/XMLSchema#string">{escape_xml(capteur.zone_trafic.nom)}</mobility:zoneTrafic>
    <mobility:dateCreation rdf:datatype="http://www.w3.org/2001/XMLSchema#dateTime">{format_datetime(capteur.date_creation)}</mobility:dateCreation>
  </rdf:Description>
</rdf:RDF>'''

        # Optimisation: modification in-place du fichier
        # Lire les dernières lignes pour trouver </rdf:RDF>
        with open(RDF_FILE_PATH, 'r+', encoding='utf-8', newline='') as f:
            # Lire tout le fichier
            content = f.read()

            # Vérifier si </rdf:RDF> existe
            if '</rdf:RDF>' in content:
                # Remplacer la ligne de fermeture par le nouveau capteur + fermeture
                content = content.replace('</rdf:RDF>', capteur_rdf)
                logger.debug(f"Remplacement de </rdf:RDF> par le nouveau capteur")
            else:
                # Ajouter à la fin du fichier
                logger.warning("Balise </rdf:RDF> non trouvée, ajout à la fin du fichier")
                content += f'\n{capteur_rdf}\n'

            # Réécrire le fichier
            f.seek(0)
            f.write(content)
            f.truncate()

        logger.info(f"Capteur {capteur.nom} ajouté avec succès au fichier RDF")
        return True

    except Exception as e:
        # Erreur lors de l'ajout du capteur au RDF - LOG DÉTAILLÉ
        logger.error(f"Erreur lors de l'ajout du capteur '{capteur.nom}' au RDF: {str(e)}", exc_info=True)
        return False

def add_capteur_properties_to_rdf():
    """Ajoute les propriétés manquantes pour les capteurs dans le RDF"""
    try:
        # Vérifier si les propriétés existent déjà
        with open(RDF_FILE_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'CapteurTrafic' in content and 'mobility:nomCapteur' in content:
            # Les propriétés existent déjà
            return True
        
        # Si les propriétés n'existent pas, les ajouter
        tree = ET.parse(RDF_FILE_PATH)
        root = tree.getroot()
        
        # Propriétés à ajouter pour les capteurs de trafic
        capteur_properties = [
            {
                'about': 'http://example.org/mobility-ontology/2025/09#nomCapteur',
                'type': 'DatatypeProperty',
                'label': 'nom du capteur',
                'comment': 'Nom ou identifiant du capteur de trafic',
                'domain': 'CapteurTrafic',
                'range': 'string'
            },
            {
                'about': 'http://example.org/mobility-ontology/2025/09#codeCapteur',
                'type': 'DatatypeProperty',
                'label': 'code du capteur',
                'comment': 'Code unique du capteur de trafic',
                'domain': 'CapteurTrafic',
                'range': 'string'
            },
            {
                'about': 'http://example.org/mobility-ontology/2025/09#typeCapteur',
                'type': 'DatatypeProperty',
                'label': 'type de capteur',
                'comment': 'Type de capteur (radar, caméra, boucle magnétique, etc.)',
                'domain': 'CapteurTrafic',
                'range': 'string'
            },
            {
                'about': 'http://example.org/mobility-ontology/2025/09#directionMesure',
                'type': 'DatatypeProperty',
                'label': 'direction de mesure',
                'comment': 'Direction de la voie mesurée par le capteur',
                'domain': 'CapteurTrafic',
                'range': 'string'
            },
            {
                'about': 'http://example.org/mobility-ontology/2025/09#statutCapteur',
                'type': 'DatatypeProperty',
                'label': 'statut du capteur',
                'comment': 'Statut du capteur (actif, inactif, maintenance, défaillant)',
                'domain': 'CapteurTrafic',
                'range': 'string'
            },
            {
                'about': 'http://example.org/mobility-ontology/2025/09#frequenceMesure',
                'type': 'DatatypeProperty',
                'label': 'fréquence de mesure',
                'comment': 'Fréquence de mesure en secondes',
                'domain': 'CapteurTrafic',
                'range': 'int'
            },
            {
                'about': 'http://example.org/mobility-ontology/2025/09#precisionDetection',
                'type': 'DatatypeProperty',
                'label': 'précision de détection',
                'comment': 'Précision de détection en pourcentage',
                'domain': 'CapteurTrafic',
                'range': 'float'
            },
            {
                'about': 'http://example.org/mobility-ontology/2025/09#vitesseMinDetection',
                'type': 'DatatypeProperty',
                'label': 'vitesse minimale détectée',
                'comment': 'Vitesse minimale détectée en km/h',
                'domain': 'CapteurTrafic',
                'range': 'int'
            },
            {
                'about': 'http://example.org/mobility-ontology/2025/09#vitesseMaxDetection',
                'type': 'DatatypeProperty',
                'label': 'vitesse maximale détectée',
                'comment': 'Vitesse maximale détectée en km/h',
                'domain': 'CapteurTrafic',
                'range': 'int'
            },
            {
                'about': 'http://example.org/mobility-ontology/2025/09#dateInstallation',
                'type': 'DatatypeProperty',
                'label': 'date d\'installation',
                'comment': 'Date d\'installation du capteur',
                'domain': 'CapteurTrafic',
                'range': 'date'
            },
            {
                'about': 'http://example.org/mobility-ontology/2025/09#fournisseur',
                'type': 'DatatypeProperty',
                'label': 'fournisseur',
                'comment': 'Fournisseur du capteur',
                'domain': 'CapteurTrafic',
                'range': 'string'
            },
            {
                'about': 'http://example.org/mobility-ontology/2025/09#modele',
                'type': 'DatatypeProperty',
                'label': 'modèle',
                'comment': 'Modèle du capteur',
                'domain': 'CapteurTrafic',
                'range': 'string'
            },
            {
                'about': 'http://example.org/mobility-ontology/2025/09#zoneTrafic',
                'type': 'DatatypeProperty',
                'label': 'zone de trafic',
                'comment': 'Zone de trafic où se trouve le capteur',
                'domain': 'CapteurTrafic',
                'range': 'string'
            },
            {
                'about': 'http://example.org/mobility-ontology/2025/09#dateCreation',
                'type': 'DatatypeProperty',
                'label': 'date de création',
                'comment': 'Date de création de l\'enregistrement',
                'domain': 'CapteurTrafic',
                'range': 'dateTime'
            }
        ]
        
        # Ajouter la classe CapteurTrafic si elle n'existe pas
        capteur_class_exists = False
        for elem in root.findall('.//rdf:Description', {'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'}):
            if elem.get('rdf:about') == 'http://example.org/mobility-ontology/2025/09#CapteurTrafic':
                capteur_class_exists = True
                break
        
        if not capteur_class_exists:
            # Ajouter la classe CapteurTrafic
            capteur_class = ET.Element('rdf:Description')
            capteur_class.set('rdf:about', 'http://example.org/mobility-ontology/2025/09#CapteurTrafic')
            
            type_elem = ET.SubElement(capteur_class, 'rdf:type')
            type_elem.set('rdf:resource', 'http://www.w3.org/2002/07/owl#Class')
            
            label_elem = ET.SubElement(capteur_class, 'rdfs:label')
            label_elem.set('xml:lang', 'fr')
            label_elem.text = 'Capteur de Trafic'
            
            comment_elem = ET.SubElement(capteur_class, 'rdfs:comment')
            comment_elem.set('xml:lang', 'fr')
            comment_elem.text = 'Capteur de surveillance du trafic routier'
            
            root.insert(-1, capteur_class)
        
        # Ajouter les propriétés
        for prop in capteur_properties:
            prop_exists = False
            for elem in root.findall('.//rdf:Description', {'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'}):
                if elem.get('rdf:about') == prop['about']:
                    prop_exists = True
                    break
            
            if not prop_exists:
                prop_elem = ET.Element('rdf:Description')
                prop_elem.set('rdf:about', prop['about'])
                
                type_elem = ET.SubElement(prop_elem, 'rdf:type')
                type_elem.set('rdf:resource', f"http://www.w3.org/2002/07/owl#{prop['type']}")
                
                label_elem = ET.SubElement(prop_elem, 'rdfs:label')
                label_elem.set('xml:lang', 'fr')
                label_elem.text = prop['label']
                
                comment_elem = ET.SubElement(prop_elem, 'rdfs:comment')
                comment_elem.set('xml:lang', 'fr')
                comment_elem.text = prop['comment']
                
                domain_elem = ET.SubElement(prop_elem, 'rdfs:domain')
                domain_elem.set('rdf:resource', f"http://example.org/mobility-ontology/2025/09#{prop['domain']}")
                
                range_elem = ET.SubElement(prop_elem, 'rdfs:range')
                range_elem.set('rdf:resource', f"http://www.w3.org/2001/XMLSchema#{prop['range']}")
                
                root.insert(-1, prop_elem)
        
        # Sauvegarder le fichier
        tree.write(RDF_FILE_PATH, encoding='utf-8', xml_declaration=True)
        print("✅ Propriétés des capteurs ajoutées au fichier RDF")
        return True
        
    except Exception as e:
        # Erreur lors de l'ajout des proprietes au RDF
        return False

@receiver(post_save, sender=CapteurTrafic)
def capteur_created_handler(sender, instance, created, **kwargs):
    """Signal handler appele lorsqu'un capteur est cree"""
    # Debug: log the signal trigger
    import logging
    logger = logging.getLogger(__name__)
    
    if created:
        logger.info(f"Nouveau capteur cree : {instance.nom} (ID: {instance.id})")
        
        # Les proprietes existent deja dans le fichier RDF, on ne les ajoute pas
        # add_capteur_properties_to_rdf()  # Desactive pour eviter l'erreur
        
        # Ajouter le capteur au fichier RDF
        success = add_capteur_to_rdf(instance)
        
        if success:
            logger.info(f"Capteur '{instance.nom}' integre avec succes dans le fichier RDF")
        else:
            logger.error(f"Echec de l'integration du capteur '{instance.nom}' dans le fichier RDF")
    else:
        # Update, not creation
        logger.debug(f"Capteur modifie : {instance.nom} (ID: {instance.id})")

def sync_existing_capteurs_to_rdf():
    """Synchronise tous les capteurs existants avec le fichier RDF"""
    print("🔄 Synchronisation des capteurs existants avec le fichier RDF...")
    
    # Ajouter les propriétés d'abord
    add_capteur_properties_to_rdf()
    
    # Ajouter tous les capteurs existants
    capteurs = CapteurTrafic.objects.all()
    added_count = 0
    
    for capteur in capteurs:
        try:
            # Vérifier si le capteur existe déjà dans le RDF
            with open(RDF_FILE_PATH, 'r', encoding='utf-8') as f:
                content = f.read()
            
            capteur_id = generate_capteur_rdf_id(capteur)
            exists = f'http://example.org/mobility-ontology/2025/09#{capteur_id}' in content
            
            if not exists:
                success = add_capteur_to_rdf(capteur)
                if success:
                    added_count += 1
                    
        except Exception as e:
            print(f"❌ Erreur pour le capteur {capteur.nom}: {str(e)}")
    
    print(f"✅ Synchronisation terminée : {added_count} nouveaux capteurs ajoutés au RDF")
    return added_count
