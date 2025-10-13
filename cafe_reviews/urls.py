# cafe_reviews/urls.py
from django.contrib import admin
from django.urls import path, include, re_path      # ⬅️ re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView, RedirectView
from django.contrib.sitemaps.views import sitemap
from django.views.static import serve as media_serve # ⬅️ media_serve
from cafe_reviews.sitemaps import sitemaps

from django.templatetags.static import static as static_url
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

    # Público
    path("", include("core.urls")),

    # Cafés (HTML)
    path("reviews/", include(("reviews.urls", "reviews"), namespace="reviews")),

    # API
    path("api/", include(router.urls)),

    # robots.txt
    path(
        "robots.txt",
        TemplateView.as_view(template_name="core/robots.txt", content_type="text/plain"),
        name="robots_txt",
    ),

    # sitemap
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="django_sitemap"),

    # favicon (archivo real en /static/images/)
    path(
        "favicon.ico",
        RedirectView.as_view(url=static_url("images/coffee-icon.png"), permanent=False),
        name="favicon",
    ),
]

# ✅ Servir MEDIA también en producción (Render)
urlpatterns += [
    re_path(r"^media/(?P<path>.*)$", media_serve, {"document_root": settings.MEDIA_ROOT}),
]

# (Opcional) si querés mantener la variante clásica para dev:
# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
