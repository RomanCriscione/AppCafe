# core/urls.py
from django.urls import path
from core import views as core_views

urlpatterns = [
    path("", core_views.home, name="home"),
    path("about/", core_views.about_view, name="about"),
    path("contact/", core_views.contact_view, name="contact"),
    path("privacidad/",core_views.privacy_policy_view,name="privacy_policy",),
    path("eliminar-cuenta/",core_views.delete_account_request_view,name="delete_account_request",),

    # SEO
    path("sitemap.xml", core_views.sitemap_xml, name="django_sitemap"),
]

