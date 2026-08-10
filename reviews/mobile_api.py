from django.shortcuts import get_object_or_404
from django.db.models import Avg

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser

from reviews.models import Cafe, CafeRelationship
from reviews.serializers import (
    CafeSerializer,
    CafeRelationshipSerializer,
    MobileUserSerializer,
)

class CreateCafeAPIView(APIView):
    """
    POST /api/mobile/cafes/create/

    Crea una cafetería para el usuario autenticado.
    La cafetería nace con plan Gratis y estado Sin reclamar.
    """

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        if not getattr(request.user, "is_owner", False):
            return Response(
                {
                    "success": False,
                    "error": "not_owner",
                    "message": (
                        "Solo las cuentas de cafetería "
                        "pueden agregar una cafetería."
                    ),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        nombre = str(
            request.data.get("name", "")
        ).strip()

        direccion = str(
            request.data.get("address", "")
        ).strip()

        localidad = str(
            request.data.get("location", "")
        ).strip()

        provincia = str(
            request.data.get("province", "")
        ).strip()

        if not nombre:
            return Response(
                {
                    "success": False,
                    "error": "name_required",
                    "message": "Ingresá el nombre de la cafetería.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if Cafe.objects.filter(
            name__iexact=nombre
        ).exists():
            return Response(
                {
                    "success": False,
                    "error": "cafe_already_exists",
                    "message": (
                        "Ya existe una cafetería "
                        "con ese nombre en Gota."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(direccion) < 5:
            return Response(
                {
                    "success": False,
                    "error": "invalid_address",
                    "message": (
                        "La dirección debe tener "
                        "al menos 5 caracteres."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not any(
            caracter.isdigit()
            for caracter in direccion
        ):
            return Response(
                {
                    "success": False,
                    "error": "invalid_address",
                    "message": (
                        "La dirección debe incluir un número."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not any(
            caracter.isalpha()
            for caracter in direccion
        ):
            return Response(
                {
                    "success": False,
                    "error": "invalid_address",
                    "message": (
                        "La dirección debe incluir "
                        "un nombre de calle."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not localidad:
            return Response(
                {
                    "success": False,
                    "error": "location_required",
                    "message": "Ingresá la localidad.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        foto = request.FILES.get("photo1")

        if foto is None:
            return Response(
                {
                    "success": False,
                    "error": "photo_required",
                    "message": (
                        "Tenés que subir al menos "
                        "una foto de la cafetería."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        max_size = 4 * 1024 * 1024

        if foto.size > max_size:
            return Response(
                {
                    "success": False,
                    "error": "photo_too_large",
                    "message": (
                        "La imagen no puede superar los 4 MB."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        instagram = str(
            request.data.get("instagram", "")
        ).strip()

        instagram = instagram.replace("@", "")
        instagram = instagram.replace(
            "https://instagram.com/",
            "",
        )
        instagram = instagram.replace(
            "https://www.instagram.com/",
            "",
        )
        instagram = instagram.strip("/")

        if " " in instagram:
            return Response(
                {
                    "success": False,
                    "error": "invalid_instagram",
                    "message": (
                        "El usuario de Instagram "
                        "no puede contener espacios."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        cafe = Cafe.objects.create(
            owner=request.user,
            name=nombre,
            address=direccion,
            location=localidad,
            province=provincia,
            description=request.data.get(
                "description",
                "",
            ),
            phone=request.data.get(
                "phone",
                "",
            ),
            email=request.data.get(
                "email",
                "",
            ),
            google_maps_url=request.data.get(
                "google_maps_url",
                "",
            ),
            instagram=instagram,
            photo1=foto,
            visibility_level=0,
        )

        return Response(
            {
                "success": True,
                "message": (
                    "Cafetería agregada correctamente."
                ),
                "cafe": {
                    "id": cafe.id,
                    "name": cafe.name,
                    "location": cafe.location,
                    "province": cafe.province,
                    "visibility_level":
                        cafe.visibility_level,
                    "claim_status":
                        cafe.claim_status,
                },
            },
            status=status.HTTP_201_CREATED,
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

        reviews = (
            cafe.reviews
            .select_related("user")
            .order_by("-created_at")[:5]
        )

        reviews_data = []

        for review in reviews:
            full_name = review.user.get_full_name().strip()

            if full_name:
                user_name = full_name
            elif review.user.first_name:
                user_name = review.user.first_name
            elif review.user.email:
                user_name = review.user.email.split("@")[0]
            else:
                user_name = "Usuario"

            avatar_url = None

            if review.user.avatar:
                try:
                    avatar_url = request.build_absolute_uri(
                        review.user.avatar.url
                    )
                except ValueError:
                    avatar_url = None

            reviews_data.append(
                {
                    "id": review.id,
                    "user": user_name,
                    "avatar": avatar_url,
                    "rating": review.rating,
                    "comment": review.comment,
                    "created_at": review.created_at.strftime(
                        "%d/%m/%Y"
                    ),
                    "owner_reply": review.owner_reply,
                }
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
                "reviews": reviews_data,
                "reviews_count": cafe.reviews.count(),
            },
            status=status.HTTP_200_OK,
        )

class RelatedCafesAPIView(APIView):
    """
    GET /api/mobile/cafes/<cafe_id>/related/

    Devuelve hasta 3 cafeterías relacionadas.
    Prioriza misma zona y misma provincia.
    Nunca incluye la cafetería actual.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, cafe_id):
        cafe_actual = get_object_or_404(
            Cafe,
            id=cafe_id,
        )

        cafes_seleccionados = []
        ids_seleccionados = [cafe_actual.id]

        def agregar_cafes(queryset):
            lugares_disponibles = 3 - len(cafes_seleccionados)

            if lugares_disponibles <= 0:
                return

            nuevos_cafes = list(
                queryset
                .exclude(id__in=ids_seleccionados)
                .annotate(
                    average_rating=Avg("reviews__rating"),
                )
                .prefetch_related("tags")
                .order_by("?")[:lugares_disponibles]
            )

            cafes_seleccionados.extend(nuevos_cafes)
            ids_seleccionados.extend(
                cafe.id
                for cafe in nuevos_cafes
            )

        # 1. Misma zona
        if cafe_actual.location:
            agregar_cafes(
                Cafe.objects.filter(
                    location=cafe_actual.location,
                )
            )

        # 2. Misma provincia
        if cafe_actual.province:
            agregar_cafes(
                Cafe.objects.filter(
                    province=cafe_actual.province,
                )
            )

        # 3. Completar con otras cafeterías
        agregar_cafes(
            Cafe.objects.all()
        )

        serializer = CafeSerializer(
            cafes_seleccionados,
            many=True,
            context={
                "request": request,
            },
        )

        return Response(
            serializer.data,
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