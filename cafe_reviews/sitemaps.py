# cafe_reviews/sitemaps.py
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.db.models import Max
from reviews.models import Cafe


class StaticSitemap(Sitemap):
    """Sitemap de páginas estáticas."""
    def items(self):
        # Nombres de URL (name) de tus vistas públicas
        return ["home", "cafe_list", "mapa_cafes", "about", "contact"]

    def location(self, item):
        return reverse(item)

    def changefreq(self, item):
        mapping = {
            "home": "weekly",
            "cafe_list": "daily",
            "mapa_cafes": "weekly",
            "about": "yearly",
            "contact": "yearly",
        }
        return mapping.get(item, "weekly")

    def priority(self, item):
        mapping = {
            "home": 0.8,
            "cafe_list": 0.9,
            "mapa_cafes": 0.8,
            "about": 0.3,
            "contact": 0.3,
        }
        return mapping.get(item, 0.5)


class CafeSitemap(Sitemap):
    """Sitemap de detalles de cafeterías."""
    changefreq = "monthly"
    priority = 0.7

    def items(self):
        return Cafe.objects.all()

    def location(self, obj):
        return reverse("cafe_detail", args=[obj.id])

    def lastmod(self, obj):
        # Última actividad: reseña más reciente del café
        last_review = obj.reviews.aggregate(last=Max("created_at"))["last"]
        # Si agregaste updated_at al modelo Cafe, lo usamos como fallback:
        return last_review or getattr(obj, "updated_at", None)


# Registro de sitemaps
sitemaps = {
    "static": StaticSitemap,
    "cafes": CafeSitemap,
}
