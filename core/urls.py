# core/urls.py
from django.urls import path
from core import views as core_views

urlpatterns = [
    path("", core_views.home, name="home"),
    path("about/", core_views.about_view, name="about"),
    path("contact/", core_views.contact_view, name="contact"),

    # SEO
    path("sitemap.xml", core_views.sitemap_xml, name="django_sitemap"),
]

