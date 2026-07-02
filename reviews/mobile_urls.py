from django.urls import path
from .mobile_api import MeAPIView

from .mobile_api import MyMapAPIView
from .auth_api import (
    MobileLoginAPIView,
    MobileRegisterAPIView,
    MobileLogoutAPIView,
)



urlpatterns = [
    path(
        "my-map/",
        MyMapAPIView.as_view(),
        name="mobile-my-map",
    ),

    path(
        "me/",
        MeAPIView.as_view(),
        name="mobile-me",
    ),

    path(
        "login/",
        MobileLoginAPIView.as_view(),
        name="mobile-login",
    ),

    path(
        "register/",
        MobileRegisterAPIView.as_view(),
        name="mobile-register",
    ),

    path(
        "logout/",
        MobileLogoutAPIView.as_view(),
        name="mobile-logout",
    ),
]