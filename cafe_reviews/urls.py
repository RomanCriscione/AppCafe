from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.generic import TemplateView, RedirectView

from django.contrib.sitemaps.views import sitemap
from cafe_reviews.sitemaps import sitemaps   # usa el registro que ya corregimos

from rest_framework.routers import DefaultRouter
from reviews.api import CafeViewSet

router = DefaultRouter()
router.register(r"cafes", CafeViewSet, basename="cafe")

urlpatterns = [
    path("admin/", admin.site.urls),

    # Auth (allauth)
    path("accounts/", include("allauth.urls")),

    # Users
    path("users/", include("accounts.urls")),

    # Público – páginas estáticas y home
    path("", include("core.urls")),

    # Cafés (HTML)
    path("reviews/", include("reviews.urls")),   # el namespace ya viene del archivo reviews/urls.py

    # API REST
    path("api/", include(router.urls)),

    # robots.txt
    path(
        "robots.txt",
        TemplateView.as_view(
            template_name="core/robots.txt",
            content_type="text/plain"
        ),
        name="robots_txt",
    ),

    # sitemap
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="django_sitemap"),

    # favicon
    path(
        "favicon.ico",
        RedirectView.as_view(
            url="/static/images/coffee-icon.png",
            permanent=False
        ),
        name="favicon",
    ),

    # --- Verificación Google (archivo en raíz) ---
    path(
        "google157d26ef7e3007f2.html",
        TemplateView.as_view(
            template_name="google157d26ef7e3007f2.html",
            content_type="text/plain"
        ),
        name="google_verify",
    ),
]

# Servir MEDIA en producción
urlpatterns += [
    re_path(r"^media/(?P<path>.*)$", RedirectView.as_view(url="/static/")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
