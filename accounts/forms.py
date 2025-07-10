from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser
from allauth.account.forms import SignupForm


# Formulario personalizado para el registro desde el admin
class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('email', 'username', 'first_name', 'last_name', 'avatar')


# Formulario personalizado para el registro con django-allauth
class CustomSignupForm(SignupForm):
    first_name = forms.CharField(max_length=30, label="Nombre", required=True)

    def save(self, request):
        user = super().save(request)
        user.first_name = self.cleaned_data['first_name']
        user.save()
        return user

# Formulario para modificar el avatar del usuario

class CustomUserChangeForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'avatar']