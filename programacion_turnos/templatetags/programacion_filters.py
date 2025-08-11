from django import template

register = template.Library()

@register.filter
def get(dictionary, key):
    """
    Gets an item from a dictionary using a key.
    """
    return dictionary.get(key)