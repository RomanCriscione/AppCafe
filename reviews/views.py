from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg, Count
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
        reseñas_por_zona = defaultdict(list)

        for review in context['reviews']:
            zona = review.cafe.location or 'Sin zona'
            reseñas_por_zona[zona].append(review)

        context['reseñas_por_zona'] = dict(reseñas_por_zona)
        return context


class CafeListView(ListView):
    model = Cafe
    template_name = 'reviews/cafe_list.html'
    context_object_name = 'cafes'

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
        }

        cafes = Cafe.objects.all()

        if zona:
            cafes = cafes.filter(location=zona)

        for key, value in filtros.items():
            if value:
                cafes = cafes.filter(**{key: True})

        tags_seleccionados = request.GET.getlist('tags')
        if tags_seleccionados:
            cafes = cafes.filter(tags__id__in=tags_seleccionados).distinct()

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

        # Filtro por ubicación
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

        self._cafes_finales = cafes  # guardar para usar en context
        return cafes

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request = self.request

        context['zonas_disponibles'] = Cafe.objects.values_list('location', flat=True).distinct().order_by('location')
        context['zona_seleccionada'] = request.GET.get('zona')
        context['orden_actual'] = request.GET.get('orden')
        context['filtros_aplicados'] = {
            'vegan': request.GET.get('vegan'),
            'pet': request.GET.get('pet'),
            'wifi': request.GET.get('wifi'),
            'outdoor': request.GET.get('outdoor'),
            'has_parking': request.GET.get('has_parking'),
            'is_accessible': request.GET.get('is_accessible'),
            'has_vegetarian_options': request.GET.get('has_vegetarian_options'),
            'serves_breakfast': request.GET.get('serves_breakfast'),
            'serves_alcohol': request.GET.get('serves_alcohol'),
            'has_books_or_games': request.GET.get('has_books_or_games'),
            'has_air_conditioning': request.GET.get('has_air_conditioning'),
        }
        context['caracteristicas'] = [
            ('vegan', 'Vegano friendly'),
            ('pet', 'Pet friendly'),
            ('wifi', 'WiFi'),
            ('outdoor', 'Mesas afuera'),
            ('has_parking', 'Estacionamiento disponible'),
            ('is_accessible', 'Accesible'),
            ('has_vegetarian_options', 'Opciones vegetarianas'),
            ('serves_breakfast', 'Sirve desayuno'),
            ('serves_alcohol', 'Sirve alcohol'),
            ('has_books_or_games', 'Libros o juegos disponibles'),
            ('has_air_conditioning', 'Aire acondicionado'),
        ]
        context['tags'] = Tag.objects.all()
        context['tags_seleccionados'] = [int(t) for t in self.request.GET.getlist('tags')]

        context['cafes_json'] = json.dumps([
            {
                'id': cafe.id,
                'name': cafe.name,
                'latitude': cafe.latitude,
                'longitude': cafe.longitude,
                'address': cafe.address,
                'url': reverse_lazy('cafe_detail', args=[cafe.id]),
            } for cafe in self._cafes_finales if cafe.latitude and cafe.longitude
        ], cls=DjangoJSONEncoder)

        if request.user.is_authenticated:
            context['favoritos_ids'] = list(request.user.favorite_cafes.values_list('id', flat=True))
        else:
            context['favoritos_ids'] = []

        context['mostrar_boton_reset'] = bool(request.GET.get('lat')) and bool(request.GET.get('lon'))

        return context


# Detalle de cafetería + dejar o editar reseña
def cafe_detail(request, cafe_id):
    cafe = get_object_or_404(Cafe, id=cafe_id)
    reviews = cafe.reviews.select_related("user").order_by("-created_at")

    # Calcular promedio y mejor reseña
    ratings = [review.rating for review in reviews]
    average_rating = round(mean(ratings), 1) if ratings else None
    best_review = reviews[0] if reviews else None

    # 👉 Guardar el café en sesión como "visto recientemente"
    viewed = request.session.get("recently_viewed", [])
    if cafe.id in viewed:
        viewed.remove(cafe.id)
    viewed.insert(0, cafe.id)
    request.session["recently_viewed"] = viewed[:5]

    # Manejo del formulario de reseña
    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid() and request.user.is_authenticated:
            review, created = Review.objects.get_or_create(
                user=request.user,
                cafe=cafe,
                defaults={
                    "comment": form.cleaned_data["comment"],
                    "rating": form.cleaned_data["rating"],
                }
            )
            if not created:
                review.comment = form.cleaned_data["comment"]
                review.rating = form.cleaned_data["rating"]
                review.save()
            messages.success(request, "¡Gracias por tu reseña!")
            return redirect("cafe_detail", cafe_id=cafe.id)
    else:
        if request.user.is_authenticated:
            try:
                existing_review = Review.objects.get(user=request.user, cafe=cafe)
                form = ReviewForm(instance=existing_review)
            except Review.DoesNotExist:
                form = ReviewForm()
        else:
            form = ReviewForm()

    # Obtener cafés recomendados por calificación promedio
    recommended_cafes = Cafe.objects.annotate(
        average_rating=Avg('reviews__rating')
    ).filter(average_rating__isnull=False).exclude(id=cafe.id).order_by('-average_rating')[:4]

    return render(request, "reviews/cafe_detail.html", {
        "cafe": cafe,
        "reviews": reviews,
        "average_rating": average_rating,
        "best_review": best_review,
        "form": form,
        "recommended_cafes": recommended_cafes,
    })

# Responder a una reseña (dueño)
@login_required
def reply_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)

    if request.user != review.cafe.owner:
        raise PermissionDenied("No sos el dueño de esta cafetería.")

    if request.method == 'POST':
        review.owner_reply = request.POST.get('reply')
        review.save()
        messages.success(request, "Respuesta guardada con éxito.")
        return redirect('cafe_detail', cafe_id=review.cafe.id)

# Crear reseña
class ReviewCreateView(LoginRequiredMixin, CreateView):
    model = Review
    form_class = ReviewForm
    template_name = 'reviews/create_review.html'
    success_url = reverse_lazy('review_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

# Panel del dueño de cafeterías
@login_required
def owner_dashboard(request):
    if not request.user.is_owner:
        raise PermissionDenied("Solo los dueños de cafeterías pueden acceder a este panel.")

    cafes = Cafe.objects.filter(owner=request.user).annotate(
        average_rating=Avg('reviews__rating'),
        total_reviews=Count('reviews')
    )

    return render(request, 'reviews/owner_dashboard.html', {
        'cafes': cafes
    })

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
        return super().form_valid(form)

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
    else:
        cafe.favorites.add(request.user)

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
            'url': reverse_lazy('cafe_detail', args=[c.id]),
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
    cafes = Cafe.objects.exclude(latitude__isnull=True, longitude__isnull=True)
    cafes_data = [
        {
            'id': cafe.id,
            'name': cafe.name,
            'latitude': cafe.latitude,
            'longitude': cafe.longitude,
            'address': cafe.address,
            'location': cafe.location,
            'url': reverse_lazy('cafe_detail', args=[cafe.id]),
        }
        for cafe in cafes
    ]
    return render(request, 'reviews/mapa_cafes.html', {
        'cafes_json': json.dumps(cafes_data, cls=DjangoJSONEncoder),
    })
