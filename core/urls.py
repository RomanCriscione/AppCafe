from django.urls import path
from . import views
from reviews.views import review_list


urlpatterns = [
    path('', review_list, name='home'),
    ]
