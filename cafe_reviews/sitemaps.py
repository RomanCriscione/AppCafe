from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.db.models import Max
from reviews.models import Cafe


class StaticSitemap(Sitemap):
    """Sitemap de páginas estáticas."""
    def items(self):
        # OJO: las rutas de reviews están bajo el namespace "reviews"
        # core.* (home/about/contact) quedan sin namespace porque se incluyen sin namespace en cafe_reviews/urls.py
        return [
            "home",
            "reviews:cafe_list",
            "reviews:mapa_cafes",
            "about",
            "contact",
        ]

    def location(self, item):
        return reverse(item)

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
            "reviews:mapa_cafes": 0.8,
            "about": 0.3,
            "contact": 0.3,
        }
        return mapping.get(item, 0.5)


class CafeSitemap(Sitemap):
    """Sitemap de detalles de cafeterías."""
    changefreq = "monthly"
    priority = 0.7

    def items(self):
        # Sólo necesitamos el id para armar la URL
        return Cafe.objects.only("id")

    def location(self, obj):
        # Respetar el namespace "reviews"
        return reverse("reviews:cafe_detail", kwargs={"cafe_id": obj.id})

    def lastmod(self, obj):
        # Última actividad: reseña más reciente del café
        last_review = obj.reviews.aggregate(last=Max("created_at"))["last"]
        # Si el modelo Cafe tiene updated_at, lo usamos como fallback
        return last_review or getattr(obj, "updated_at", None)


# Registro de sitemaps
sitemaps = {
    "static": StaticSitemap,
    "cafes": CafeSitemap,
}
