"""
Filtres personnalisés pour les templates SmartCity
"""

from django import template

register = template.Library()

@register.filter
def split(value, delimiter):
    """Divise une chaîne selon un délimiteur"""
    if value:
        return str(value).split(delimiter)
    return []

@register.filter
def last(value):
    """Récupère le dernier élément d'une liste"""
    if value and isinstance(value, (list, tuple)):
        return value[-1]
    return value

@register.filter
def extract_name(value):
    """Extrait le nom d'une URI RDF (après # ou dernier /)"""
    if not value:
        return value
    
    value_str = str(value)
    
    # Essayer de diviser par #
    if '#' in value_str:
        return value_str.split('#')[-1]
    
    # Sinon diviser par /
    if '/' in value_str:
        return value_str.split('/')[-1]
    
    return value_str