from django.shortcuts import get_object_or_404

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from reviews.models import Cafe, CafeRelationship
from reviews.serializers import (
    CafeRelationshipSerializer,
    MobileUserSerializer,
)

class CafeDetailAPIView(APIView):
    """
    GET /api/mobile/cafes/<cafe_id>/

    Devuelve el detalle completo de una cafetería.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, cafe_id):
        cafe = get_object_or_404(
            Cafe,
            id=cafe_id,
        )

        fotos = []

        for field_name in [
            "photo1",
            "photo2",
            "photo3",
        ]:
            field = getattr(
                cafe,
                field_name,
                None,
            )

            if field:
                try:
                    fotos.append(
                        request.build_absolute_uri(
                            field.url,
                        )
                    )
                except ValueError:
                    pass

        tags = list(
            cafe.tags.values_list(
                "name",
                flat=True,
            )
        )

        return Response(
            {
                "id": cafe.id,
                "name": cafe.name,
                "location": cafe.location,
                "province": cafe.province,
                "address": cafe.address,
                "description": cafe.description,
                "phone": cafe.phone,
                "google_maps_url": cafe.google_maps_url,
                "instagram": cafe.instagram,
                "average_rating": str(
                    cafe.average_rating()
                ),
                "photos": fotos,
                "latitude": cafe.latitude,
                "longitude": cafe.longitude,
                "has_wifi": cafe.has_wifi,
                "has_air_conditioning":
                    cafe.has_air_conditioning,
                "has_power_outlets":
                    cafe.has_power_outlets,
                "has_outdoor_seating":
                    cafe.has_outdoor_seating,
                "has_parking": cafe.has_parking,
                "is_accessible": cafe.is_accessible,
                "has_baby_changing":
                    cafe.has_baby_changing,
                "is_pet_friendly":
                    cafe.is_pet_friendly,
                "has_specialty_coffee":
                    cafe.has_specialty_coffee,
                "serves_brunch":
                    cafe.serves_brunch,
                "serves_breakfast":
                    cafe.serves_breakfast,
                "serves_alcohol":
                    cafe.serves_alcohol,
                "has_artisanal_pastries":
                    cafe.has_artisanal_pastries,
                "is_vegan_friendly":
                    cafe.is_vegan_friendly,
                "has_vegetarian_options":
                    cafe.has_vegetarian_options,
                "has_gluten_free_options":
                    cafe.has_gluten_free_options,
                "laptop_friendly":
                    cafe.laptop_friendly,
                "quiet_space":
                    cafe.quiet_space,
                "has_books_or_games":
                    cafe.has_books_or_games,
                "tags": tags,
            },
            status=status.HTTP_200_OK,
        )


class MyMapAPIView(generics.ListAPIView):
    """
    GET /api/mobile/my-map/

    Devuelve el recorrido del usuario autenticado.
    """

    serializer_class = CafeRelationshipSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            CafeRelationship.objects
            .filter(user=self.request.user)
            .select_related("cafe")
            .order_by("-updated_at")
        )
    
class SetCafeStatusAPIView(APIView):
    """
    POST /api/mobile/cafes/<cafe_id>/set-status/

    Crea, cambia o elimina el estado de una cafetería
    dentro del mapa del usuario autenticado.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, cafe_id):
        cafe = get_object_or_404(
            Cafe,
            id=cafe_id,
        )

        selected_status = request.data.get(
            "status",
            "",
        )

        valid_statuses = [
            CafeRelationship.WANT_TO_GO,
            CafeRelationship.WANT_TO_RETURN,
            CafeRelationship.VISITED,
        ]

        if selected_status not in valid_statuses:
            return Response(
                {
                    "success": False,
                    "error": "invalid_status",
                    "message": "El estado enviado no es válido.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        relationship, created = (
            CafeRelationship.objects.get_or_create(
                user=request.user,
                cafe=cafe,
                defaults={
                    "status": selected_status,
                },
            )
        )

        removed = False

        if not created:
            if relationship.status == selected_status:
                relationship.delete()
                removed = True
            else:
                relationship.status = selected_status
                relationship.save()

        active_status = (
            None
            if removed
            else selected_status
        )

        return Response(
            {
                "success": True,
                "cafe_id": cafe.id,
                "status": active_status,
                "removed": removed,
            },
            status=status.HTTP_200_OK,
        )
    
class SetCafeCollectionAPIView(APIView):
    """
    POST /api/mobile/cafes/<cafe_id>/set-collection/

    Guarda la colección de una cafetería
    dentro del mapa del usuario autenticado.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, cafe_id):
        cafe = get_object_or_404(
            Cafe,
            id=cafe_id,
        )

        collection = request.data.get(
            "collection",
            "",
        )

        valid_collections = [
            "read",
            "work",
            "slow",
            "rain",
            "talk",
        ]

        if collection not in valid_collections:
            return Response(
                {
                    "success": False,
                    "error": "invalid_collection",
                    "message": "La colección enviada no es válida.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        relationship = CafeRelationship.objects.filter(
            user=request.user,
            cafe=cafe,
        ).first()

        if relationship is None:
            return Response(
                {
                    "success": False,
                    "error": "relationship_not_found",
                    "message": "Primero agregá el café a tu mapa.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        relationship.collection = collection
        relationship.save(
            update_fields=["collection"],
        )

        return Response(
            {
                "success": True,
                "cafe_id": cafe.id,
                "collection": relationship.collection,
            },
            status=status.HTTP_200_OK,
        )


class MeAPIView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MobileUserSerializer

    def get(self, request):
        serializer = MobileUserSerializer(
            request.user,
            context={"request": request},
        )

        return Response(serializer.data)