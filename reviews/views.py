from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg
from django.views.generic import ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Review, Cafe
from .forms import ReviewForm, CafeForm
from django.core.exceptions import PermissionDenied

# Listar reseñas
def review_list(request):
    reviews = Review.objects.all().order_by('-created_at')
    return render(request, 'reviews/review_list.html', {'reviews': reviews})

class ReviewListView(ListView):
    model = Review
    template_name = 'reviews/review_list.html'
    context_object_name = 'reviews'

# Listar cafeterías con filtro opcional por zona
def cafe_list(request):
    zona = request.GET.get('zona')
    if zona:
        cafes = Cafe.objects.filter(location=zona).order_by('name')
    else:
        cafes = Cafe.objects.all().order_by('name')

    zonas_disponibles = Cafe.objects.values_list('location', flat=True).distinct().order_by('location')

    return render(request, 'reviews/cafe_list.html', {
        'cafes': cafes,
        'zonas_disponibles': zonas_disponibles,
        'zona_seleccionada': zona
    })

# Crear reseña (usuario logueado)
class ReviewCreateView(LoginRequiredMixin, CreateView):
    model = Review
    form_class = ReviewForm
    template_name = 'reviews/create_review.html'
    success_url = reverse_lazy('review_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

# Ver detalles de una cafetería y dejar o actualizar reseña
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
            review.save()
            if existing_review:
                messages.success(request, 'Tu reseña fue actualizada.')
            else:
                messages.success(request, 'Tu reseña fue creada.')
            return redirect('cafe_detail', cafe_id=cafe.id)
    else:
        form = ReviewForm(instance=existing_review)

    return render(request, 'reviews/cafe_detail.html', {
        'cafe': cafe,
        'reviews': reviews,
        'form': form,
        'existing_review': existing_review,
        'average_rating': average_rating
    })

# Subir fotos para una cafetería (usuario logueado)
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

class CreateCafeView(LoginRequiredMixin, CreateView):
    model = Cafe
    form_class = CafeForm
    template_name = 'reviews/create_cafe.html'
    success_url = reverse_lazy('cafe_list')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_owner:
            raise PermissionDenied("Solo los dueños de cafeterías pueden agregar una.")
        return super().dispatch(request, *args, **kwargs)