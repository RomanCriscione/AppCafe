# reviews/templatetags/tag_icons.py
from django import template

register = template.Library()

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
    name = None
    category = None

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
