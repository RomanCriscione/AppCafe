from django import forms
from .models import Review, Cafe  

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']

class CafeForm(forms.ModelForm):
    class Meta:
        model = Cafe
        fields = [
            'name',
            'address',
            'location',
            'description',
            'phone',
            'google_maps_url',
            'photo1', 'photo1_title',
            'photo2', 'photo2_title',
            'photo3', 'photo3_title',
            'is_vegan_friendly',
            'is_pet_friendly',
            'has_wifi',
            'has_outdoor_seating',
            'tags',
            'latitude', 'longitude',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'google_maps_url': forms.URLInput(attrs={'placeholder': 'https://maps.google.com/...'}),
            'photo1_title': forms.TextInput(attrs={'placeholder': 'Título de la foto 1'}),
            'photo2_title': forms.TextInput(attrs={'placeholder': 'Título de la foto 2'}),
            'photo3_title': forms.TextInput(attrs={'placeholder': 'Título de la foto 3'}),
            'tags': forms.CheckboxSelectMultiple(),
        }
    def clean(self):
        cleaned_data = super().clean()
        max_size = 3 * 1024 * 1024  # 3MB en bytes

        for campo in ['photo1', 'photo2', 'photo3']:
            imagen = self.files.get(campo)
            if imagen and imagen.size > max_size:
                self.add_error(campo, "La imagen no puede superar los 3MB.")

        return cleaned_data