from django.urls import path
from .mobile_api import (
    CafeDetailAPIView,
    MeAPIView,
    MyMapAPIView,
    SetCafeStatusAPIView,
    SetCafeCollectionAPIView,
)
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

    path(
        "cafes/<int:cafe_id>/",
        CafeDetailAPIView.as_view(),
        name="mobile-cafe-detail",
    ),

    path(
        "cafes/<int:cafe_id>/set-status/",
        SetCafeStatusAPIView.as_view(),
        name="mobile-set-cafe-status",
    ),
    path(
        "cafes/<int:cafe_id>/set-collection/",
        SetCafeCollectionAPIView.as_view(),
        name="mobile-set-cafe-collection",
    ),
]