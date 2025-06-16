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
import os
from django.core.paginator import Paginator
from .models import Tag
from django.http import JsonResponse
from math import radians, cos, sin, asin, sqrt


# Listar reseñas agrupadas por zona
def review_list(request):
    all_reviews = Review.objects.select_related('cafe', 'user').order_by('-created_at')
    reseñas_por_zona = defaultdict(list)

    for review in all_reviews:
        zona = review.cafe.location or 'Sin zona'
        reseñas_por_zona[zona].append(review)

    return render(request, 'reviews/review_list.html', {
        'reseñas_por_zona': dict(reseñas_por_zona)
    })

# Versión class-based no utilizada
class ReviewListView(ListView):
    model = Review
    template_name = 'reviews/review_list.html'
    context_object_name = 'reviews'

# Listar cafeterías con filtros
def cafe_list(request):
    zona = request.GET.get('zona')
    orden = request.GET.get('orden')

    filtros = {
        'is_vegan_friendly': request.GET.get('vegan') == 'on',
        'is_pet_friendly': request.GET.get('pet') == 'on',
        'has_wifi': request.GET.get('wifi') == 'on',
        'has_outdoor_seating': request.GET.get('outdoor') == 'on',
    }

    todos_los_tags = Tag.objects.all()
    tags_seleccionados = request.GET.getlist('tags')

    if tags_seleccionados:
        cafes = cafes.filter(tags__id__in=tags_seleccionados).distinct()

    cafes = Cafe.objects.all()

    if zona:
        cafes = cafes.filter(location=zona)

    for key, value in filtros.items():
        if value:
            cafes = cafes.filter(**{key: True})

    cafes = cafes.annotate(
        average_rating=Avg('reviews__rating'),
        total_reviews=Count('reviews')
    )

    if orden == 'rating':
        cafes = cafes.order_by('-average_rating')
    elif orden == 'reviews':
        cafes = cafes.order_by('-total_reviews')
    else:
        cafes = cafes.order_by('name')

    zonas_disponibles = Cafe.objects.values_list('location', flat=True).distinct().order_by('location')

    return render(request, 'reviews/cafe_list.html', {
        'cafes': cafes,
        'zonas_disponibles': zonas_disponibles,
        'zona_seleccionada': zona,
        'orden_actual': orden,
        'filtros_aplicados': filtros,
        'tags': todos_los_tags,
        'tags_seleccionados': [int(t) for t in tags_seleccionados],
})


# Detalle de cafetería + dejar o editar reseña
def cafe_detail(request, cafe_id):
    cafe = get_object_or_404(Cafe, pk=cafe_id)
    reviews = Review.objects.filter(cafe=cafe).order_by('-created_at')
    average_rating = reviews.aggregate(Avg('rating'))['rating__avg']

    existing_review = None
    if request.user.is_authenticated:
        try:
            existing_review = Review.objects.get(cafe=cafe, user=request.user)
        except Review.DoesNotExist:
            pass

    if request.method == 'POST' and request.user.is_authenticated:
        form = ReviewForm(request.POST, instance=existing_review)
        if form.is_valid():
            review = form.save(commit=False)
            review.cafe = cafe
            review.user = request.user
            review.location = cafe.location
            review.save()
            messages.success(request, "¡Gracias por tu reseña!")
            return redirect('cafe_detail', cafe_id=cafe.id)
    else:
        form = ReviewForm(instance=existing_review)

    best_review = reviews.order_by('-rating', '-created_at').first()

    return render(request, 'reviews/cafe_detail.html', {
        'cafe': cafe,
        'reviews': reviews,
        'form': form,
        'existing_review': existing_review,
        'average_rating': average_rating,
        'best_review': best_review,
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
        reviews = cafe.reviews.select_related('user').order_by('-created_at')
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
    cafe = get_object_or_404(Cafe, id=cafe_id, owner=request.user)

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
def toggle_favorite(request, cafe_id):
    cafe = get_object_or_404(Cafe, id=cafe_id)

    if request.user in cafe.favorites.all():
        cafe.favorites.remove(request.user)
        messages.info(request, f'{cafe.name} eliminado de favoritos.')
    else:
        cafe.favorites.add(request.user)
        messages.success(request, f'{cafe.name} agregado a favoritos.')

    return redirect('cafe_detail', cafe_id=cafe.id)

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