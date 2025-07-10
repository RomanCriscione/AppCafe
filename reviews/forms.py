from django import forms
from .models import Review, Cafe
from django.core.exceptions import ValidationError
import re

# Validación externa por si se quiere también usar en el modelo
def validar_phone(valor):
    if valor and not re.match(r'^\+?\d{6,15}$', valor):
        raise ValidationError("Número inválido. Usá solo números, con o sin +, de 6 a 15 dígitos.")

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']

class CafeForm(forms.ModelForm):
    phone = forms.CharField(
        max_length=20,
        required=False,
        help_text='Ejemplo: +541155112233 o 01155556666',
        widget=forms.TextInput(attrs={'placeholder': '+541155112233 o 01155556666'})
    )

    class Meta:
        model = Cafe
        fields = [
            'name', 'address', 'location', 'description', 'phone', 'google_maps_url',
            'photo1', 'photo1_title',
            'photo2', 'photo2_title',
            'photo3', 'photo3_title',
            'is_vegan_friendly', 'is_pet_friendly', 'has_wifi', 'has_outdoor_seating',
            'has_parking', 'is_accessible', 'has_vegetarian_options',
            'serves_breakfast', 'serves_alcohol',
            'has_books_or_games', 'has_air_conditioning',
            'has_gluten_free', 'has_specialty_coffee', 'has_artisanal_pastries',
            'tags', 'latitude', 'longitude',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'google_maps_url': forms.URLInput(attrs={'placeholder': 'https://maps.google.com/...'}),
            'photo1_title': forms.TextInput(attrs={'placeholder': 'Título de la foto 1'}),
            'photo2_title': forms.TextInput(attrs={'placeholder': 'Título de la foto 2'}),
            'photo3_title': forms.TextInput(attrs={'placeholder': 'Título de la foto 3'}),
            'tags': forms.CheckboxSelectMultiple(),
            'photo1': forms.ClearableFileInput(attrs={'accept': 'image/jpeg,image/png'}),
            'photo2': forms.ClearableFileInput(attrs={'accept': 'image/jpeg,image/png'}),
            'photo3': forms.ClearableFileInput(attrs={'accept': 'image/jpeg,image/png'}),
        }
        help_texts = {
            'photo1': 'Máximo 3MB. Formatos aceptados: JPG o PNG.',
            'photo2': 'Máximo 3MB. Formatos aceptados: JPG o PNG.',
            'photo3': 'Máximo 3MB. Formatos aceptados: JPG o PNG.',
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
