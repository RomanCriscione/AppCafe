from pathlib import Path

from django.conf import settings
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.static import serve
from django.views.generic import RedirectView, TemplateView

from django.contrib.sitemaps.views import sitemap
from cafe_reviews.sitemaps import sitemaps

from rest_framework.routers import DefaultRouter
from reviews.api import CafeViewSet

BASE_DIR = Path(__file__).resolve().parent.parent

# =====================
# API ROUTER
# =====================
router = DefaultRouter()
router.register(r"cafes", CafeViewSet, basename="cafe")

urlpatterns = [
    path("admin/", admin.site.urls),

    # auth
    path("accounts/", include("allauth.urls")),
    path("users/", include("accounts.urls")),

    # frontend
    path("", include("core.urls")),
    path("reviews/", include("reviews.urls")),

    # api
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

    # Google verification
    path(
        "google157d26ef7e3007f2.html",
        serve,
        {"document_root": BASE_DIR / "static"},
        name="google_verify",
    ),
]

# MEDIA
urlpatterns += [
    re_path(
        r"^media/(?P<path>.*)$",
        serve,
        {"document_root": settings.MEDIA_ROOT},
    ),
]
