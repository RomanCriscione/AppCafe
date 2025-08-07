from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def replace(value, arg):
    """
    Reemplaza una subcadena por otra.
    Uso: {{ value|replace:"_| " }} → reemplaza guión bajo por espacio
    """
    try:
        old, new = arg.split('|')
        return value.replace(old, new)
    except ValueError:
        return value
