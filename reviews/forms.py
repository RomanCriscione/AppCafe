# reviews/forms.py
from __future__ import annotations
import re
from django import forms
from django.core.exceptions import ValidationError
from .models import Review, Cafe, Tag
# Formularios de reclamo: dependen de tu archivo reviews/claims.py
from .claims import (
    ClaimRequest,
    ClaimEvidence,
    ClaimMethod,  # p.ej.: EMAIL_DOMAIN, PHOTO_CODE, PHONE
)

# --------------------------------------------------------------------------------------
# Helpers / Validaciones compartidas
# --------------------------------------------------------------------------------------
def validar_phone(valor):
    """
    Validación externa por si también querés usarla en modelos.
    Acepta números con o sin +, de 6 a 15 dígitos.
    """
    if valor and not re.match(r'^\+?\d{6,15}$', valor):
        raise ValidationError("Número inválido. Usá solo números, con o sin +, de 6 a 15 dígitos.")


# --------------------------------------------------------------------------------------
# Reviews
# --------------------------------------------------------------------------------------
class ReviewForm(forms.ModelForm):
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all().order_by('category', 'name'),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'mb-2'}),
        required=False,
        label="¿Cómo describirías tu experiencia?",
    )
    comment = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full mt-1 p-2 border rounded',
            'rows': 3
        })
    )

    class Meta:
        model = Review
        fields = ['rating', 'comment', 'tags']


# --------------------------------------------------------------------------------------
# Cafés (form del dueño / admin simple)
# --------------------------------------------------------------------------------------
class CafeForm(forms.ModelForm):
    phone = forms.CharField(
        max_length=20,
        required=False,
        help_text='Ejemplo: +541155112233 o 01155556666',
        widget=forms.TextInput(attrs={'placeholder': '+541155112233 o 01155556666'})
    )

    class Meta:
        model = Cafe
        # ✅ SIN 'tags' (las etiquetas sensoriales se eligen en las reviews)
        fields = [
            'name', 'address', 'location', 'description',
            'phone', 'email',
            'google_maps_url',
            'photo1', 'photo1_title',
            'photo2', 'photo2_title',
            'photo3', 'photo3_title',
            'is_vegan_friendly', 'is_pet_friendly', 'has_wifi', 'has_outdoor_seating',
            'has_parking', 'is_accessible', 'has_vegetarian_options',
            'serves_breakfast', 'serves_alcohol',
            'has_books_or_games', 'has_air_conditioning',
            'has_gluten_free', 'has_specialty_coffee', 'has_artisanal_pastries',
            'accepts_cards', 'gluten_free_options', 'has_baby_changing',
            'has_power_outlets', 'laptop_friendly', 'quiet_space',
            'specialty_coffee', 'brunch', 'accepts_reservations',
            'latitude', 'longitude',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'google_maps_url': forms.URLInput(attrs={'placeholder': 'https://maps.google.com/...'}),
            'email': forms.EmailInput(attrs={'placeholder': 'dueño@tucafe.com'}),
            'photo1_title': forms.TextInput(attrs={'placeholder': 'Título de la foto 1'}),
            'photo2_title': forms.TextInput(attrs={'placeholder': 'Título de la foto 2'}),
            'photo3_title': forms.TextInput(attrs={'placeholder': 'Título de la foto 3'}),
            'photo1': forms.ClearableFileInput(attrs={'accept': 'image/jpeg,image/png'}),
            'photo2': forms.ClearableFileInput(attrs={'accept': 'image/jpeg,image/png'}),
            'photo3': forms.ClearableFileInput(attrs={'accept': 'image/jpeg,image/png'}),
        }
        help_texts = {
            'photo1': 'Máximo 3MB. Formatos aceptados: JPG o PNG.',
            'photo2': 'Máximo 3MB. Formatos aceptados: JPG o PNG.',
            'photo3': 'Máximo 3MB. Formatos aceptados: JPG o PNG.',
        }
        labels = {
            'has_wifi': 'Wi-Fi',
            'is_pet_friendly': 'Pet friendly',
            'is_vegan_friendly': 'Vegano friendly',
            'has_outdoor_seating': 'Mesas afuera',
            'has_parking': 'Estacionamiento',
            'is_accessible': 'Accesible',
            'has_vegetarian_options': 'Opción vegetariana',
            'serves_breakfast': 'Desayuno',
            'serves_alcohol': 'Bebidas alcohólicas',
            'has_books_or_games': 'Juegos o libros',
            'has_air_conditioning': 'Aire acondicionado',
            'has_gluten_free': 'Sin TACC',
            'has_specialty_coffee': 'Café de especialidad',
            'has_artisanal_pastries': 'Pastelería artesanal',
        }

    def clean_address(self):
        address = self.cleaned_data.get('address')
        if not address or len(address) < 5:
            raise forms.ValidationError("La dirección debe tener al menos 5 caracteres.")
        if not any(char.isdigit() for char in address):
            raise forms.ValidationError("La dirección debe incluir un número.")
        if not any(char.isalpha() for char in address):
            raise forms.ValidationError("La dirección debe incluir un nombre de calle.")
        return address

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone and not re.match(r'^\+?\d{6,15}$', phone):
            raise forms.ValidationError("Número inválido. Usá solo números, con o sin +, de 6 a 15 dígitos.")
        return phone

    def clean(self):
        cleaned_data = super().clean()
        max_size = 3 * 1024 * 1024  # 3MB
        for campo in ['photo1', 'photo2', 'photo3']:
            imagen = self.files.get(campo)
            if imagen and imagen.size > max_size:
                self.add_error(campo, "La imagen no puede superar los 3MB.")
        return cleaned_data


# --------------------------------------------------------------------------------------
# CLAIMS (reclamo de ficha)
# --------------------------------------------------------------------------------------
class ClaimStartForm(forms.ModelForm):
    """
    Primer paso: elegir método de verificación.
    Filtra choices según datos del café (p.ej. si no hay email, oculta EMAIL_DOMAIN).
    """
    method = forms.ChoiceField(
        choices=ClaimMethod.choices,
        widget=forms.RadioSelect,
        label="¿Cómo querés verificar la titularidad?",
    )

    class Meta:
        model = ClaimRequest
        fields = ["method"]

    def __init__(self, *args, cafe: Cafe | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.cafe = cafe

        # Filtrar choices dinámicamente
        choices = list(ClaimMethod.choices)

        # Si el café no tiene email corporativo configurado, ocultamos EMAIL_DOMAIN
        if not getattr(self.cafe, "email", None):
            choices = [c for c in choices if c[0] != ClaimMethod.EMAIL_DOMAIN]

        # (Opcional) si no querés ofrecer PHONE todavía, lo removés:
        # choices = [c for c in choices if c[0] != ClaimMethod.PHONE]

        self.fields["method"].choices = choices

    def clean(self):
        cleaned = super().clean()
        method = cleaned.get("method")

        if method == ClaimMethod.EMAIL_DOMAIN and not getattr(self.cafe, "email", None):
            raise ValidationError("Este local no tiene email configurado para verificación por dominio.")
        return cleaned


class ClaimVerifyEmailForm(forms.Form):
    """
    Paso para ingresar el código recibido por email.
    """
    code = forms.CharField(
        max_length=12,
        strip=True,
        label="Código recibido",
        widget=forms.TextInput(attrs={
            "placeholder": "Ingresá el código",
            "autocomplete": "one-time-code",
        }),
    )

    def clean_code(self):
        code = self.cleaned_data["code"].strip()
        # Si tus códigos son numéricos de 6 dígitos, validá así:
        # if not re.fullmatch(r"\d{6}", code):
        #     raise ValidationError("El código debe tener 6 números.")
        return code


class MultiFileInput(forms.ClearableFileInput):
    """
    Widget para permitir subir múltiples archivos.
    """
    allow_multiple_selected = True


class ClaimEvidenceForm(forms.Form):
    """
    Subida de evidencias (fotos + PDF). Permitimos múltiples archivos.
    """
    files = forms.FileField(
        label="Evidencias (fotos o PDF)",
        widget=MultiFileInput(attrs={"accept": "image/*,.pdf", "multiple": True}),
    )

    MAX_FILES = 5
    MAX_SIZE_MB = 8
    ALLOWED_CONTENT_TYPES = {
        "image/jpeg",
        "image/png",
        "image/webp",
        "application/pdf",
    }

    def clean_files(self):
        # Si el request usa FILES con múltiples archivos:
        files = []
        if hasattr(self.files, "getlist"):
            files = self.files.getlist("files")
        # Fallback por si viniera 1 solo:
        if not files and "files" in self.cleaned_data:
            files = [self.cleaned_data["files"]]

        if not files:
            raise ValidationError("Subí al menos un archivo.")

        if len(files) > self.MAX_FILES:
            raise ValidationError(f"Podés subir hasta {self.MAX_FILES} archivos.")

        for f in files:
            ctype = getattr(f, "content_type", None)
            if ctype not in self.ALLOWED_CONTENT_TYPES:
                raise ValidationError("Solo se permiten imágenes (JPG/PNG/WEBP) o PDF.")

            size_mb = f.size / (1024 * 1024)
            if size_mb > self.MAX_SIZE_MB:
                raise ValidationError(f"Cada archivo debe pesar menos de {self.MAX_SIZE_MB} MB.")

        return files
