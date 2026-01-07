from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.generic import RedirectView, TemplateView
from django.views.static import serve        # ✅

from django.contrib.sitemaps.views import sitemap
from cafe_reviews.sitemaps import sitemaps   # tu diccionario del sitemaps.py

from rest_framework.routers import DefaultRouter
from reviews.api import CafeViewSet

# === Router API ===
router = DefaultRouter()
router.register(r"cafes", CafeViewSet, basename="cafe")

urlpatterns = [
    path("admin/", admin.site.urls),

    # Allauth
    path("accounts/", include("allauth.urls")),

    # Usuarios
    path("users/", include("accounts.urls")),

    # Público
    path("", include("core.urls")),

    # App reviews HTML
    path("reviews/", include("reviews.urls")),

    # API
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

    # sitemap principal
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

    # ==============================
    # 🔎 GOOGLE VERIFICATION
    # ==============================
    path(
        "google157d26ef7e3007f2.html",
        serve,
        {
            "document_root": settings.STATIC_ROOT,   # es Path, Whitenoise lo sirve
            "path": "google157d26ef7e3007f2.html",   # ✅ ESTO RESUELVE EL ERROR
        },
        name="google_verify",
    ),
]

# === MEDIA producción ===
urlpatterns += [
    re_path(
        r"^media/(?P<path>.*)$",
        serve,
        {"document_root": settings.MEDIA_ROOT},
    ),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
