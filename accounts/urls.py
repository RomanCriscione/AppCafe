from django.urls import path
from .views import register, edit_avatar, profile, register_owner

urlpatterns = [
    path('register/', register, name='register'),
    path('edit-avatar/', edit_avatar, name='edit_avatar'),
    path('profile/', profile, name='profile'),
    path('register/owner/', register_owner, name='register_owner'),
]
