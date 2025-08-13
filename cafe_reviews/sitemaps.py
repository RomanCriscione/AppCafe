# cafe_reviews/sitemaps.py
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from reviews.models import Cafe

class StaticViewSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.5

    def items(self):
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

sitemaps = {
    "static": StaticViewSitemap,
    "cafes": CafeSitemap,
}
