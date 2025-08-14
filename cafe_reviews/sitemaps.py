# cafe_reviews/sitemaps.py
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.db.models import Max

from reviews.models import Cafe


class StaticViewSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        # nombres de URL que existen en tu proyecto
        return ["home", "cafe_list", "mapa_cafes", "about", "contact"]

    def location(self, item):
        return reverse(item)


class CafeSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.7

    def items(self):
        return Cafe.objects.all()

    def location(self, obj):
        return reverse("cafe_detail", args=[obj.id])

    def lastmod(self, obj):
        # última actividad del café = última reseña creada
        return obj.reviews.aggregate(last=Max("created_at"))["last"]


sitemaps = {
    "static": StaticViewSitemap,
    "cafes": CafeSitemap,
}
