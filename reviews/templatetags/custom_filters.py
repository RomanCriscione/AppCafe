from django import template
register = template.Library()

@register.filter
def get_item(dictionary, key):
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    # También permite acceder a atributos de un objeto (modelo)
    return getattr(dictionary, key, None)

@register.filter
def replace(value, arg):
    try:
        old, new = arg.split('|', 1)
        return str(value).replace(old, new)
    except Exception:
        return value

# ===== Etiquetas en español =====
@register.filter
def feature_label(key: str) -> str:
    labels = {
        "has_wifi": "Wi-Fi disponible",
        "has_air_conditioning": "Aire acondicionado",
        "serves_alcohol": "Sirve alcohol",
        "is_pet_friendly": "Apto mascotas",
        "is_vegan_friendly": "Opciones veganas",
        "has_outdoor_seating": "Mesas al aire libre",
        "has_parking": "Estacionamiento",
        "is_accessible": "Accesible s/ ruedas",
        "has_vegetarian_options": "Opciones vegetarianas",
        "has_books_or_games": "Libros / juegos",
        "serves_breakfast": "Desayuno",

        # ➕ Nuevas
        "accepts_cards": "Acepta tarjetas",
        "gluten_free_options": "Opciones sin gluten",
        "has_baby_changing": "Cambiador para bebés",
        "has_power_outlets": "Enchufes disponibles",
        "laptop_friendly": "Apto para trabajar",
        "quiet_space": "Espacio tranquilo",
        "specialty_coffee": "Café de especialidad",
        "brunch": "Brunch",
        "accepts_reservations": "Acepta reservas",
    }
    return labels.get(key, key.replace("_", " ").capitalize())

# (Opcional) un emoji simpático por feature
@register.filter
def feature_emoji(key: str) -> str:
    emojis = {
        "has_wifi": "📶",
        "has_air_conditioning": "❄️",
        "serves_alcohol": "🍷",
        "is_pet_friendly": "🐾",
        "is_vegan_friendly": "🌿",
        "has_outdoor_seating": "☀️",
        "has_parking": "🅿️",
        "is_accessible": "♿",
        "has_vegetarian_options": "🥗",
        "has_books_or_games": "📚",
        "serves_breakfast": "🍳",

        "accepts_cards": "💳",
        "gluten_free_options": "🌾❌",
        "has_baby_changing": "👶",
        "has_power_outlets": "🔌",
        "laptop_friendly": "💻",
        "quiet_space": "🤫",
        "specialty_coffee": "☕️⭐",
        "brunch": "🥞",
        "accepts_reservations": "📅",
    }
    return emojis.get(key, "")
