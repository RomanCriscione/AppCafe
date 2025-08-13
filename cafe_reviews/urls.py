# cafe_reviews/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.contrib.sitemaps import views as sitemap_views
from cafe_reviews.sitemaps import sitemaps

urlpatterns = [
    path("admin/", admin.site.urls),

    # Auth
    path("accounts/", include("allauth.urls")),
    path("users/", include("accounts.urls")),

    # Público
    path("", include("core.urls")),

    # Cafeterías y reseñas
    path("reviews/", include("reviews.urls")),

    # robots.txt estático
    path(
        "robots.txt",
        TemplateView.as_view(template_name="core/robots.txt", content_type="text/plain"),
        name="robots_txt",
    ),

    # sitemap.xml con el framework oficial
    path("sitemap.xml", sitemap_views.sitemap, {"sitemaps": sitemaps}, name="sitemap"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
