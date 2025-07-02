from django.shortcuts import render
from reviews.models import Review, Cafe
from django.db.models import Avg
from django.urls import reverse
import json
from statistics import mean

# ✅ Función auxiliar para obtener cafés vistos recientemente
def get_recently_viewed_cafes(request):
    cafe_ids = request.session.get("recently_viewed", [])
    return Cafe.objects.filter(id__in=cafe_ids).prefetch_related("tags")

# ✅ Vista principal del home
def home(request):
    latest_reviews = Review.objects.select_related("user", "cafe").order_by("-created_at")[:6]

    all_cafes = Cafe.objects.prefetch_related("reviews", "tags")

    top_cafes = []
    for cafe in all_cafes:
        ratings = [review.rating for review in cafe.reviews.all()]
        if ratings:
            avg = mean(ratings)
            if avg >= 4:
                top_cafes.append(cafe)

    cafes_data = [
        {
            "name": cafe.name,
            "latitude": cafe.latitude,
            "longitude": cafe.longitude,
            "url": reverse("cafe_detail", args=[cafe.id])
        }
        for cafe in top_cafes if cafe.latitude and cafe.longitude
    ]

    recently_viewed_cafes = get_recently_viewed_cafes(request)

    context = {
        "latest_reviews": latest_reviews,
        "top_cafes": top_cafes[:6],  
        "cafes_json": json.dumps(cafes_data),
        "recently_viewed_cafes": recently_viewed_cafes,
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
