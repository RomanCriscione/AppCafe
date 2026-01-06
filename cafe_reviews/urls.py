from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.generic import RedirectView, TemplateView

from django.contrib.sitemaps.views import sitemap
from cafe_reviews.sitemaps import sitemaps

from rest_framework.routers import DefaultRouter
from reviews.api import CafeViewSet

# Router API
router = DefaultRouter()
router.register(r"cafes", CafeViewSet, basename="cafe")

urlpatterns = [
    path("admin/", admin.site.urls),

    # Autenticación Allauth
    path("accounts/", include("allauth.urls")),

    # Rutas de usuarios
    path("users/", include("accounts.urls")),

    # Público – páginas estáticas
    path("", include("core.urls")),

    # Cafés HTML
    path("reviews/", include("reviews.urls")),

    # API REST
    path("api/", include(router.urls)),

    # robots.txt
    path(
        "robots.txt",
        TemplateView.as_view(
            template_name="core/robots.txt",
            content_type="text/plain",
        ),
        name="robots_txt",
    ),

    # sitemap
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": sitemaps},
        name="django_sitemap",
    ),

    # favicon
    path(
        "favicon.ico",
        RedirectView.as_view(
            url="/static/images/coffee-icon.png",
            permanent=False,
        ),
        name="favicon",
    ),

    # --- VERIFICACIÓN GOOGLE – SERVIR COMO ESTÁTICO ---
    path(
        "google157d26ef7e3007f2.html",
        RedirectView.as_view(
            url="/static/google157d26ef7e3007f2.html",
            permanent=False,
        ),
        name="google_verify",
    ),
]

# MEDIA en Render
urlpatterns += [
    re_path(
        r"^media/(?P<path>.*)$",
        django.views.static.serve,
        {"document_root": settings.MEDIA_ROOT},
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
