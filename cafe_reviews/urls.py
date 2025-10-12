# cafe_reviews/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView, RedirectView
from django.contrib.sitemaps.views import sitemap
from cafe_reviews.sitemaps import sitemaps

from django.templatetags.static import static as static_url  # para URL de static
from rest_framework.routers import DefaultRouter
from reviews.api import CafeViewSet

router = DefaultRouter()
router.register(r"cafes", CafeViewSet, basename="cafe")

urlpatterns = [
    path("admin/", admin.site.urls),

    # --- Autenticación (allauth) ---
    path("accounts/", include("allauth.urls")),

    # --- Usuarios (vistas propias) ---
    path("users/", include("accounts.urls")),

    # --- Público (home, about, contact, etc.) ---
    path("", include("core.urls")),

    # --- Cafeterías y reseñas (HTML) ---
    path("reviews/", include(("reviews.urls", "reviews"), namespace="reviews")),

    # --- API (JSON) ---
    path("api/", include(router.urls)),

    # robots.txt
    path(
        "robots.txt",
        TemplateView.as_view(template_name="core/robots.txt", content_type="text/plain"),
        name="robots_txt",
    ),

    # Sitemap
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="django_sitemap"),

    # Favicon (apunta a un archivo que existe en /static/images/)
    path(
        "favicon.ico",
        RedirectView.as_view(url=static_url("images/coffee-icon.png"), permanent=False),
        name="favicon",
    ),
]

# ⚠️ Provisorio: servir MEDIA también en producción (Render) hasta moverlo a disco/bucket
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
