from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.urls import static
from django.views.generic import TemplateView, RedirectView
from django.contrib.sitemaps.views import sitemap

from cafe_reviews.sitemaps import sitemaps
from rest_framework.routers import DefaultRouter
from reviews.api import CafeViewSet

router = DefaultRouter()
router.register(r"cafes", CafeViewSet, basename="cafe")

urlpatterns = [
    path("admin/", admin.site.urls),

    # Allauth
    path("accounts/", include("allauth.urls")),

    # Rutas de usuarios
    path("users/", include("accounts.urls")),

    # Páginas públicas
    path("", include("core.urls")),

    # HTML de cafés
    path("reviews/", include("reviews.urls")),

    # API
    path("api/", include(router.urls)),

    # robots
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
        RedirectView.as_view(url="/static/images/coffee-icon.png"),
        name="favicon",
    ),

    # --- Google verification ---
    path(
        "google157d26ef7e3007f2.html",
        static.serve,
        {"document_root": settings.STATIC_ROOT},
        name="google_verify",
    ),
]

# MEDIA fallback
urlpatterns += [
    re_path(r"^media/(?P<path>.*)$", settings.MEDIA_ROOT),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
