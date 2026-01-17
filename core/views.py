# file: core/views.py
from django.shortcuts import render
from django.http import HttpResponse
from django.urls import reverse
from django.core.serializers.json import DjangoJSONEncoder
from django.core.mail import send_mail
from django.conf import settings


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
        Review.objects.select_related("user", "cafe")
        .order_by("-created_at")[:6]
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

    # Cafés destacados con promedio >= 4
    top_cafes = []
    for cafe in cafes_with_coords:
        ratings = [r.rating for r in cafe.reviews.all()]
        if ratings:
            avg = sum(ratings) / len(ratings)
            if avg >= 4:
                top_cafes.append(cafe)

    # Etiquetas por café
    tag_data = get_tags_grouped_by_cafe(top_cafes)

    # Cafés vistos recientemente
    recently_viewed_cafes = get_recently_viewed_cafes(request)

    # Zonas dinámicas
    home_zones = Cafe.objects.values_list("location", flat=True).distinct()

    context = {
        "latest_reviews": latest_reviews,
        "top_cafes": top_cafes[:6],
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

