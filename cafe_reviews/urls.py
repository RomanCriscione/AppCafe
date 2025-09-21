from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.contrib.sitemaps.views import sitemap
from cafe_reviews.sitemaps import sitemaps

urlpatterns = [
    path("admin/", admin.site.urls),

    # --- Autenticación (allauth) ---
    path("accounts/", include("allauth.urls")),

    # --- Usuarios (vistas propias) ---
    path("users/", include("accounts.urls")),

    # --- Público (home, about, contact, etc.) ---
    path("", include("core.urls")),

    # --- Cafeterías y reseñas ---
    path("reviews/", include(("reviews.urls", "reviews"), namespace="reviews")),

    # robots.txt (template plano)
    path(
        "robots.txt",
        TemplateView.as_view(template_name="core/robots.txt", content_type="text/plain"),
        name="robots_txt",
    ),

    # Sitemap (framework de Django)
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="django_sitemap"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
