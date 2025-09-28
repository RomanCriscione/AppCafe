# core/validators.py
from django.core.exceptions import ValidationError
from .disposable import DOMAINS  # set() de dominios desechables
def validate_not_disposable(email):
    dom = email.split("@")[-1].lower()
    if dom in DOMAINS:
        raise ValidationError("Ese dominio de email no está permitido.")
