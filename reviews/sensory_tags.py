SENSORY_REVIEW_TAG_GROUPS = {
    "conexion": [
        "Podés ir solo sin sentirte solo",
        "Ideal para charla de sobremesa",
        "Ideal para una primera cita sin presión",
    ],
    "refugio": [
        "Buen lugar para esperar sin ansiedad",
        "Te dan ganas de desconectarte",
        "Te vas y te dan ganas de volver",
        "Pedirías otra taza solo para quedarte",
    ],
    "ritual": [
        "Huele a café recién molido",
        "Pan casero y café en taza pesada",
        "Ventanales con luz todo el día",
    ],
    "inspiracion": [
        "Ideal para escribir o leer un cuento",
        "Paredes con historias",
    ],
}


SENSORY_REVIEW_TAG_NAMES = {
    name
    for names in SENSORY_REVIEW_TAG_GROUPS.values()
    for name in names
}