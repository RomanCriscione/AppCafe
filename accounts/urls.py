from django.urls import path
from .views import register, edit_avatar

urlpatterns = [
    path('register/', register, name='register'),
    path('edit-avatar/', edit_avatar, name='edit_avatar'),
]
