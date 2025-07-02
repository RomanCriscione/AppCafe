from django.urls import path
from core.views import about_view, contact_view, home

urlpatterns = [
    path('', home, name='home'),
    path('about/', about_view, name='about'),
    path("contact/", contact_view, name="contact"),
]
