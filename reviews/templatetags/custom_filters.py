# reviews/templatetags/custom_filters.py
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

# ===== Etiquetas en español (features booleanas) =====
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

# ===== Emojis para etiquetas sensoriales/ambiente/hacer/estética/emocional =====

_EMOJI_BY_NAME = {
    # sensorial
    "Huele a café recién molido": "☕️",
    "Suena bossa nova de fondo": "🎶",
    "Pan casero y café en taza pesada": "🍞☕️",
    "Tiene aroma a madera y lluvia": "🌧️🌲",
    "Tostadas como las de tu abuela": "🍞💖",
    "El espresso que necesitabas": "⚡️☕️",
    "Café fuerte, pero amable": "💪☕️",
    "Tiene música, pero no grita": "🎵🤫",
    "Las tazas te abrazan": "☕️🫶",
    "El café llega caliente, siempre": "🔥☕️",

    # ambiente
    "Te saludan por tu nombre": "🙋‍♀️🙋‍♂️",
    "El mozo ya sabe tu pedido": "📝☕️",
    "Siempre hay alguien leyendo": "📖",
    "Ideal para charla de sobremesa": "🗣️🍰",
    "Te podés quedar sin pedir nada más": "🛋️",
    "Vas una vez y ya te saludan como si nada": "😊🤝",
    "Mesas cerquita, como para conversar bajito": "🤫🪑",
    "Te sentís en casa, pero sin tener que lavar": "🏠✨",
    "Si vas seguido, te guardan tu mesa": "🪑🔖",
    "Podés ir solo sin sentirte solo": "🧍‍♂️🤍",

    # hacer
    "Ideal para escribir un cuento": "✍️",
    "Tiene enchufes donde los necesitás": "🔌",
    "Silencio sin incomodidad": "🤫🙂",
    "Para leer sin mirar el reloj": "📚⏳",
    "Buena conexión, pero te da ganas de desconectarte": "📶🧘",
    "Las sillas no te arruinan la espalda": "🪑✅",
    "Se puede estudiar sin culpa": "📖🧠",
    "Para planear cosas que todavía no contaste": "📝💭",
    "Cafecito y to-do list": "☕️✅",
    "La playlist ayuda a concentrarse": "🎧🧠",

    # estetica
    "Tiene plantas que no son de plástico": "🪴",
    "Ventanales con luz todo el día": "🪟☀️",
    "Parece París, pero está a 5 cuadras": "🗼",
    "Manteles distintos en cada mesa": "🧵🧺",
    "Huele a librería vieja y pan": "📚🍞",
    "Paredes con historias (y fotos de verdad)": "🖼️",
    "Cada taza es distinta, como debe ser": "☕️✨",
    "Te dan la contraseña del WiFi sin pedirla": "🔑📶",
    "Baños cuidados (y eso dice mucho)": "🚻🧼",
    "Hay un gato que manda": "🐈👑",

    # emocional
    "Para cuando no sabés qué hacer": "🤷‍♀️☕️",
    "Ideal para una primera cita sin presión": "💘",
    "Buen lugar para esperar sin ansiedad": "🧘⏳",
    "Donde podés no hablar por un rato": "🤫",
    "De esos que ordenan el día": "📅",
    "Para días grises (o con sol tímido)": "🌦️",
    "Cuando necesitás que algo salga bien": "🍀",
    "De los que se quedan con vos": "💫",
    "Un buen lugar para no decidir nada": "😌",
    "Te vas y te dan ganas de volver": "🔁",
}

_FALLBACK_BY_CATEGORY = {
    "sensorial": "☕️",
    "ambiente": "🤝",
    "hacer": "✍️",
    "estetica": "🪴",
    "emocional": "💫",
}

@register.filter
def tag_emoji(tag):
    """
    Devuelve un emoji para un Tag. Acepta instancia Tag o dict (de values()).
    - Si el nombre coincide exactamente con _EMOJI_BY_NAME, usa ese.
    - Si no, intenta fallback por categoría (_FALLBACK_BY_CATEGORY).
    - Si nada coincide, devuelve un emoji genérico.
    """
    name = None
    category = None

    # Soporta tanto objetos como dicts
    if isinstance(tag, dict):
        name = tag.get("name") or tag.get("tags__name")
        category = tag.get("category") or tag.get("tags__category")
    else:
        name = getattr(tag, "name", None) or (str(tag) if tag is not None else None)
        category = getattr(tag, "category", None)

    if name in _EMOJI_BY_NAME:
        return _EMOJI_BY_NAME[name]
    if category in _FALLBACK_BY_CATEGORY:
        return _FALLBACK_BY_CATEGORY[category]
    return "🏷️"
