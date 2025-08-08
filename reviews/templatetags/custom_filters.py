from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None

@register.filter
def replace(value, arg):
    """
    Uso: {{ texto|replace:"old|new" }}
    Ej: {{ "has_wifi"|replace:"_| " }} -> "has wifi"
    """
    try:
        old, new = arg.split('|', 1)
        return str(value).replace(old, new)
    except Exception:
        return value
