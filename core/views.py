from django.shortcuts import render
from reviews.models import Review, Cafe
from django.db.models import Avg
from django.urls import reverse
import json
from statistics import mean
from .utils import get_recently_viewed_cafes
from reviews.utils.tags import get_tags_grouped_by_cafe
from core import messages as core_messages

# ✅ Función auxiliar para obtener cafés vistos recientemente
def get_recently_viewed_cafes(request):
    cafe_ids = request.session.get("recently_viewed", [])
    return Cafe.objects.filter(id__in=cafe_ids).prefetch_related("tags")

# ✅ Vista principal del home
def home(request):
    latest_reviews = Review.objects.select_related("user", "cafe").order_by("-created_at")[:6]
    cafes_with_coords = Cafe.objects.filter(latitude__isnull=False, longitude__isnull=False).prefetch_related("tags")

    cafes_data = [
        {
            "id": cafe.id,
            "name": cafe.name,
            "address": cafe.address,
            "location": cafe.location,
            "latitude": cafe.latitude,
            "longitude": cafe.longitude,
            "url": reverse("cafe_detail", args=[cafe.id])
        }
        for cafe in cafes_with_coords
    ]

    top_cafes = []
    for cafe in cafes_with_coords:
        ratings = [review.rating for review in cafe.reviews.all()]
        if ratings:
            avg = sum(ratings) / len(ratings)
            if avg >= 4:
                top_cafes.append(cafe)

    tag_data = get_tags_grouped_by_cafe(top_cafes)
    recently_viewed_cafes = get_recently_viewed_cafes(request)

    context = {
        "latest_reviews": latest_reviews,
        "top_cafes": top_cafes[:6],
        "cafes_json": json.dumps(cafes_data),
        "recently_viewed_cafes": recently_viewed_cafes,
        "tag_data": tag_data,
        "ui_messages": {
            "welcome": core_messages.MESSAGES.get("welcome_user"),
            "no_results": core_messages.MESSAGES.get("search_no_results"),
            "no_reviews": core_messages.MESSAGES.get("cafe_no_reviews"),
            "no_favorites": core_messages.MESSAGES.get("no_favorites"),
            "no_user_reviews": core_messages.MESSAGES.get("no_reviews_user"),
            "loading": core_messages.MESSAGES.get("loading"),
            "error_404": core_messages.MESSAGES.get("error_404"),
            "owner_welcome": core_messages.MESSAGES.get("welcome_owner"),
            "cafe_added": core_messages.MESSAGES.get("cafe_added"),
            "review_submitted": core_messages.MESSAGES.get("review_sent"),
        }
    }
    return render(request, "core/home.html", context)


# ✅ Vista "Acerca de mí"
def about_view(request):
    return render(request, 'core/about.html')

# ✅ Vista de contacto
def contact_view(request):
    success = False
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        message = request.POST.get("message")
        success = True
    return render(request, "core/contact.html", {"success": success})
