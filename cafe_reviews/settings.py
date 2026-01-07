from pathlib import Path
from django.conf import settings
from django.contrib import admin
from django.urls import path, include, re_path

from django.views.generic import RedirectView
from django.views.static import serve            # ✅ este es el correcto

from django.contrib.sitemaps.views import sitemap
from cafe_reviews.sitemaps import sitemaps       # tu diccionario ya corregido

from rest_framework.routers import DefaultRouter
from reviews.api import CafeViewSet

BASE_DIR = Path(__file__).resolve().parent.parent

# Router API
router = DefaultRouter()
router.register(r"cafes", CafeViewSet, basename="cafe")

urlpatterns = [
    path("admin/", admin.site.urls),

    # Allauth
    path("accounts/", include("allauth.urls")),

    # Users
    path("users/", include("accounts.urls")),

    # Público
    path("", include("core.urls")),

    # Cafés HTML
    path("reviews/", include("reviews.urls")),

    # API REST
    path("api/", include(router.urls)),

    # robots
    path(
        "robots.txt",
        RedirectView.as_view(url="/static/css/"),
        name="robots_txt"
    ),

    # sitemap
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps},
            name="django_sitemap"),

    # favicon
    path("favicon.ico",
            RedirectView.as_view(url="/static/images/coffee-icon.png",
                                permanent=False),
            name="favicon"),

    # ==============================
    # 🔎 GOOGLE VERIFICATION
    # ==============================
    path(
        "google157d26ef7e3007f2.html",
        serve,
        {"document_root": BASE_DIR / "static"},
        name="google_verify",
    ),
]

# Servir MEDIA producción
urlpatterns += [
    re_path(r"^media/(?P<path>.*)$", serve,
            {"document_root": settings.MEDIA_ROOT}),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                            document_root=settings.MEDIA_ROOT)
