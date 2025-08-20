from django import template

register = template.Library()
from django import template

register = template.Library()

@register.filter
def dict_get(dictionary, key):
    """Obtiene un valor del diccionario usando una clave"""
    if isinstance(dictionary, dict):
        result = dictionary.get(key, '')
        return result
    return ''