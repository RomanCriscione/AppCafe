from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

from core.views import sitemap_xml

urlpatterns = [
    path("admin/", admin.site.urls),

    # Auth (django-allauth)
    path("accounts/", include("allauth.urls")),

    # Acciones personalizadas de usuarios
    path("users/", include("accounts.urls")),

    # Vistas públicas (home, about, contact, etc.)
    path("", include("core.urls")),

    # Cafeterías y reseñas
    path("reviews/", include("reviews.urls")),

    # robots.txt (estático)
    path(
        "robots.txt",
        TemplateView.as_view(
            template_name="core/robots.txt",
            content_type="text/plain",
        ),
        name="robots_txt",
    ),

    # sitemap.xml (dinámico) — única ruta
    path("sitemap.xml", sitemap_xml, name="sitemap_xml"),
]

# Archivos MEDIA en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
