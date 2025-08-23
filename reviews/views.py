from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg, Count, F, Q
from django.views.generic import ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.core.exceptions import PermissionDenied
from collections import defaultdict
from .models import Review, Cafe
from .forms import ReviewForm, CafeForm
import os, json, math
from django.core.paginator import Paginator
from .models import Tag
from django.http import JsonResponse
from math import radians, cos, sin, asin, sqrt
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponseForbidden
from reviews.utils.geo import haversine_distance
from statistics import mean
from reviews.utils.tags import get_tags_grouped_by_cafe
from core.messages import MESSAGES
from django.urls import reverse
from django.templatetags.static import static

# ✅ imports para invalidar el caché de fragmentos
from django.core.cache.utils import make_template_fragment_key
from django.core.cache import cache


# Listar reseñas agrupadas por zona
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

        # Zonas y orden
        context['zonas_disponibles'] = (
            Cafe.objects.values_list('location', flat=True)
            .distinct()
            .order_by('location')
        )
        context['zona_seleccionada'] = request.GET.get('zona')
        context['orden_actual'] = request.GET.get('orden')

        # ✅ Booleanos (incluye serves_breakfast)
        boolean_keys = [
            'has_wifi', 'has_air_conditioning', 'serves_alcohol', 'is_pet_friendly',
            'is_vegan_friendly', 'has_outdoor_seating', 'has_parking', 'is_accessible',
            'has_vegetarian_options', 'has_books_or_games', 'serves_breakfast', "accepts_cards", "gluten_free_options", "has_baby_changing",
            "has_power_outlets", "laptop_friendly", "quiet_space",
            "specialty_coffee", "brunch", "accepts_reservations",
        ]
        context['campos_activos'] = {k: (request.GET.get(k) == 'on') for k in boolean_keys}

        # Mostrar botón “Ver todos”
        context['mostrar_boton_reset'] = any([
            request.GET.get('zona'),
            request.GET.get('orden'),
            request.GET.get('lat'),
            request.GET.get('lon'),
            *[request.GET.get(k) for k in boolean_keys],
        ])

        # Favoritos del usuario
        if request.user.is_authenticated:
            context['favoritos_ids'] = set(
                request.user.favorite_cafes.values_list('id', flat=True)
            )
        else:
            context['favoritos_ids'] = set()

        # Datos para el mapa (Leaflet) — consulta directa, liviana
        cafes = (
            Cafe.objects
                .only('id', 'name', 'latitude', 'longitude')
                .exclude(latitude__isnull=True)
                .exclude(longitude__isnull=True)
        )
        cafes_data = [
            {
                'id': c.id,
                'name': c.name,
                'latitude': float(c.latitude),
                'longitude': float(c.longitude),
                'url': reverse('cafe_detail', args=[c.id]),
            }
            for c in cafes
        ]
        context['cafes_json'] = json.dumps(cafes_data, cls=DjangoJSONEncoder)

        return context


class CafeListView(ListView):
    model = Cafe
    template_name = 'reviews/cafe_list.html'
    context_object_name = 'cafes'
    paginate_by = 12  # ✅ paginación

    def get_queryset(self):
        request = self.request
        zona = request.GET.get('zona')
        orden = request.GET.get('orden')
        lat = request.GET.get('lat')
        lon = request.GET.get('lon')

        filtros = {
            'is_vegan_friendly': request.GET.get('vegan') == 'on',
            'is_pet_friendly': request.GET.get('pet') == 'on',
            'has_wifi': request.GET.get('wifi') == 'on',
            'has_outdoor_seating': request.GET.get('outdoor') == 'on',
            'has_parking': request.GET.get('has_parking') == 'on',
            'is_accessible': request.GET.get('is_accessible') == 'on',
            'has_vegetarian_options': request.GET.get('has_vegetarian_options') == 'on',
            'serves_breakfast': request.GET.get('serves_breakfast') == 'on',
            'serves_alcohol': request.GET.get('serves_alcohol') == 'on',
            'has_books_or_games': request.GET.get('has_books_or_games') == 'on',
            'has_air_conditioning': request.GET.get('has_air_conditioning') == 'on',
            "accepts_cards": request.GET.get("accepts_cards") == "on",
            "gluten_free_options": request.GET.get("gluten_free_options") == "on",
            "has_baby_changing": request.GET.get("has_baby_changing") == "on",
            "has_power_outlets": request.GET.get("has_power_outlets") == "on",
            "laptop_friendly": request.GET.get("laptop_friendly") == "on",
            "quiet_space": request.GET.get("quiet_space") == "on",
            "specialty_coffee": request.GET.get("specialty_coffee") == "on",
            "brunch": request.GET.get("brunch") == "on",
            "accepts_reservations": request.GET.get("accepts_reservations") == "on",
            }

        cafes = Cafe.objects.all()

        if zona:
            cafes = cafes.filter(location=zona)

        for key, value in filtros.items():
            if value:
                cafes = cafes.filter(**{key: True})

        cafes = cafes.annotate(
            average_rating=Avg('reviews__rating'),
            total_reviews=Count('reviews')
        ).prefetch_related('favorites')

        if orden == 'rating':
            cafes = cafes.order_by('-average_rating')
        elif orden == 'reviews':
            cafes = cafes.order_by('-total_reviews')
        elif orden == 'algoritmo':
            cafes = list(cafes)
            for cafe in cafes:
                rating = cafe.average_rating or 0
                reviews = cafe.total_reviews or 0
                fotos = sum(bool(getattr(cafe, f'photo{i}')) for i in range(1, 4))
                favs = cafe.favorites.count()
                caracteristicas_count = sum([
                    cafe.is_vegan_friendly,
                    cafe.is_pet_friendly,
                    cafe.has_wifi,
                    cafe.has_outdoor_seating,
                    cafe.has_parking,
                    cafe.is_accessible,
                    cafe.has_vegetarian_options,
                    cafe.serves_breakfast,
                    cafe.serves_alcohol,
                    cafe.has_books_or_games,
                    cafe.has_air_conditioning
                ])
                score_base = (
                    rating * 2 +
                    reviews * 0.7 +
                    fotos * 1 +
                    favs * 0.6 +
                    caracteristicas_count * 0.3
                )
                if cafe.visibility_level == 1:
                    cafe.score = score_base * 1.10
                elif cafe.visibility_level == 2:
                    cafe.score = score_base * 1.20
                else:
                    cafe.score = score_base
            cafes.sort(key=lambda c: c.score, reverse=True)
        else:
            cafes = cafes.order_by('name')

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

        # ⛔️ OJO: ListView paginará si cafes es QuerySet; si lo convertiste a list() (algoritmo),
        # igual funciona, pero la paginación es en memoria. Aceptable por ahora.
        self._cafes_finales = cafes
        return cafes

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request = self.request

        context['zonas_disponibles'] = (
            Cafe.objects.values_list('location', flat=True)
            .distinct()
            .order_by('location')
        )
        context['zona_seleccionada'] = request.GET.get('zona')
        context['orden_actual'] = request.GET.get('orden')

        boolean_keys = [
            'has_wifi', 'has_air_conditioning', 'serves_alcohol', 'is_pet_friendly',
            'is_vegan_friendly', 'has_outdoor_seating', 'has_parking', 'is_accessible',
            'has_vegetarian_options', 'has_books_or_games', "accepts_cards", "gluten_free_options", "has_baby_changing",
            "has_power_outlets", "laptop_friendly", "quiet_space",
            "specialty_coffee", "brunch", "accepts_reservations",
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

        cafes = context.get('cafes', [])
        cafes_data = []
        for c in cafes:
            cafes_data.append({
                'id': c.id,
                'name': c.name,
                'latitude': float(c.latitude) if c.latitude is not None else None,
                'longitude': float(c.longitude) if c.longitude is not None else None,
                'url': reverse('cafe_detail', args=[c.id]),
            })
        context['cafes_json'] = json.dumps(cafes_data, cls=DjangoJSONEncoder)

        return context




# Detalle de cafetería + dejar o editar reseña
def cafe_detail(request, cafe_id):
    cafe = get_object_or_404(Cafe, id=cafe_id)
    reviews = cafe.reviews.select_related("user").prefetch_related("tags").order_by("-created_at")

    # Calcular promedio y mejor reseña
    ratings = [r.rating for r in reviews]
    average_rating = round(mean(ratings), 1) if ratings else None
    best_review = reviews[0] if reviews else None

    # Guardar "visto recientemente"
    viewed = request.session.get("recently_viewed", [])
    if cafe.id in viewed:
        viewed.remove(cafe.id)
    viewed.insert(0, cafe.id)
    request.session["recently_viewed"] = viewed[:5]

    # Preparar formulario (sin manejar POST acá)
    if request.user.is_authenticated:
        try:
            existing_review = Review.objects.get(user=request.user, cafe=cafe)
            form = ReviewForm(instance=existing_review)
        except Review.DoesNotExist:
            form = ReviewForm()
    else:
        form = ReviewForm()

    # Agrupar TODAS las etiquetas por categoría (para el wizard de reseña)
    all_tags = Tag.objects.all().order_by("category", "name")
    tag_groups = defaultdict(list)
    for tag in all_tags:
        tag_groups[tag.category].append(tag)

    # === Etiquetas sensoriales ordenadas por uso en reseñas de ESTE café ===
    tag_counts_qs = (
        Tag.objects
        .filter(reviews__cafe=cafe)
        .annotate(num=Count('reviews', filter=Q(reviews__cafe=cafe)))
        .order_by('-num', 'name')
    )
    top_tags = list(tag_counts_qs[:5])   # Top 5 destacadas
    more_tags = list(tag_counts_qs[5:])  # El resto (para "ver más")

    # Recomendados por calificación
    recommended_cafes = (
        Cafe.objects.annotate(average_rating=Avg("reviews__rating"))
        .filter(average_rating__isnull=False)
        .exclude(id=cafe.id)
        .order_by("-average_rating")[:4]
    )

    # URLs absolutas para SEO/OG
    full_page_url = request.build_absolute_uri(reverse("cafe_detail", args=[cafe.id]))

    # Elegimos la mejor imagen disponible o fallback
    if getattr(cafe, "photo1", None):
        og_image_path = cafe.photo1.url
    elif getattr(cafe, "photo2", None):
        og_image_path = cafe.photo2.url
    elif getattr(cafe, "photo3", None):
        og_image_path = cafe.photo3.url
    else:
        og_image_path = static("images/og-default.jpg")

    full_image_url = request.build_absolute_uri(og_image_path)

    return render(request, "reviews/cafe_detail.html", {
        "cafe": cafe,
        "reviews": reviews,
        "average_rating": average_rating,
        "best_review": best_review,
        "form": form,
        "recommended_cafes": recommended_cafes,
        "tag_choices": dict(tag_groups),

        
        "top_tags": top_tags,
        "more_tags": more_tags,

        "full_page_url": full_page_url,
        "full_image_url": full_image_url,
    })




@login_required
def create_review(request, cafe_id):
    cafe = get_object_or_404(Cafe, pk=cafe_id)

    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.cafe = cafe
            review.user = request.user
            review.save()

            # Guardar etiquetas seleccionadas (tags desde checkboxes)
            selected_tag_ids = request.POST.getlist("tags")
            tags = Tag.objects.filter(id__in=selected_tag_ids)
            review.tags.set(tags)

            # 🧹 invalidar caché del listado de reseñas
            key = make_template_fragment_key("cafe_reviews_list", [cafe.id])
            cache.delete(key)

            messages.success(request, MESSAGES["review_sent"])
            return redirect("cafe_detail", cafe_id=cafe.id)
        else:
            messages.error(request, "Por favor corregí los errores.")
    else:
        form = ReviewForm()

    # Agrupar etiquetas por categoría → mismo formato que cafe_detail
    all_tags = Tag.objects.all().order_by("category", "name")
    tag_groups = defaultdict(list)
    for tag in all_tags:
        tag_groups[tag.category].append(tag)

    context = {
        "form": form,
        "cafe": cafe,
        "tag_choices": dict(tag_groups),  # <- clave usada en review_wizard_step2.html
    }

    return render(request, "reviews/create_review.html", context)

@login_required
def edit_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)

    # Solo el autor (o staff) puede editar
    if request.user != review.user and not request.user.is_staff:
        raise PermissionDenied("No podés editar esta reseña.")

    if request.method == "POST":
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()

            # Si usás checkboxes fuera del M2M del form:
            if "tags" in request.POST:
                selected_tag_ids = request.POST.getlist("tags")
                tags = Tag.objects.filter(id__in=selected_tag_ids)
                review.tags.set(tags)

            # 🧹 invalidar caché del listado de reseñas
            key = make_template_fragment_key("cafe_reviews_list", [review.cafe_id])
            cache.delete(key)

            messages.success(request, "Reseña actualizada correctamente.")
            return redirect("cafe_detail", cafe_id=review.cafe_id)
        else:
            messages.error(request, "Por favor corregí los errores.")
    else:
        form = ReviewForm(instance=review)

    # Necesitamos las categorías de tags como en create_review
    all_tags = Tag.objects.all().order_by("category", "name")
    tag_groups = defaultdict(list)
    for tag in all_tags:
        tag_groups[tag.category].append(tag)

    return render(
        request,
        "reviews/create_review.html",  # reutilizamos el mismo template
        {"form": form, "cafe": review.cafe, "tag_choices": dict(tag_groups), "editing": True},
    )


@login_required
def delete_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)

    # Solo el autor (o staff) puede eliminar
    if request.user != review.user and not request.user.is_staff:
        raise PermissionDenied("No podés eliminar esta reseña.")

    cafe_id = review.cafe_id

    if request.method == "POST":
        review.delete()

        # 🧹 invalidar caché del listado de reseñas
        key = make_template_fragment_key("cafe_reviews_list", [cafe_id])
        cache.delete(key)

        messages.success(request, "Reseña eliminada.")
        return redirect("cafe_detail", cafe_id=cafe_id)

    # Pantalla simple de confirmación
    return render(request, "reviews/delete_review.html", {"review": review, "cafe": review.cafe})


# Responder a una reseña (dueño)
@login_required
def reply_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)

    if request.user != review.cafe.owner:
        raise PermissionDenied("No sos el dueño de esta cafetería.")

    if request.method == 'POST':
        review.owner_reply = request.POST.get('reply')
        review.save()

        # 🧹 invalidar caché del listado de reseñas
        key = make_template_fragment_key("cafe_reviews_list", [review.cafe_id])
        cache.delete(key)

        messages.success(request, "Respuesta guardada con éxito.")
        return redirect('cafe_detail', cafe_id=review.cafe.id)

# Crear reseña
class ReviewCreateView(LoginRequiredMixin, CreateView):
    model = Review
    form_class = ReviewForm
    template_name = 'reviews/create_review.html'
    success_url = reverse_lazy('review_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from reviews.models import Tag
        from collections import defaultdict

        # Agrupar etiquetas por categoría
        tag_choices = defaultdict(list)
        for tag in Tag.objects.all():
            tag_choices[tag.category].append(tag)

        context['tag_choices'] = dict(tag_choices)
        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)

        # Asignar las etiquetas desde el formulario
        tags = form.cleaned_data.get('tags')
        if tags:
            self.object.tags.set(tags)

        # 🧹 invalidar caché del listado de reseñas (si tiene café asociado)
        if getattr(self.object, "cafe_id", None):
            key = make_template_fragment_key("cafe_reviews_list", [self.object.cafe_id])
            cache.delete(key)

        return response


# Panel del dueño de cafeterías
@login_required
def owner_dashboard(request):
    owner = request.user
    cafes = Cafe.objects.filter(owner=owner).prefetch_related('reviews__tags')

    # Chequear si no tiene cafés
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

    context = {
        'cafes': cafes,
        'no_cafes': no_cafes  # <-- AGREGADO
    }
    return render(request, 'reviews/owner_dashboard.html', context)


# Vista nueva: reseñas agrupadas por cafetería del dueño
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

# Crear cafetería
class CreateCafeView(LoginRequiredMixin, CreateView):
    model = Cafe
    form_class = CafeForm
    template_name = 'reviews/create_cafe.html'
    success_url = reverse_lazy('cafe_list')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_owner:
            raise PermissionDenied("Solo los dueños de cafeterías pueden agregar una.")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.owner = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, MESSAGES["cafe_added"])
        return response

# Editar cafetería
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
            return redirect('owner_dashboard')
    else:
        form = CafeForm(instance=cafe)

    return render(request, 'reviews/edit_cafe.html', {'form': form, 'cafe': cafe})

# Eliminar cafetería y sus fotos
@login_required
def delete_cafe(request, cafe_id):
    cafe = get_object_or_404(Cafe, id=cafe_id, owner=request.user)

    if request.method == 'POST':
        fotos = [cafe.photo1, cafe.photo2, cafe.photo3]
        cafe.delete()
        for foto in fotos:
            if foto and os.path.isfile(foto.path):
                os.remove(foto.path)

        messages.success(request, "Cafetería eliminada junto con sus fotos y reseñas.")
        return redirect('owner_dashboard')

    return render(request, 'reviews/delete_cafe.html', {'cafe': cafe})

# Subir fotos
@login_required
def upload_photos(request, cafe_id):
    cafe = get_object_or_404(Cafe, pk=cafe_id)

    if request.method == 'POST':
        form = CafeForm(request.POST, request.FILES, instance=cafe)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fotos actualizadas correctamente.')
            return redirect('cafe_detail', cafe_id=cafe.id)
    else:
        form = CafeForm(instance=cafe)

    return render(request, 'reviews/upload_photos.html', {
        'form': form,
        'cafe': cafe
    })


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

    # Agregamos la última reseña a cada café
    for cafe in cafes:
        cafe.last_review = cafe.reviews.order_by('-created_at').first()

    # Para dropdown de zonas
    zonas_disponibles = Cafe.objects.filter(favorites=request.user).values_list('location', flat=True).distinct()

    # 🔄 Paginación
    paginator = Paginator(cafes, 6)  # 6 cafés por página
    pagina = request.GET.get('page')
    cafes_paginados = paginator.get_page(pagina)

    return render(request, 'reviews/favorite_cafes.html', {
        'cafes': cafes_paginados,
        'orden_actual': orden,
        'zona_actual': zona,
        'zonas_disponibles': zonas_disponibles
    })


@login_required
def toggle_favorite(request, cafe_id):
    cafe = get_object_or_404(Cafe, id=cafe_id)

    if request.user in cafe.favorites.all():
        cafe.favorites.remove(request.user)
        messages.info(request, f"{cafe.name} eliminado de favoritos.")
    else:
        cafe.favorites.add(request.user)
        messages.success(request, f"{cafe.name} agregado a favoritos. ❤️")

    return redirect(request.META.get('HTTP_REFERER', 'cafe_list'))


#Editar comentarios del dueño del café
@login_required
def edit_owner_reply(request, review_id):
    review = get_object_or_404(Review, id=review_id)

    if request.user != review.cafe.owner:
        raise PermissionDenied("No sos el dueño de esta cafetería.")

    if request.method == 'POST':
        review.owner_reply = request.POST.get('reply')
        review.save()

        # 🧹 invalidar caché del listado de reseñas
        key = make_template_fragment_key("cafe_reviews_list", [review.cafe_id])
        cache.delete(key)

        messages.success(request, "Respuesta del dueño actualizada correctamente.")

    return redirect('owner_reviews')

def nearby_cafes(request):
    try:
        lat = float(request.GET.get('lat'))
        lon = float(request.GET.get('lon'))
    except (TypeError, ValueError):
        return JsonResponse({'error': 'Coordenadas inválidas'}, status=400)

    def haversine(lat1, lon1, lat2, lon2):
        # Radio de la Tierra en km
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
            'url': reverse('cafe_detail', args=[c.id]),
        }
        for c, dist in cafes_ordenados
    ]

    return JsonResponse(data, safe=False)

# Función reutilizable para asignar plan de visibilidad
def asignar_plan(cafe, nivel):
    if nivel in [0, 1, 2]:
        cafe.visibility_level = nivel
        cafe.save()
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
            if asignar_plan(cafe, nuevo_nivel):
                messages.success(request, "Nivel de visibilidad actualizado.")
            else:
                messages.error(request, "Nivel inválido.")
        except (ValueError, TypeError):
            messages.error(request, "Nivel inválido.")

    return redirect('owner_dashboard')


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
            # TODO: Integrar con pasarela de pago aquí en el futuro
            if asignar_plan(cafe, nivel):
                nombres_planes = {
                    0: "☕ Gratuito – nivel base",
                    1: "☕ Plan Barista – intermedio",
                    2: "☕☕ Plan Maestro – nivel superior"
                }
                messages.success(request, f"{cafe.name} actualizado al plan: {nombres_planes[nivel]}")
            else:
                messages.error(request, "Nivel inválido.")
        except ValueError:
            messages.error(request, "Nivel inválido.")

        return redirect('planes')

    cafes = Cafe.objects.filter(owner=request.user)
    return render(request, 'reviews/planes.html', {'cafes': cafes})

def mapa_cafes(request):
    # Sólo con coordenadas
    cafes_qs = Cafe.objects.exclude(latitude__isnull=True, longitude__isnull=True)

    # Incluir todos los flags que usás en el front
    BOOL_FIELDS = [
        "is_pet_friendly",
        "has_wifi",
        "has_outdoor_seating",
        "is_vegan_friendly",
        "has_parking",
        "is_accessible",
        "has_vegetarian_options",
        "serves_breakfast",
        "serves_alcohol",
        "has_books_or_games",
        "has_air_conditioning",
        # extras opcionales (dejálos si existen en tu modelo)
        "has_gluten_free",
        "has_specialty_coffee",
        "has_artisanal_pastries",
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
            "url": reverse("cafe_detail", args=[c.id]),
        }
        # adjuntar booleanos (si el atributo no existe, False)
        for f in BOOL_FIELDS:
            item[f] = bool(getattr(c, f, False))
        cafes_data.append(item)

    return render(
        request,
        "reviews/mapa_cafes.html",
        {"cafes_json": json.dumps(cafes_data, cls=DjangoJSONEncoder)},
    )