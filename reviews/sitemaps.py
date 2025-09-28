# file: reviews/sitemaps.py
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Cafe
from django.db.models import Max

class CafeSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        # Si tenés un flag de "oculto" o similar, filtralo acá.
        return Cafe.objects.all().only("id", "name")

    def location(self, obj):
        return reverse("reviews:cafe_detail", kwargs={"cafe_id": obj.id})

    def lastmod(self, obj):
        # Si tu modelo Cafe tiene updated_at, usalo acá.
        latest_review = obj.reviews.aggregate(mx=Max("created_at"))["mx"]
        return latest_review

class StaticViewSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.5

    def items(self):
        # Solo páginas públicas
        return [
            ("reviews:review_list"),
            ("reviews:cafe_list"),
            ("reviews:mapa_cafes"),
        ]

    def location(self, item):
        return reverse(item)