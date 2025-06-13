from django.urls import path
from . import views
from reviews.views import review_list
from core.views import about_view, contact_view


urlpatterns = [
    path('', review_list, name='home'),
    path('about/', about_view, name='about'),
    path("contact/", contact_view, name="contact"),
    ]
