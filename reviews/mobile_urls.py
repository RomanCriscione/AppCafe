from django.urls import path

from .mobile_api import MyMapAPIView
from .auth_api import MobileLoginAPIView

urlpatterns = [
    path(
        "my-map/",
        MyMapAPIView.as_view(),
        name="mobile-my-map",
    ),

    path(
        "login/",
        MobileLoginAPIView.as_view(),
        name="mobile-login",
    ),
]