# reviews/api.py
from django.db.models import Avg, Count
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
from reviews.utils.ranking import calcular_score_cafe
from rest_framework.response import Response


class CafeViewSet(ReadOnlyModelViewSet):
    """
    Endpoints:
    - GET /api/cafes/       -> lista
    - GET /api/cafes/{id}/  -> detalle
    """
    permission_classes = [AllowAny]  # Público en desarrollo
    serializer_class = CafeSerializer

    def get_queryset(self):
        return (
            Cafe.objects
            .select_related("owner")
            .prefetch_related(
                "tags",
                "relationships",
            )
            .annotate(
                average_rating=Avg("reviews__rating"),
                total_reviews=Count("reviews"),
            )
        )

    # Anotamos el promedio de rating tomando el related_name 'reviews'
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(
            self.get_queryset()
        )

        ordering = request.query_params.get("ordering")
        search = request.query_params.get("search")

        if not ordering and not search:
            cafes = list(queryset)

            lat = request.query_params.get("lat")
            lon = request.query_params.get("lon")

            try:
                user_lat = float(lat) if lat else None
                user_lon = float(lon) if lon else None
            except (TypeError, ValueError):
                user_lat = None
                user_lon = None

            for cafe in cafes:
                cafe.score = calcular_score_cafe(
                    cafe,
                    user=(
                        request.user
                        if request.user.is_authenticated
                        else None
                    ),
                    user_lat=user_lat,
                    user_lon=user_lon,
                    cafes_vistos_ids=[],
                )

            cafes.sort(
                key=lambda cafe: cafe.score,
                reverse=True,
            )

            serializer = self.get_serializer(
                cafes,
                many=True,
            )

            return Response(serializer.data)

        serializer = self.get_serializer(
            queryset,
            many=True,
        )

        return Response(serializer.data)

    # Búsqueda & orden (opcional, ya mismo te suma valor)
    filter_backends = [SearchFilter, OrderingFilter] + ([DjangoFilterBackend] if HAS_DJANGO_FILTER else [])
    search_fields = ["name", "address", "location"]
    ordering_fields = ["name", "average_rating", "created_at"]

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
