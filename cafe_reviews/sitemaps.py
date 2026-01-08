from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.db.models import Max


class StaticSitemap(Sitemap):
    """Sitemap de páginas estáticas"""

    def items(self):
        return [
            "home",
            "reviews:cafe_list",
            "reviews:mapa_cafes",
            "about",
            "contact",
        ]

    def changefreq(self, item):
        mapping = {
            "home": "weekly",
            "reviews:cafe_list": "daily",
            "reviews:mapa_cafes": "weekly",
            "about": "yearly",
            "contact": "yearly",
        }
        return mapping.get(item, "weekly")

    def priority(self, item):
        mapping = {
            "home": 0.8,
            "reviews:cafe_list": 0.9,
            "reviews:mapa_cafes": 0.6,
            "about": 0.3,
            "contact": 0.3,
        }
        return mapping.get(item, 0.5)

    def location(self, item):
        return reverse(item)


class CafeSitemap(Sitemap):
    """Sitemap de cafeterías"""

    changefreq = "monthly"
    priority = 0.7

    def items(self):
        # ✅ IMPORT DIFERIDO (CLAVE)
        from reviews.models import Cafe
        return Cafe.objects.only("id", "updated_at")

    def location(self, obj):
        return reverse("reviews:cafe_detail", kwargs={"cafe_id": obj.id})

    def lastmod(self, obj):
        last_review = obj.reviews.aggregate(last=Max("created_at")).get("last")
        return last_review or obj.updated_at


# ✅ diccionario FINAL (instancias, no clases)
sitemaps = {
    "static": StaticSitemap(),
    "cafes": CafeSitemap(),
}
