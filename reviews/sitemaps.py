from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.db.models import Max
from .models import Cafe


class CafeSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Cafe.objects.all()

    def location(self, obj):
        return reverse("reviews:cafe_detail", kwargs={"cafe_id": obj.id})

    def lastmod(self, obj):
        latest_review = obj.reviews.aggregate(mx=Max("created_at"))["mx"]
        return latest_review or obj.created_at


class StaticViewSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.5

    def items(self):
        return [
            "reviews:review_list",
            "reviews:cafe_list",
            "reviews:mapa_cafes",
        ]

    def location(self, item):
        return reverse(item)
