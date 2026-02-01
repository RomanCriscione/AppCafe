from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg, Count, F, Q, Sum
from django.views.generic import ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.core.exceptions import PermissionDenied
from collections import defaultdict
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponseForbidden
from django.core.serializers.json import DjangoJSONEncoder
from django.templatetags.static import static
from django.utils import timezone
from datetime import timedelta
from django.views.decorators.http import require_POST
from django.conf import settings
import os, json
from core.mixins import EmailVerifiedRequiredMixin
from allauth.account.models import EmailAddress
from core.rate_limit import rate_limit
from reviews.utils.ranking import calcular_score_cafe
from .models import Review, Cafe, ReviewLike, ReviewReport, Tag, CafeStat
from .forms import ReviewForm, CafeForm, ReviewReportForm
from reviews.utils.geo import haversine_distance
from core.messages import MESSAGES
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from openpyxl import Workbook
from datetime import datetime

# Helper para invalidar el fragment cache de la lista de reseñas
def _invalidate_reviews_cache(cafe_id, user_id=None):
    from django.core.cache.utils import make_template_fragment_key
    from django.core.cache import cache

    # El template usa: {% cache 600 cafe_reviews_list cafe.id user.id %}
    posibles = [
        make_template_fragment_key("cafe_reviews_list", [cafe_id, ""]),
        make_template_fragment_key("cafe_reviews_list", [cafe_id, "None"]),
    ]
    if user_id:
        posibles.append(make_template_fragment_key("cafe_reviews_list", [cafe_id, user_id]))

    for k in posibles:
        cache.delete(k)

# ✅ cache fragment
from django.core.cache.utils import make_template_fragment_key
from django.core.cache import cache


_UI_MSG = {
    "no_results": "No encontramos cafés con esos filtros.",
    "search_no_results": "No encontramos cafés en esa zona.",
    "no_reviews": "Todavía no hay reseñas.",
}

# === TAGS SENSORIALES MANUALES (18 etiquetas, 3 grupos) ===

MANUAL_TAG_GROUPS = {
    "Sensorial": [
        "Baños cuidados (y eso dice mucho)",
        "Cada taza es distinta, como debe ser",
        "Hay un gato que manda",
        "Paredes con historias (y fotos de verdad)",
        "Ventanales con luz todo el día",
        "Huele a café recién molido",
    ],
    "Ambiente / Servicio": [
        "Podés ir solo sin sentirte solo",
        "Te saludan por tu nombre",
        "Ideal para charla de sobremesa",
        "Buen lugar para esperar sin ansiedad",
        "Ideal para una primera cita sin presión",
        "Te vas y te dan ganas de volver",
    ],
    "Emocional / Experiencia": [
        "Buena conexión, pero te da ganas de desconectarte",
        "Ideal para escribir un cuento",
        "La playlist ayuda a concentrarse",
        "Las sillas no te arruinan la espalda",
        "Para leer sin mirar el reloj",
        "Pan casero y café en taza pesada",
    ],
}


def get_manual_tag_choices():
    all_names = []
    for names in MANUAL_TAG_GROUPS.values():
        all_names.extend(names)

    tags_qs = (
        Tag.objects
        .filter(name__in=all_names)
        .annotate(num_reviews=Count("reviews"))
    )

    tags_by_name = {t.name: t for t in tags_qs}

    grouped = {}
    for category, names in MANUAL_TAG_GROUPS.items():
        tags = [tags_by_name[n] for n in names if n in tags_by_name]
        tags.sort(key=lambda t: (-t.num_reviews, t.name.lower()))
        grouped[category] = tags

    return grouped

FEATURE_FIELDS = [
    # Servicios / infraestructura
    "has_wifi",
    "has_air_conditioning",
    "has_power_outlets",
    "has_outdoor_seating",
    "has_parking",
    "is_accessible",
    "accepts_cards",
    "accepts_reservations",
    "has_baby_changing",

    # Mascotas
    "is_pet_friendly",

    # Oferta gastronómica
    "has_specialty_coffee",
    "serves_brunch",
    "serves_breakfast",
    "serves_alcohol",
    "has_artisanal_pastries",
    "offers_ice_cream",

    # Opciones alimentarias
    "is_vegan_friendly",
    "has_vegetarian_options",
    "has_gluten_free_options",

    # Uso del espacio
    "laptop_friendly",
    "quiet_space",

    # Extras
    "has_books_or_games",
]



class ReviewListView(ListView):
    model = Review
    template_name = 'reviews/review_list.html'
    context_object_name = 'reviews'
    ordering = ['-created_at']

    def get_queryset(self):
        return Review.objects.select_related('cafe', 'user')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request = self.request

        context['zonas_disponibles'] = (
            Cafe.objects.values_list('location', flat=True)
            .distinct().order_by('location')
        )
        context['zona_seleccionada'] = request.GET.get('zona')
        context['orden_actual'] = request.GET.get('orden')

        boolean_keys = [
            'has_wifi', 'has_air_conditioning', 'serves_alcohol', 'is_pet_friendly',
            'is_vegan_friendly', 'has_outdoor_seating', 'has_parking', 'is_accessible',
            'has_vegetarian_options', 'has_books_or_games', 'serves_breakfast',
            "accepts_cards", "has_gluten_free_options", "has_baby_changing",
            "has_power_outlets", "laptop_friendly", "quiet_space",
            "has_specialty_coffee", "serves_brunch", "accepts_reservations",
        ]
        context['campos_activos'] = {k: (request.GET.get(k) == 'on') for k in boolean_keys}

        context['mostrar_boton_reset'] = any([
            request.GET.get('zona'),
            request.GET.get('orden'),
            request.GET.get('lat'),
            request.GET.get('lon'),
            *[request.GET.get(k) for k in boolean_keys],
        ])

        if request.user.is_authenticated:
            context['favoritos_ids'] = set(
                request.user.favorite_cafes.values_list('id', flat=True)
            )
        else:
            context['favoritos_ids'] = set()

        cafes = (
            Cafe.objects.only('id', 'name', 'latitude', 'longitude')
            .exclude(latitude__isnull=True).exclude(longitude__isnull=True)
        )
        cafes_data = [
            {
                'id': c.id,
                'name': c.name,
                'latitude': float(c.latitude),
                'longitude': float(c.longitude),
                'url': reverse('reviews:cafe_detail', kwargs={'cafe_id': c.id}),
            }
            for c in cafes
        ]
        context['cafes_json'] = json.dumps(cafes_data, cls=DjangoJSONEncoder)
        context['ui_messages'] = _UI_MSG
        return context
    

class CafeListView(ListView):
    model = Cafe
    template_name = 'reviews/cafe_list.html'
    context_object_name = 'cafes'
    paginate_by = 12

    def get_queryset(self):
        request = self.request
        zona = request.GET.get('zona')
        orden = request.GET.get('orden', 'algoritmo')
        lat = request.GET.get('lat')
        lon = request.GET.get('lon')


        cafes = Cafe.objects.only(
            'id', 'name', 'location', 'latitude', 'longitude',
            'photo1', 'photo2', 'photo3',
            'visibility_level',
            'is_vegan_friendly', 'is_pet_friendly', 'has_wifi',
            'has_outdoor_seating', 'has_parking', 'is_accessible',
            'has_vegetarian_options', 'serves_breakfast', 'serves_alcohol',
            'has_books_or_games', 'has_air_conditioning'
)


        if zona:
            cafes = cafes.filter(location=zona)

        for field in FEATURE_FIELDS:
            if request.GET.get(field) == "on":
                cafes = cafes.filter(**{field: True})

        # Alias para que la tarjeta lea avg_rating / num_reviews
        cafes = cafes.annotate(
            average_rating=Avg('reviews__rating'),
            avg_rating=Avg('reviews__rating'),
            total_reviews=Count('reviews'),
            num_reviews=Count('reviews'),
            precio_promedio=Avg('reviews__precio_capuccino'),
        ).prefetch_related('favorites')

        if orden == 'rating':
            cafes = cafes.order_by('-average_rating')

        elif orden == 'reviews':
            cafes = cafes.order_by('-total_reviews')

        else:
            # 🔥 ALGORITMO POR DEFECTO
            cafes = list(cafes)

            cafes_vistos = request.session.get("cafes_vistos", [])

            for cafe in cafes:
                cafe.score = calcular_score_cafe(
                    cafe,
                    user=request.user if request.user.is_authenticated else None,
                    user_lat=float(lat) if lat else None,
                    user_lon=float(lon) if lon else None,
                    cafes_vistos_ids=cafes_vistos,
                )

            cafes.sort(key=lambda c: c.score, reverse=True)


        # Filtro por ubicación (3 km)
        if lat and lon:
            try:
                lat = float(lat)
                lon = float(lon)
                cafes = [
                    cafe for cafe in cafes
                    if cafe.latitude and cafe.longitude and
                    haversine_distance(lat, lon, cafe.latitude, cafe.longitude) <= 3
                ]
            except ValueError:
                pass

        return cafes

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request = self.request
                # === SEO: meta dinámicos para listado de cafés ===
        zona = request.GET.get("zona")
        orden = request.GET.get("orden")

        if zona:
            context["meta_title"] = f"Cafeterías en {zona} | Gota"
            context["meta_description"] = (
                f"Descubrí cafeterías en {zona}: reseñas reales, buen café y experiencias con identidad."
            )
        else:
            context["meta_title"] = "Cafeterías recomendadas | Gota"
            context["meta_description"] = (
                "Descubrí y recomendá cafeterías reales: buen café, reseñas honestas y experiencias que se sienten."
            )


        context['zonas_disponibles'] = (
            Cafe.objects.values_list('location', flat=True)
            .distinct().order_by('location')
        )
        context['zona_seleccionada'] = request.GET.get('zona')
        context['orden_actual'] = request.GET.get('orden', 'algoritmo')

        context["campos_activos"] = {
            field: field in request.GET
            for field in FEATURE_FIELDS
        }


        context['mostrar_boton_reset'] = any([
            request.GET.get('zona'),
            request.GET.get('orden'),
            request.GET.get('lat'),
            request.GET.get('lon'),
            *[request.GET.get(f) for f in FEATURE_FIELDS],
        ])

        if request.user.is_authenticated:
            context['favoritos_ids'] = set(
                request.user.favorite_cafes.values_list('id', flat=True)
            )
        else:
            context['favoritos_ids'] = set()

        cafes = context.get('cafes', [])
        cafes_data = []
        for c in cafes:
            cafes_data.append({
                'id': c.id,
                'name': c.name,
                'latitude': float(c.latitude) if c.latitude is not None else None,
                'longitude': float(c.longitude) if c.longitude is not None else None,
                'url': reverse('reviews:cafe_detail', kwargs={'cafe_id': c.id}),
            })
        context['cafes_json'] = json.dumps(cafes_data, cls=DjangoJSONEncoder)
        context['ui_messages'] = _UI_MSG
        return context


def cafe_detail(request, cafe_id):
    cafe = get_object_or_404(Cafe, id=cafe_id)

    # ⭐ NUEVO — highlight desde URL (?highlight=ID)
    highlight_id = request.GET.get("highlight")

    # todas las reseñas de ese café
    reviews_qs = (
        cafe.reviews
        .select_related("user")
        .prefetch_related("tags")
        .annotate(likes_count=Count("likes", distinct=True))
        .order_by("-created_at")
    )

    total_reviews = reviews_qs.count()
    agg = reviews_qs.aggregate(avg=Avg("rating"))
    average_rating = round(agg["avg"], 1) if agg["avg"] is not None else None
    best_review = reviews_qs.order_by("-rating", "-created_at").first()

    # ⭐ promedio de precio del capuccino
    precio_promedio = cafe.reviews.filter(
        precio_capuccino__isnull=False
    ).aggregate(
        Avg("precio_capuccino")
    )["precio_capuccino__avg"]

    # % positivas
    positives = reviews_qs.filter(rating__gte=4).count()
    positive_pct = int((positives / total_reviews) * 100) if total_reviews else 0

    # radar por categorías a partir de tags
    SENSOR_AXES = ["sensorial", "emocional", "estética", "ambiente", "comida", "bebida", "servicio"]
    sensor_rows = (
        Tag.objects.filter(reviews__cafe=cafe)
        .values("category")
        .annotate(count=Count("reviews", filter=Q(reviews__cafe=cafe)))
    )
    sensor_dict = {row["category"]: row["count"] for row in sensor_rows}
    radar_labels = SENSOR_AXES
    radar_values = [sensor_dict.get(k, 0) for k in SENSOR_AXES]

    # paginado
    paginator = Paginator(reviews_qs, 8)
    page_obj = paginator.get_page(request.GET.get("page") or 1)

    # fotos seguras
    safe_photos = []
    for idx in (1, 2, 3):
        photo = getattr(cafe, f"photo{idx}", None)
        title = getattr(cafe, f"photo{idx}_title", "") or cafe.name
        if not photo:
            continue
        try:
            url = photo.url
        except Exception:
            continue
        safe_photos.append({"url": url, "title": title})

    # tags más usadas
    tag_counts_qs = (
        Tag.objects.filter(reviews__cafe=cafe)
        .annotate(num=Count("reviews", filter=Q(reviews__cafe=cafe)))
        .order_by("-num", "name")
    )
    top_tags = list(tag_counts_qs[:5])
    more_tags = list(tag_counts_qs[5:])

    # recomendados
    recommended_cafes = (
        Cafe.objects.annotate(average_rating=Avg("reviews__rating"))
        .filter(average_rating__isnull=False)
        .exclude(id=cafe.id)
        .order_by("-average_rating")[:4]
    )

    # urls absolutas
    full_page_url = request.build_absolute_uri(
        reverse("reviews:cafe_detail", kwargs={"cafe_id": cafe.id})
    )
    if safe_photos:
        og_image_path = safe_photos[0]["url"]
    else:
        og_image_path = static("images/og-default.jpg")
    full_image_url = request.build_absolute_uri(og_image_path)
    cafe_list_abs = request.build_absolute_uri(reverse("reviews:cafe_list"))

    # likes del usuario + su review
    liked_ids = set()
    my_review = None
    if request.user.is_authenticated:
        liked_ids = set(
            ReviewLike.objects.filter(user=request.user, review__cafe=cafe)
            .values_list("review_id", flat=True)
        )
        my_review = (
            Review.objects.filter(user=request.user, cafe=cafe)
            .order_by("-created_at", "-id")
            .first()
        )

    # texto de cabecera
    one_liner = None

    if top_tags:
        one_liner = f"Ideal: {top_tags[0].name}"
    elif best_review and best_review.comment:
        txt = best_review.comment.strip()
        one_liner = txt[:90] + ("…" if len(txt) > 90 else "")

    # === Diversidad: marcar café como visto ===
    vistos = request.session.get("cafes_vistos", [])

    if cafe.id not in vistos:
        vistos.append(cafe.id)

    # limitar tamaño para no inflar la sesión
    request.session["cafes_vistos"] = vistos[-50:]


    return render(
        request,
        "reviews/cafe_detail.html",
        {
            "cafe": cafe,
            "reviews": page_obj.object_list,
            "page_obj": page_obj,
            "total_reviews": total_reviews,
            "average_rating": average_rating,
            "best_review": best_review,
            "positive_pct": positive_pct,
            "radar_labels": radar_labels,
            "radar_values": radar_values,
            "recommended_cafes": recommended_cafes,
            "top_tags": top_tags,
            "more_tags": more_tags,
            "liked_ids": liked_ids,
            "my_review": my_review,
            "one_liner": one_liner,
            "full_page_url": full_page_url,
            "full_image_url": full_image_url,
            "cafe_list_abs": cafe_list_abs,
            "photos": safe_photos,

            # ⭐ NUEVOS
            "precio_promedio": precio_promedio,
            "highlight_id": int(highlight_id) if highlight_id and highlight_id.isdigit() else None,

                    # ✅ SEO
            "meta_title": f"{cafe.name} en {cafe.location} | Reseñas y experiencias reales – Gota",
            "meta_description": (
                f"{cafe.name} en {cafe.location}. "
                "Reseñas reales, fotos, puntuaciones y experiencias de personas que lo visitaron."
            ),
            "og_image_url": cafe.photo1.url if cafe.photo1 else full_image_url,
        },
    )



@login_required
def create_review(request, cafe_id):
    if not EmailAddress.objects.filter(
        user=request.user,
        verified=True
    ).exists():
        messages.warning(
            request,
            MESSAGES["email_not_verified"]
        )

        return redirect("account_email_verification_sent")
    cafe = get_object_or_404(Cafe, pk=cafe_id)

    # --- evitar múltiples reseñas ---
    existing = (
        Review.objects.filter(user=request.user, cafe=cafe)
        .order_by("-created_at", "-id")
        .first()
    )
    if request.method == "GET" and existing:
        messages.info(request, MESSAGES["review_already_exists"])
        return redirect("reviews:edit_review", review_id=existing.id)

    selected_tag_ids = []
    current_step = "1"

    # =========================
    # POST
    # =========================
    if request.method == "POST":
        form = ReviewForm(request.POST)
        current_step = request.POST.get("current_step") or "1"

        try:
            initial_rating = int(request.POST.get("rating") or 0)
        except ValueError:
            initial_rating = 0

        selected_tag_ids = [
            int(t) for t in request.POST.getlist("tags") if t.isdigit()
        ]

        if form.is_valid():
            review = form.save(commit=False)
            review.cafe = cafe
            review.user = request.user

            precio = request.POST.get("precio_capuccino")
            review.precio_capuccino = (
                int(precio) if precio and precio.isdigit() else None
            )

            review.save()

            if selected_tag_ids:
                review.tags.set(
                    Tag.objects.filter(id__in=selected_tag_ids)
                )

            try:
                _invalidate_reviews_cache(cafe.id, user_id=request.user.id)
            except Exception:
                pass

            messages.success(
                request,
                "¡Gracias por tu reseña!",
                extra_tags="review_success"
            )
            return redirect(
    f"{reverse('reviews:cafe_detail', args=[cafe.id])}?highlight={review.id}#reviews")


        else:
            messages.error(request, MESSAGES["form_invalid"])


    # =========================
    # GET
    # =========================
    else:
        try:
            initial_rating = int(request.GET.get("rating") or 0)
        except ValueError:
            initial_rating = 0

        form = ReviewForm(initial={"rating": initial_rating})

    # 👉 SIEMPRE disponible (GET y POST inválido)
    tag_choices = get_manual_tag_choices()

    return render(
        request,
        "reviews/create_review.html",
        {
            "form": form,
            "cafe": cafe,
            "tag_choices": tag_choices,
            "initial_rating": initial_rating,
            "selected_tag_ids": selected_tag_ids,
            "current_step": current_step,
        },
    )


@login_required
def edit_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)

    if request.user != review.user and not request.user.is_staff:
        raise PermissionDenied("No podés editar esta reseña.")

    selected_tag_ids = list(review.tags.values_list("id", flat=True))

    if request.method == "POST":
        form = ReviewForm(request.POST, instance=review)

        try:
            initial_rating = int(request.POST.get("rating") or review.rating or 0)
        except:
            initial_rating = int(review.rating or 0)

        selected_tag_ids = [int(t) for t in request.POST.getlist("tags") if t.isdigit()]

        if form.is_valid():
            form.save()

            if "tags" in request.POST:
                review.tags.set(Tag.objects.filter(id__in=selected_tag_ids))

            key = make_template_fragment_key("cafe_reviews_list", [review.cafe_id])
            cache.delete(key)

            messages.success(request, "Reseña actualizada correctamente.")
            return redirect("reviews:cafe_detail", cafe_id=review.cafe_id)
        else:
            messages.error(request, "Por favor corregí los errores.")
    else:
        form = ReviewForm(instance=review)
        try:
            initial_rating = int(review.rating or 0)
        except:
            initial_rating = 0

    tag_choices = get_manual_tag_choices()

    return render(
        request,
        "reviews/create_review.html",
        {
            "form": form,
            "cafe": review.cafe,
            "tag_choices": tag_choices,
            "editing": True,
            "initial_rating": initial_rating,
            "selected_tag_ids": selected_tag_ids,
        },
    )



@login_required
def delete_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)

    if request.user != review.user and not request.user.is_staff:
        raise PermissionDenied("No podés eliminar esta reseña.")

    cafe_id = review.cafe_id

    if request.method == 'POST':
        review.delete()
        key = make_template_fragment_key("cafe_reviews_list", [cafe_id])
        cache.delete(key)
        messages.success(request, "Reseña eliminada.")
        return redirect("reviews:cafe_detail", cafe_id=cafe_id)

    return render(request, 'reviews/delete_review.html', {"review": review, "cafe": review.cafe})


@login_required
def reply_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)

    if request.user != review.cafe.owner:
        raise PermissionDenied("No sos el dueño de esta cafetería.")

    if request.method == 'POST':
        review.owner_reply = request.POST.get('reply')
        review.save()
        key = make_template_fragment_key("cafe_reviews_list", [review.cafe_id])
        cache.delete(key)
        messages.success(request, "Respuesta guardada con éxito.")
        return redirect('reviews:cafe_detail', cafe_id=review.cafe.id)


class ReviewCreateView(LoginRequiredMixin, CreateView):
    model = Review
    form_class = ReviewForm
    template_name = 'reviews/create_review.html'
    success_url = reverse_lazy('reviews:review_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tag_choices = defaultdict(list)
        for tag in Tag.objects.all():
            tag_choices[tag.category].append(tag)
        context['tag_choices'] = dict(tag_choices)
        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        tags = form.cleaned_data.get('tags')
        if tags:
            self.object.tags.set(tags)
        if getattr(self.object, "cafe_id", None):
            key = make_template_fragment_key("cafe_reviews_list", [self.object.cafe_id])
            cache.delete(key)
        return response


@login_required
def owner_dashboard(request):
    owner = request.user
    cafes = Cafe.objects.filter(owner=owner).prefetch_related('reviews__tags')
    no_cafes = not cafes.exists()

    for cafe in cafes:
        tags = Tag.objects.filter(
            reviews__cafe=cafe
        ).values('name', 'category').annotate(count=Count('id')).order_by('-count')

        grouped_tags = defaultdict(list)
        for tag in tags:
            grouped_tags[tag['category']].append({
                'name': tag['name'],
                'count': tag['count'],
            })
        cafe.tags_summary = grouped_tags

    context = {'cafes': cafes, 'no_cafes': no_cafes}
    return render(request, 'reviews/owner_dashboard.html', context)


@login_required
def owner_reviews(request):
    if not request.user.is_owner:
        raise PermissionDenied("Solo los dueños pueden ver esta sección.")

    cafes = Cafe.objects.filter(owner=request.user).prefetch_related('reviews')
    reseñas_por_cafe = {}

    for cafe in cafes:
        reviews = cafe.reviews.select_related('user').order_by('-rating', '-created_at')
        average_rating = reviews.aggregate(avg=Avg('rating'))['avg']
        reseñas_por_cafe[cafe] = {
            'reviews': reviews,
            'average_rating': round(average_rating, 1) if average_rating else None
        }

    return render(request, 'reviews/owner_reviews.html', {
        'reseñas_por_cafe': reseñas_por_cafe
    })


class CreateCafeView(
    EmailVerifiedRequiredMixin,
    LoginRequiredMixin,
    CreateView
):
    model = Cafe
    form_class = CafeForm
    template_name = 'reviews/create_cafe.html'
    success_url = reverse_lazy('reviews:cafe_list')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_owner:
            raise PermissionDenied("Solo los dueños de cafeterías pueden agregar una.")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.owner = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, MESSAGES["cafe_added"])
        return response


@login_required
def edit_cafe(request, cafe_id):
    cafe = get_object_or_404(Cafe, id=cafe_id)

    if request.user != cafe.owner:
        raise PermissionDenied("No tenés permiso para editar esta cafetería.")

    if request.method == 'POST':
        form = CafeForm(request.POST, request.FILES, instance=cafe)
        if form.is_valid():
            form.save()
            messages.success(request, "Cafetería actualizada con éxito.")
            return redirect('reviews:owner_dashboard')
    else:
        form = CafeForm(instance=cafe)

    return render(request, 'reviews/edit_cafe.html', {'form': form, 'cafe': cafe})


@login_required
def delete_cafe(request, cafe_id):
    cafe = get_object_or_404(Cafe, id=cafe_id, owner=request.user)

    if request.method == 'POST':
        fotos = [cafe.photo1, cafe.photo2, cafe.photo3]
        cafe.delete()
        for foto in fotos:
            try:
                if foto and os.path.isfile(foto.path):
                    os.remove(foto.path)
            except Exception:
                pass
        messages.success(request, "Cafetería eliminada junto con sus fotos y reseñas.")
        return redirect('reviews:owner_dashboard')

    return render(request, 'reviews/delete_cafe.html', {'cafe': cafe})


@login_required
def upload_photos(request, cafe_id):
    cafe = get_object_or_404(Cafe, pk=cafe_id)

    if request.method == 'POST':
        form = CafeForm(request.POST, request.FILES, instance=cafe)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fotos actualizadas correctamente.')
            return redirect('reviews:cafe_detail', cafe_id=cafe.id)
    else:
        form = CafeForm(instance=cafe)

    return render(request, 'reviews/upload_photos.html', {'form': form, 'cafe': cafe})


@login_required
def favorite_cafes(request):
    orden = request.GET.get('orden')
    zona = request.GET.get('zona')

    cafes = Cafe.objects.filter(favorites=request.user)

    if zona:
        cafes = cafes.filter(location=zona)

    cafes = cafes.annotate(
        average_rating=Avg('reviews__rating'),
        total_reviews=Count('reviews')
    ).prefetch_related('reviews')

    if orden == 'rating':
        cafes = cafes.order_by('-average_rating')
    elif orden == 'reviews':
        cafes = cafes.order_by('-total_reviews')
    else:
        cafes = cafes.order_by('name')

    for cafe in cafes:
        cafe.last_review = cafe.reviews.order_by('-created_at').first()

    zonas_disponibles = Cafe.objects.filter(favorites=request.user).values_list('location', flat=True).distinct()

    paginator = Paginator(cafes, 6)
    pagina = request.GET.get('page')
    cafes_paginados = paginator.get_page(pagina)

    return render(request, 'reviews/favorite_cafes.html', {
        'cafes': cafes_paginados,
        'orden_actual': orden,
        'zona_actual': zona,
        'zonas_disponibles': zonas_disponibles
    })


@login_required
@require_POST
def toggle_favorite(request, cafe_id):

    # ⛔ Bloqueo si email no está verificado
    if not EmailAddress.objects.filter(
        user=request.user,
        verified=True
    ).exists():

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse(
                {
                    "ok": False,
                    "error": "email_not_verified",
                    "message": "Confirmá tu email para usar favoritos."
                },
                status=403
            )

        messages.warning(
            request,
            "Confirmá tu email para usar favoritos."
        )
        return redirect("account_email_verification_sent")

    rl = rate_limit(
        key=f"fav:{request.user.id}",
        limit=20,
        window_seconds=60,
        ajax=True,
        message="Demasiados favoritos en poco tiempo."
    )
    if rl:
        return rl

    cafe = get_object_or_404(Cafe, id=cafe_id)

    if request.user in cafe.favorites.all():
        cafe.favorites.remove(request.user)
        liked = False
        messages.info(request, f"{cafe.name} eliminado de favoritos.")
    else:
        cafe.favorites.add(request.user)
        liked = True
        messages.success(request, f"{cafe.name} agregado a favoritos. ❤️")

    # AJAX (fetch)
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"ok": True, "liked": liked})

    # Fallback sin JS
    return redirect(request.META.get("HTTP_REFERER") or reverse("reviews:cafe_list"))



@login_required
def edit_owner_reply(request, review_id):
    review = get_object_or_404(Review, id=review_id)

    if request.user != review.cafe.owner:
        raise PermissionDenied("No sos el dueño de esta cafetería.")

    if request.method == 'POST':
        review.owner_reply = request.POST.get('reply')
        review.save()
        key = make_template_fragment_key("cafe_reviews_list", [review.cafe_id])
        cache.delete(key)
        messages.success(request, "Respuesta del dueño actualizada correctamente.")

    return redirect('reviews:owner_reviews')


def nearby_cafes(request):
    try:
        lat = float(request.GET.get('lat'))
        lon = float(request.GET.get('lon'))
    except (TypeError, ValueError):
        return JsonResponse({'error': 'Coordenadas inválidas'}, status=400)

    def haversine(lat1, lon1, lat2, lon2):
        from math import radians, sin, cos, asin, sqrt
        R = 6371.0
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a))
        return R * c

    cafes = Cafe.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True)
    cafes_con_distancia = []

    for cafe in cafes:
        distancia = haversine(lat, lon, cafe.latitude, cafe.longitude)
        cafes_con_distancia.append((cafe, distancia))

    cafes_ordenados = sorted(cafes_con_distancia, key=lambda x: x[1])[:10]

    data = [
        {
            'name': c.name,
            'address': c.address,
            'location': c.location,
            'distance_km': round(dist, 2),
            'url': reverse('reviews:cafe_detail', kwargs={'cafe_id': c.id}),
        }
        for c, dist in cafes_ordenados
    ]

    return JsonResponse(data, safe=False)


def asignar_plan(cafe, nivel: int):
    if nivel == 0:
        cafe.visibility_level = 0
        cafe.save(update_fields=["visibility_level"])
        return True
    return False


@login_required
def cambiar_visibilidad(request, cafe_id):
    cafe = get_object_or_404(Cafe, id=cafe_id)

    if request.user != cafe.owner:
        return HttpResponseForbidden("No tenés permiso para editar este café.")

    if request.method == 'POST':
        try:
            nuevo_nivel = int(request.POST.get('visibility_level'))
        except (TypeError, ValueError):
            messages.error(request, "Nivel inválido.")
            return redirect('reviews:owner_dashboard')

        if nuevo_nivel == 0:
            asignar_plan(cafe, 0)
            messages.success(request, "Se activó el plan gratuito.")
            return redirect('reviews:owner_dashboard')

        link = getattr(settings, "PAYMENT_LINKS", {}).get(nuevo_nivel)
        if not getattr(settings, "PLAN_UPGRADES_ENABLED", False) or not link:
            messages.info(request, "Los planes pagos todavía no están disponibles. Te avisamos pronto.")
            return redirect('reviews:planes')

        return redirect(f"{link}?cafe={cafe.id}&user={request.user.id}")

    return redirect('reviews:owner_dashboard')


@login_required
def plan_checkout_redirect(request, cafe_id, nivel):
    cafe = get_object_or_404(Cafe, id=cafe_id, owner=request.user)
    try:
        nivel = int(nivel)
    except (TypeError, ValueError):
        messages.error(request, "Nivel inválido.")
        return redirect('reviews:planes')

    if nivel == 0:
        messages.info(request, "El plan gratuito ya está activo.")
        return redirect('reviews:planes')

    link = getattr(settings, "PAYMENT_LINKS", {}).get(nivel)
    if not getattr(settings, "PLAN_UPGRADES_ENABLED", False) or not link:
        messages.info(request, "Los planes pagos estarán disponibles pronto.")
        return redirect('reviews:planes')

    return redirect(f"{link}?cafe={cafe.id}&user={request.user.id}")


@login_required
def planes_view(request):
    if not request.user.is_owner:
        raise PermissionDenied("Solo los dueños pueden ver los planes.")

    if request.method == 'POST':
        cafe_id = request.POST.get('cafe_id')
        nivel = request.POST.get('nivel')
        cafe = get_object_or_404(Cafe, id=cafe_id, owner=request.user)

        try:
            nivel = int(nivel)
        except (TypeError, ValueError):
            messages.error(request, "Nivel inválido.")
            return redirect('reviews:planes')

        if nivel == 0:
            asignar_plan(cafe, 0)
            messages.success(request, "Plan gratuito activado.")
            return redirect('reviews:planes')

        return redirect('reviews:plan_checkout_redirect', cafe_id=cafe.id, nivel=nivel)

    cafes = Cafe.objects.filter(owner=request.user)
    return render(request, 'reviews/planes.html', {
        'cafes': cafes,
        'upgrades_enabled': getattr(settings, "PLAN_UPGRADES_ENABLED", False),
    })


def mapa_cafes(request):
    cafes_qs = Cafe.objects.exclude(latitude__isnull=True, longitude__isnull=True)

    BOOL_FIELDS = [
        "is_pet_friendly", "has_wifi", "has_outdoor_seating", "is_vegan_friendly",
        "has_parking", "is_accessible", "has_vegetarian_options", "serves_breakfast",
        "serves_alcohol", "has_books_or_games", "has_air_conditioning",
        "has_gluten_free", "has_specialty_coffee", "has_artisanal_pastries",
    ]

    cafes_data = []
    for c in cafes_qs:
        item = {
            "id": c.id,
            "name": c.name,
            "latitude": float(c.latitude) if c.latitude is not None else None,
            "longitude": float(c.longitude) if c.longitude is not None else None,
            "address": c.address,
            "location": c.location,
            "url": reverse("reviews:cafe_detail", kwargs={"cafe_id": c.id}),
        }
        for f in BOOL_FIELDS:
            item[f] = bool(getattr(c, f, False))
        cafes_data.append(item)

    return render(
        request,
        "reviews/mapa_cafes.html",
        {"cafes_json": json.dumps(cafes_data, cls=DjangoJSONEncoder)},
    )


@login_required
def analytics_dashboard(request):
    if not request.user.is_owner:
        raise PermissionDenied("Solo los dueños pueden ver analíticas.")

    cafes_owner = Cafe.objects.filter(owner=request.user).order_by("name")
    if not cafes_owner.exists():
        return render(request, "reviews/analytics_dashboard.html", {
            "cafes": cafes_owner, "cafe": None,
            "labels_json": "[]", "views_json": "[]",
            "totals": {"views": 0, "favorites": 0, "reviews": 0},
        })

    selected_id = request.GET.get("cafe")
    if selected_id:
        cafe = get_object_or_404(Cafe, id=selected_id, owner=request.user)
    else:
        cafe = cafes_owner.first()

    totals = {
        "views": CafeStat.objects.filter(cafe=cafe).aggregate(s=Sum("views"))["s"] or 0,
        "favorites": cafe.favorites.count(),
        "reviews": cafe.reviews.count(),
    }

    today = timezone.localdate()
    start = today - timedelta(days=29)
    qs = (
        CafeStat.objects.filter(cafe=cafe, date__range=[start, today])
        .values("date").annotate(v=Sum("views"))
    )
    by_date = {row["date"]: (row["v"] or 0) for row in qs}

    labels, values = [], []
    for i in range(30):
        d = start + timedelta(days=i)
        labels.append(d.strftime("%d/%m"))
        values.append(by_date.get(d, 0))

    context = {
        "cafes": cafes_owner,
        "cafe": cafe,
        "totals": totals,
        "labels_json": json.dumps(labels),
        "views_json": json.dumps(values),
    }
    return render(request, "reviews/analytics_dashboard.html", context)


@require_POST
@login_required
def toggle_review_like(request, review_id):
    review = get_object_or_404(Review, pk=review_id)

    obj, created = ReviewLike.objects.get_or_create(review=review, user=request.user)
    if not created:
        obj.delete()
        liked = False
    else:
        liked = True

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        count = ReviewLike.objects.filter(review=review).count()
        return JsonResponse({"ok": True, "liked": liked, "count": count})

    return redirect("reviews:cafe_detail", cafe_id=review.cafe_id)


@login_required
def report_review(request, review_id):
    review = get_object_or_404(Review, pk=review_id)

    if request.method == "POST":
        form = ReviewReportForm(request.POST)
        if form.is_valid():
            pending_exists = ReviewReport.objects.filter(
                review=review, user=request.user, status=ReviewReport.Status.PENDING
            ).exists()
            if pending_exists:
                messages.info(request, "Ya enviaste un reporte para esta reseña. Está en revisión.")
                return redirect("reviews:cafe_detail", cafe_id=review.cafe_id)

            rep = form.save(commit=False)
            rep.review = review
            rep.user = request.user
            rep.save()
            messages.success(request, "¡Gracias! Recibimos tu denuncia y la revisaremos.")
            return redirect("reviews:cafe_detail", cafe_id=review.cafe_id)
    else:
        form = ReviewReportForm()

    return render(
        request,
        "reviews/reports/report_form.html",
        {"review": review, "form": form}
    )

@staff_member_required
def founder_analytics(request):
    today = timezone.localdate()

    range_param = request.GET.get("range")
    date_from = request.GET.get("from")
    date_to = request.GET.get("to")

    if range_param == "7":
        start_date = today - timedelta(days=6)
        end_date = today
    elif range_param == "30":
        start_date = today - timedelta(days=29)
        end_date = today
    elif date_from and date_to:
        try:
            start_date = datetime.fromisoformat(date_from).date()
            end_date = datetime.fromisoformat(date_to).date()
        except ValueError:
            start_date = None
            end_date = None
    else:
        start_date = None
        end_date = None

    cafes = Cafe.objects.select_related("owner")

    if start_date and end_date:
        cafes = cafes.annotate(
            total_views=Sum(
                "stats__views",
                filter=Q(stats__date__range=(start_date, end_date))
            )
        )
    else:
        cafes = cafes.annotate(
            total_views=Sum("stats__views")
        )

    cafes = cafes.annotate(
        total_reviews=Count("reviews", distinct=True),
        total_favorites=Count("favorites", distinct=True),
        avg_rating=Avg("reviews__rating"),
    ).order_by(F("total_views").desc(nulls_last=True))
    # === TOTALES GLOBALES (KPIs) ===
    ratings = [c.avg_rating for c in cafes if c.avg_rating]

    totals = {
        "views": sum(c.total_views or 0 for c in cafes),
        "reviews": sum(c.total_reviews or 0 for c in cafes),
        "favorites": sum(c.total_favorites or 0 for c in cafes),
        "avg_rating": round(sum(ratings) / len(ratings), 2) if ratings else None,
    }

    # === TOP CAFÉS POR VISITAS ===
    top_cafes = (
        cafes
        .filter(total_views__gt=0)
        .order_by("-total_views")[:5]
    )

    # === EVOLUCIÓN DIARIA DE VISITAS (GLOBAL) ===
    stats_qs = CafeStat.objects.filter(
        cafe__in=cafes.values_list("id", flat=True)
    )
    if start_date and end_date:
        stats_qs = stats_qs.filter(date__range=(start_date, end_date))

    daily = (
        stats_qs
        .values("date")
        .annotate(total=Sum("views"))
        .order_by("date")
    )

    labels = [d["date"].strftime("%d/%m") for d in daily]
    values = [d["total"] or 0 for d in daily]

    export = request.GET.get("export")

    if export == "excel":
        return export_founder_excel(cafes)

    return render(
        request,
        "reviews/founder_analytics.html",
        {
            "cafes": cafes,
            "top_cafes": top_cafes,
            "totals": totals,
            "labels": labels,
            "values": values,
            "range": range_param,
            "from": date_from,
            "to": date_to,
        }
    )


def export_founder_excel(cafes):
    wb = Workbook()
    ws = wb.active
    ws.title = "Founder Analytics"

    headers = [
        "Café",
        "Dueño",
        "Email dueño",
        "Zona",
        "Plan",
        "Visitas",
        "Reviews",
        "Favoritos",
        "Rating promedio",
        "Creado",
    ]
    ws.append(headers)

    PLAN_MAP = {
        0: "Gratis",
        1: "Destacado",
        2: "Premium",
    }

    for c in cafes:
        ws.append([
            c.name,
            c.owner.get_full_name() or c.owner.email,
            c.owner.email,
            c.location,
            PLAN_MAP.get(c.visibility_level),
            c.total_views or 0,
            c.total_reviews,
            c.total_favorites,
            round(c.avg_rating, 1) if c.avg_rating else "",
            c.created_at.strftime("%Y-%m-%d"),
        ])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="gota_founder_analytics.xlsx"'

    wb.save(response)
    return response
