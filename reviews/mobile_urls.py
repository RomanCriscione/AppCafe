from django.urls import path

from .mobile_api import MyMapAPIView

urlpatterns = [
    path(
        "my-map/",
        MyMapAPIView.as_view(),
        name="mobile-my-map",
    ),
]