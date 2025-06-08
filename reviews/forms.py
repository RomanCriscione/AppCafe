from django import forms
from .models import Review, Cafe  

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']

class CafeForm(forms.ModelForm):
    class Meta:
        model = Cafe
        fields = ['name', 'address', 'location', 'description', 'phone', 'photo1', 'photo2', 'photo3']
