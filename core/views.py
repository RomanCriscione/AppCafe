# file: core/views.py
from django.shortcuts import render
from django.http import HttpResponse
from django.urls import reverse
from django.core.serializers.json import DjangoJSONEncoder
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Avg, Count
import random


from reviews.models import Review, Cafe
from reviews.utils.tags import get_tags_grouped_by_cafe
from core import messages as core_messages

import json


# ✅ Cafés vistos recientemente (desde la sesión)
def get_recently_viewed_cafes(request):
    cafe_ids = request.session.get("recently_viewed", [])
    return Cafe.objects.filter(id__in=cafe_ids).prefetch_related("tags")


# ✅ Home
def home(request):
    # Últimas reseñas
    latest_reviews = (
        Review.objects
        .select_related("user", "cafe")
        .exclude(comment__isnull=True)
        .exclude(comment__exact="")
        .order_by("-created_at")[:3]
    )

    # Cafés con coordenadas (para mapa)
    cafes_with_coords = (
        Cafe.objects
        .filter(latitude__isnull=False, longitude__isnull=False)
        .prefetch_related("tags")
    )

    # Datos para el mapa (ojo con Decimals → JSON encoder)
    cafes_data = [
        {
            "id": cafe.id,
            "name": cafe.name,
            "address": cafe.address,
            "location": cafe.location,
            "latitude": cafe.latitude,
            "longitude": cafe.longitude,
            # 🔧 FIX: usar namespace 'reviews'
            "url": reverse("reviews:cafe_detail", kwargs={"cafe_id": cafe.id}),
        }
        for cafe in cafes_with_coords
    ]

    # 🔥 Cafés destacados inteligentes
    total_reviews = Review.objects.count()

    if total_reviews < 150:
        min_reviews = 2
    elif total_reviews < 600:
        min_reviews = 5
    else:
        min_reviews = 10

    top_cafes_qs = (
        Cafe.objects
        .annotate(
            avg_rating=Avg("reviews__rating"),
            num_reviews=Count("reviews")
        )
        .filter(avg_rating__gte=4, num_reviews__gte=min_reviews)
        .prefetch_related("tags")
        .order_by("-avg_rating", "-num_reviews")[:20]
    )

    top_cafes = list(top_cafes_qs)
    random.shuffle(top_cafes)
    top_cafes = top_cafes[:6]

    # Etiquetas por café
    tag_data = get_tags_grouped_by_cafe(top_cafes)

    # Cafés vistos recientemente
    recently_viewed_cafes = get_recently_viewed_cafes(request)

    # Zonas dinámicas
    home_zones = Cafe.objects.values_list("location", flat=True).distinct()

    context = {
        "latest_reviews": latest_reviews,
        "top_cafes": top_cafes,
        "cafes_json": json.dumps(cafes_data, cls=DjangoJSONEncoder),
        "recently_viewed_cafes": recently_viewed_cafes,
        "tag_data": tag_data,
        "home_zones": home_zones,
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
        },
    }
    context["meta_title"] = "Gota · Descubrí y recomendá cafeterías con identidad"
    context["meta_description"] = (
        "Gota es una plataforma para descubrir y recomendar cafeterías reales, "
        "con buen café y experiencias que se sienten."
    )

    return render(request, "core/home.html", context)




# ✅ About
def about_view(request):
    return render(request, "core/about.html")


# ✅ Contacto
def contact_view(request):
    success = False

    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        message = request.POST.get("message")

        if name and email and message:
            send_mail(
                subject=f"Contacto Gota · {name}",
                message=(
                    f"Nombre: {name}\n"
                    f"Email: {email}\n\n"
                    f"Mensaje:\n{message}"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=["hola@gogota.ar"],
                reply_to=[email],                         
            )
            success = True

    return render(request, "core/contact.html", {"success": success})



# ✅ Sitemap dinámico
def sitemap_xml(request):
    cafes = Cafe.objects.only("id").order_by("id")
    # `render` ya pasa `request` al template → podés usar {{ request.get_host }} ahí
    return render(
        request,
        "core/sitemap.xml",
        {"cafes": cafes},
        content_type="application/xml",
    )

