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
            'photo1',
            'photo2',
            'photo3',
            'is_vegan_friendly',
            'is_pet_friendly',
            'has_wifi',
            'has_outdoor_seating',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'google_maps_url': forms.URLInput(attrs={'placeholder': 'https://maps.google.com/...'}),
        }
