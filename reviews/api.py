# reviews/api.py
from django.db.models import Avg
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.permissions import AllowAny
from rest_framework.filters import SearchFilter, OrderingFilter
try:
    # Si tenés django-filter instalado, habilitamos filtros. Si no, lo ignoramos.
    from django_filters.rest_framework import DjangoFilterBackend
    HAS_DJANGO_FILTER = True
except Exception:
    HAS_DJANGO_FILTER = False

from reviews.models import Cafe
from .serializers import CafeSerializer


class CafeViewSet(ReadOnlyModelViewSet):
    """
    Endpoints:
    - GET /api/cafes/       -> lista
    - GET /api/cafes/{id}/  -> detalle
    """
    permission_classes = [AllowAny]  # Público en desarrollo
    serializer_class = CafeSerializer

    # Anotamos el promedio de rating tomando el related_name 'reviews'
    def get_queryset(self):
        return (
            Cafe.objects
            .select_related("owner")           # opcional, por si se usa en el serializer
            .prefetch_related("tags")          # para evitar N+1
            .annotate(average_rating=Avg("reviews__rating"))
            .order_by("name")
        )

    # Búsqueda & orden (opcional, ya mismo te suma valor)
    filter_backends = [SearchFilter, OrderingFilter] + ([DjangoFilterBackend] if HAS_DJANGO_FILTER else [])
    search_fields = ["name", "address", "location"]
    ordering_fields = ["name", "average_rating", "created_at"]
    ordering = ["name"]

    # Si tenés django-filter, podés habilitar filtros booleanos básicos:
    if HAS_DJANGO_FILTER:
        from django_filters import rest_framework as filters
        class CafeFilter(filters.FilterSet):
            class Meta:
                model = Cafe
                fields = {
                    "has_wifi": ["exact"],
                    "is_pet_friendly": ["exact"],
                    "is_vegan_friendly": ["exact"],
                    "location": ["exact", "icontains"],
                    "visibility_level": ["exact"],
                }
        filterset_class = CafeFilter
