from math import atan2, cos, radians, sin, sqrt

from django.shortcuts import get_object_or_404
from django.db.models import Avg, Sum

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils import timezone
from datetime import timedelta

from reviews.models import (
    Cafe,
    CafeCheckIn,
    CafeRelationship,
    CafeWhisper,
    CafeReward,
    Review,
    ReviewReport,
    RewardActionRule,
    RewardSettings,
    UserPointTransaction,
    UserCoupon,
    Tag,
)

from reviews.rewards import award_points

from reviews.serializers import (
    CafeSerializer,
    CafeRelationshipSerializer,
    MobileUserSerializer,
)

def calculate_distance_meters(lat1, lon1, lat2, lon2):
    earth_radius_meters = 6371000

    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    delta_lat = radians(lat2 - lat1)
    delta_lon = radians(lon2 - lon1)

    a = (
        sin(delta_lat / 2) ** 2
        + cos(lat1_rad)
        * cos(lat2_rad)
        * sin(delta_lon / 2) ** 2
    )

    c = 2 * atan2(
        sqrt(a),
        sqrt(1 - a),
    )

    return earth_radius_meters * c

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

        if not provincia:
            return Response(
                {
                    "success": False,
                    "error": "province_required",
                    "message": "Seleccioná una provincia.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        foto = request.FILES.get("photo1")
        foto2 = request.FILES.get("photo2")
        foto3 = request.FILES.get("photo3")

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

        for imagen in [foto, foto2, foto3]:
            if imagen is not None and imagen.size > max_size:
                return Response(
                    {
                        "success": False,
                        "error": "photo_too_large",
                        "message": (
                            "Cada imagen puede pesar como máximo 4 MB."
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
            photo2=foto2,
            photo3=foto3,

            latitude=request.data.get("latitude") or None,
            longitude=request.data.get("longitude") or None,

            has_wifi=request.data.get("has_wifi") == "true",
            has_air_conditioning=request.data.get("has_air_conditioning") == "true",
            has_power_outlets=request.data.get("has_power_outlets") == "true",
            has_outdoor_seating=request.data.get("has_outdoor_seating") == "true",
            has_parking=request.data.get("has_parking") == "true",
            is_accessible=request.data.get("is_accessible") == "true",
            has_baby_changing=request.data.get("has_baby_changing") == "true",

            is_pet_friendly=request.data.get("is_pet_friendly") == "true",
            is_kids_friendly=request.data.get("is_kids_friendly") == "true",

            has_specialty_coffee=request.data.get("has_specialty_coffee") == "true",
            serves_brunch=request.data.get("serves_brunch") == "true",
            serves_breakfast=request.data.get("serves_breakfast") == "true",
            serves_alcohol=request.data.get("serves_alcohol") == "true",
            has_artisanal_pastries=request.data.get("has_artisanal_pastries") == "true",

            is_vegan_friendly=request.data.get("is_vegan_friendly") == "true",
            has_vegetarian_options=request.data.get("has_vegetarian_options") == "true",
            has_gluten_free_options=request.data.get("has_gluten_free_options") == "true",
            has_healthy_options=request.data.get("has_healthy_options") == "true",
            has_sugar_free_options=request.data.get("has_sugar_free_options") == "true",
            has_plant_based_milk=request.data.get("has_plant_based_milk") == "true",

            has_garden=request.data.get("has_garden") == "true",
            has_water_view=request.data.get("has_water_view") == "true",
            has_mountain_view=request.data.get("has_mountain_view") == "true",
            surrounded_by_nature=request.data.get("surrounded_by_nature") == "true",
            has_rooftop=request.data.get("has_rooftop") == "true",
            has_large_windows=request.data.get("has_large_windows") == "true",
            is_old_house=request.data.get("is_old_house") == "true",
            is_historic_building=request.data.get("is_historic_building") == "true",
            inside_bookstore=request.data.get("inside_bookstore") == "true",
            inside_cultural_space=request.data.get("inside_cultural_space") == "true",

            laptop_friendly=request.data.get("laptop_friendly") == "true",
            quiet_space=request.data.get("quiet_space") == "true",

            has_books_or_games=request.data.get("has_books_or_games") == "true",

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
class MyCafesAPIView(generics.ListAPIView):
    """
    GET /api/mobile/cafes/mine/

    Devuelve las cafeterías del usuario autenticado.
    """

    serializer_class = CafeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Cafe.objects
            .filter(owner=self.request.user)
            .order_by("name")
        )


class UpdateCafeAPIView(APIView):
    """
    PATCH /api/mobile/cafes/<cafe_id>/update/

    Actualiza una cafetería del usuario autenticado.
    """

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def patch(self, request, cafe_id):
        cafe = get_object_or_404(
            Cafe,
            id=cafe_id,
            owner=request.user,
        )

        campos_texto = {
            "name": "name",
            "address": "address",
            "location": "location",
            "province": "province",
            "description": "description",
            "phone": "phone",
            "email": "email",
            "google_maps_url": "google_maps_url",
            "instagram": "instagram",
            "latitude": "latitude",
            "longitude": "longitude",
        }

        for campo_api, campo_modelo in campos_texto.items():
            if campo_api in request.data:
                valor = request.data.get(campo_api)

                if campo_api == "instagram":
                    valor = str(valor or "").strip()
                    valor = valor.replace("@", "")
                    valor = valor.replace(
                        "https://instagram.com/",
                        "",
                    )
                    valor = valor.replace(
                        "https://www.instagram.com/",
                        "",
                    )
                    valor = valor.strip("/")

                if campo_api in ["latitude", "longitude"]:
                    valor = valor or None

                setattr(
                    cafe,
                    campo_modelo,
                    valor,
                )

        campos_booleanos = [
            "has_wifi",
            "has_air_conditioning",
            "has_power_outlets",
            "has_outdoor_seating",
            "has_parking",
            "is_accessible",
            "has_baby_changing",
            "is_pet_friendly",
            "is_kids_friendly",
            "has_specialty_coffee",
            "serves_brunch",
            "serves_breakfast",
            "serves_alcohol",
            "has_artisanal_pastries",
            "is_vegan_friendly",
            "has_vegetarian_options",
            "has_gluten_free_options",
            "has_healthy_options",
            "has_sugar_free_options",
            "has_plant_based_milk",
            "has_garden",
            "has_water_view",
            "has_mountain_view",
            "surrounded_by_nature",
            "has_rooftop",
            "has_large_windows",
            "is_old_house",
            "is_historic_building",
            "inside_bookstore",
            "inside_cultural_space",
            "laptop_friendly",
            "quiet_space",
            "has_books_or_games",
        ]

        for campo in campos_booleanos:
            if campo in request.data:
                setattr(
                    cafe,
                    campo,
                    request.data.get(campo) == "true",
                )

        max_size = 4 * 1024 * 1024

        for campo_foto in [
            "photo1",
            "photo2",
            "photo3",
        ]:
            nueva_foto = request.FILES.get(
                campo_foto
            )

            if nueva_foto is None:
                continue

            if nueva_foto.size > max_size:
                return Response(
                    {
                        "success": False,
                        "error": "photo_too_large",
                        "message": (
                            "Cada imagen puede pesar "
                            "como máximo 4 MB."
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            setattr(
                cafe,
                campo_foto,
                nueva_foto,
            )

        cafe.save()

        return Response(
            {
                "success": True,
                "message": (
                    "Cafetería actualizada correctamente."
                ),
                "cafe_id": cafe.id,
            },
            status=status.HTTP_200_OK,
        )


class ReviewTagsAPIView(APIView):
    """
    GET /api/mobile/review-tags/

    Devuelve las etiquetas activas usadas
    actualmente en el formulario web de reseñas.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        manual_tag_groups = {
            "conexion": [
                "Podés ir solo sin sentirte solo",
                "Ideal para charla de sobremesa",
                "Ideal para una primera cita sin presión",
            ],
            "refugio": [
                "Buen lugar para esperar sin ansiedad",
                "Te dan ganas de desconectarte",
                "Te vas y te dan ganas de volver",
                "Pedirías otra taza solo para quedarte",
            ],
            "ritual": [
                "Huele a café recién molido",
                "Pan casero y café en taza pesada",
                "Ventanales con luz todo el día",
            ],
            "inspiracion": [
                "Ideal para escribir o leer un cuento",
                "Paredes con historias",
            ],
        }

        nombres = [
            nombre
            for grupo in manual_tag_groups.values()
            for nombre in grupo
        ]

        tags = Tag.objects.filter(
            name__in=nombres,
        )

        tags_por_nombre = {
            tag.name: tag
            for tag in tags
        }

        resultado = []

        for grupo, nombres_grupo in manual_tag_groups.items():
            for nombre in nombres_grupo:
                tag = tags_por_nombre.get(nombre)

                if tag is None:
                    continue

                resultado.append(
                    {
                        "id": tag.id,
                        "name": tag.name,
                        "group": grupo,
                    }
                )

        return Response(
            {
                "tags": resultado,
            },
            status=status.HTTP_200_OK,
        )

class CafeWhispersAPIView(APIView):
    """
    GET /api/mobile/cafes/<cafe_id>/whispers/
    POST /api/mobile/cafes/<cafe_id>/whispers/

    Lista huellas visibles y permite dejar
    una huella por día por usuario.
    """

    permission_classes = [AllowAny]

    def get(self, request, cafe_id):
        cafe = get_object_or_404(
            Cafe,
            id=cafe_id,
        )

        whispers = (
            CafeWhisper.objects
            .filter(
                cafe=cafe,
                is_hidden=False,
            )
            .order_by("-created_at")[:12]
        )

        data = [
            {
                "id": whisper.id,
                "text": whisper.text,
                "created_at": whisper.created_at.strftime(
                    "%d/%m/%Y"
                ),
            }
            for whisper in whispers
        ]

        return Response(
            {
                "whispers": data,
                "count": len(data),
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request, cafe_id):
        if not request.user.is_authenticated:
            return Response(
                {
                    "success": False,
                    "error": "authentication_required",
                    "message": "Ingresá para dejar una huella.",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )
        cafe = get_object_or_404(
            Cafe,
            id=cafe_id,
        )

        today = timezone.now().date()

        already_left = CafeWhisper.objects.filter(
            user=request.user,
            cafe=cafe,
            created_at__date=today,
        ).exists()

        if already_left:
            return Response(
                {
                    "success": False,
                    "error": "whisper_already_exists_today",
                    "message": (
                        "Ya dejaste tu huella de hoy. "
                        "Mañana podés sumar otra ☕"
                    ),
                },
                status=status.HTTP_409_CONFLICT,
            )

        text = str(
            request.data.get("text", "")
        ).strip()

        if not text:
            return Response(
                {
                    "success": False,
                    "error": "text_required",
                    "message": "Escribí una huella.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        whisper = CafeWhisper.objects.create(
            user=request.user,
            cafe=cafe,
            text=text[:40],
        )

        reward_result = award_points(
            user=request.user,
            cafe=cafe,
            action=RewardActionRule.Action.WHISPER,
        )

        return Response(
            {
                "success": True,
                "message": (
                    "Esa sensación ya forma parte de este café ✨"
                ),
                "reward": reward_result,
                "whisper": {
                    "id": whisper.id,
                    "text": whisper.text,
                    "created_at":
                        whisper.created_at.strftime(
                            "%d/%m/%Y"
                        ),
                },
            },
            status=status.HTTP_201_CREATED,
        )

class CreateReviewAPIView(APIView):
    """
    POST /api/mobile/cafes/<cafe_id>/reviews/create/

    Crea una reseña para una cafetería.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, cafe_id):
        cafe = get_object_or_404(
            Cafe,
            id=cafe_id,
        )

        existing_review = Review.objects.filter(
            user=request.user,
            cafe=cafe,
        ).first()

        if existing_review:
            return Response(
                {
                    "success": False,
                    "error": "review_already_exists",
                    "message": (
                        "Ya dejaste una reseña para esta cafetería."
                    ),
                    "review_id": existing_review.id,
                },
                status=status.HTTP_409_CONFLICT,
            )

        rating = request.data.get("rating")
        comment = str(
            request.data.get("comment", "")
        ).strip()

        best_for_plan = str(
            request.data.get("best_for_plan", "")
        ).strip()

        precio_capuccino = request.data.get(
            "precio_capuccino"
        )

        try:
            rating = int(rating)
        except (TypeError, ValueError):
            return Response(
                {
                    "success": False,
                    "error": "invalid_rating",
                    "message": (
                        "Seleccioná una calificación "
                        "entre 1 y 5."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if rating < 1 or rating > 5:
            return Response(
                {
                    "success": False,
                    "error": "invalid_rating",
                    "message": (
                        "Seleccioná una calificación "
                        "entre 1 y 5."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        planes_validos = {
            choice[0]
            for choice in Review.PLAN_CHOICES
        }

        if best_for_plan not in planes_validos:
            return Response(
                {
                    "success": False,
                    "error": "invalid_best_for_plan",
                    "message": (
                        "Elegí para qué plan es mejor "
                        "esta cafetería."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if precio_capuccino in ("", None):
            precio_capuccino = None
        else:
            try:
                precio_capuccino = int(
                    precio_capuccino
                )
            except (TypeError, ValueError):
                return Response(
                    {
                        "success": False,
                        "error": "invalid_price",
                        "message": (
                            "Ingresá un precio válido."
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if (
                precio_capuccino < 1000
                or precio_capuccino > 15000
            ):
                return Response(
                    {
                        "success": False,
                        "error": "invalid_price",
                        "message": (
                            "El precio del capuccino "
                            "debe estar entre $1.000 "
                            "y $15.000."
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        review = Review.objects.create(
            user=request.user,
            cafe=cafe,
            location=cafe.location,
            rating=rating,
            comment=comment,
            best_for_plan=best_for_plan,
            precio_capuccino=precio_capuccino,
        )

        settings = RewardSettings.objects.first()

        valid_hours = (
            settings.check_in_valid_hours
            if settings is not None
            else 72
        )

        check_in_cutoff = timezone.now() - timedelta(
            hours=valid_hours
        )

        if (
            settings is not None
            and settings.program_starts_at is not None
            and settings.program_starts_at > check_in_cutoff
        ):
            check_in_cutoff = settings.program_starts_at

        has_recent_valid_check_in = CafeCheckIn.objects.filter(
            user=request.user,
            cafe=cafe,
            is_valid=True,
            created_at__gte=check_in_cutoff,
        ).exists()

        review_reward = None

        if has_recent_valid_check_in:
            review_reward = award_points(
                user=request.user,
                cafe=cafe,
                action=RewardActionRule.Action.REVIEW,
            )

        tag_ids = request.data.get("tags", [])

        if not isinstance(tag_ids, list):
            tag_ids = [tag_ids]

        tag_ids = [
            tag_id
            for tag_id in tag_ids
            if str(tag_id).strip()
        ]

        review_tag_bonus_reward = None

        if tag_ids:
            tags = Tag.objects.filter(
                id__in=tag_ids,
            )

            review.tags.set(tags)

            if (
                has_recent_valid_check_in
                and tags.exists()
            ):
                review_tag_bonus_reward = award_points(
                    user=request.user,
                    cafe=cafe,
                    action=RewardActionRule.Action.REVIEW_TAG_BONUS,
                )

        return Response(
            {
                "success": True,
                "message": "Reseña publicada correctamente.",
                "reward": {
                    "base": review_reward,
                    "tag_bonus": review_tag_bonus_reward,
                    "total_points": (
                        (review_reward or {}).get("points", 0)
                        + (review_tag_bonus_reward or {}).get("points", 0)
                    ),
                },
                "review_reward_eligible": has_recent_valid_check_in,
                "review": {
                    "id": review.id,
                    "rating": review.rating,
                    "comment": review.comment,
                    "best_for_plan": review.best_for_plan,
                    "precio_capuccino":
                        review.precio_capuccino,
                },
            },
            status=status.HTTP_201_CREATED,
        )

class UpdateReviewAPIView(APIView):
    """
    PUT /api/mobile/reviews/<review_id>/

    Actualiza una reseña del usuario autenticado.
    """

    permission_classes = [IsAuthenticated]

    def put(self, request, review_id):
        review = get_object_or_404(
            Review,
            id=review_id,
            user=request.user,
        )

        rating = request.data.get("rating")

        comment = str(
            request.data.get("comment", "")
        ).strip()

        best_for_plan = str(
            request.data.get("best_for_plan", "")
        ).strip()

        precio_capuccino = request.data.get(
            "precio_capuccino"
        )

        try:
            rating = int(rating)
        except (TypeError, ValueError):
            return Response(
                {
                    "success": False,
                    "error": "invalid_rating",
                    "message": (
                        "Seleccioná una calificación "
                        "entre 1 y 5."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if rating < 1 or rating > 5:
            return Response(
                {
                    "success": False,
                    "error": "invalid_rating",
                    "message": (
                        "Seleccioná una calificación "
                        "entre 1 y 5."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        planes_validos = {
            choice[0]
            for choice in Review.PLAN_CHOICES
        }

        if best_for_plan not in planes_validos:
            return Response(
                {
                    "success": False,
                    "error": "invalid_best_for_plan",
                    "message": (
                        "Elegí para qué plan es mejor "
                        "esta cafetería."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if precio_capuccino in ("", None):
            precio_capuccino = None
        else:
            try:
                precio_capuccino = int(
                    precio_capuccino
                )
            except (TypeError, ValueError):
                return Response(
                    {
                        "success": False,
                        "error": "invalid_price",
                        "message": (
                            "Ingresá un precio válido."
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if (
                precio_capuccino < 1000
                or precio_capuccino > 15000
            ):
                return Response(
                    {
                        "success": False,
                        "error": "invalid_price",
                        "message": (
                            "El precio del capuccino "
                            "debe estar entre $1.000 "
                            "y $15.000."
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        review.rating = rating
        review.comment = comment
        review.best_for_plan = best_for_plan
        review.precio_capuccino = precio_capuccino

        review.save(
            update_fields=[
                "rating",
                "comment",
                "best_for_plan",
                "precio_capuccino",
            ]
        )

        tag_ids = request.data.get(
            "tags",
            [],
        )

        if not isinstance(tag_ids, list):
            tag_ids = [tag_ids]

        tag_ids = [
            tag_id
            for tag_id in tag_ids
            if str(tag_id).strip()
        ]

        tags = Tag.objects.filter(
            id__in=tag_ids,
        )

        review.tags.set(tags)

        return Response(
            {
                "success": True,
                "message": (
                    "Reseña actualizada correctamente."
                ),
                "review": {
                    "id": review.id,
                    "rating": review.rating,
                    "comment": review.comment,
                    "best_for_plan":
                        review.best_for_plan,
                    "precio_capuccino":
                        review.precio_capuccino,
                },
            },
            status=status.HTTP_200_OK,
        )

class ReportReviewAPIView(APIView):
    """
    POST /api/mobile/reviews/<review_id>/report/

    Permite al usuario autenticado reportar una reseña.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, review_id):
        review = get_object_or_404(
            Review,
            id=review_id,
        )

        if review.user_id == request.user.id:
            return Response(
                {
                    "success": False,
                    "error": "own_review",
                    "message": "No podés reportar tu propia reseña.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        reason = str(
            request.data.get("reason", "")
        ).strip()

        message = str(
            request.data.get("message", "")
        ).strip()

        valid_reasons = {
            choice[0]
            for choice in ReviewReport.Reason.choices
        }

        if reason not in valid_reasons:
            return Response(
                {
                    "success": False,
                    "error": "invalid_reason",
                    "message": "Seleccioná un motivo válido.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        existing_report = ReviewReport.objects.filter(
            user=request.user,
            review=review,
        ).first()

        if existing_report is not None:
            return Response(
                {
                    "success": False,
                    "error": "already_reported",
                    "message": (
                        "Ya reportaste esta reseña. "
                        "Gracias por ayudarnos a cuidar Gota."
                    ),
                },
                status=status.HTTP_409_CONFLICT,
            )

        report = ReviewReport.objects.create(
            user=request.user,
            review=review,
            reason=reason,
            message=message or None,
        )

        return Response(
            {
                "success": True,
                "message": (
                    "Gracias. Recibimos tu reporte "
                    "y vamos a revisarlo."
                ),
                "report": {
                    "id": report.id,
                    "review_id": review.id,
                    "reason": report.reason,
                    "status": report.status,
                },
            },
            status=status.HTTP_201_CREATED,
        )

class CafeDetailAPIView(APIView):
    """
    GET /api/mobile/cafes/<cafe_id>/

    Devuelve el detalle completo de una cafetería.
    """

    permission_classes = [AllowAny]

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

        my_review = None

        if request.user.is_authenticated:
            my_review = Review.objects.filter(
                cafe=cafe,
                user=request.user,
            ).first()

        my_review_data = None

        if my_review:
            my_review_data = {
                "id": my_review.id,
                "rating": my_review.rating,
                "comment": my_review.comment,
                "best_for_plan": my_review.best_for_plan,
                "precio_capuccino": my_review.precio_capuccino,
                "tags": list(
                    my_review.tags.values_list(
                        "id",
                        flat=True,
                    )
                ),
            }

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
                "is_kids_friendly":
                    cafe.is_kids_friendly,
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
                "has_healthy_options":
                    cafe.has_healthy_options,
                "has_sugar_free_options":
                    cafe.has_sugar_free_options,
                "has_plant_based_milk":
                    cafe.has_plant_based_milk,

                "has_garden":
                    cafe.has_garden,
                "has_water_view":
                    cafe.has_water_view,
                "has_mountain_view":
                    cafe.has_mountain_view,
                "surrounded_by_nature":
                    cafe.surrounded_by_nature,
                "has_rooftop":
                    cafe.has_rooftop,
                "has_large_windows":
                    cafe.has_large_windows,
                "is_old_house":
                    cafe.is_old_house,
                "is_historic_building":
                    cafe.is_historic_building,
                "inside_bookstore":
                    cafe.inside_bookstore,
                "inside_cultural_space":
                    cafe.inside_cultural_space,
                "laptop_friendly":
                    cafe.laptop_friendly,
                "quiet_space":
                    cafe.quiet_space,
                "has_books_or_games":
                    cafe.has_books_or_games,
                "tags": tags,
                "reviews": reviews_data,
                "reviews_count": cafe.reviews.count(),
                "my_review": my_review_data,
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

    permission_classes = [AllowAny]

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

        reward_result = None

        if not removed:
            if selected_status == CafeRelationship.WANT_TO_GO:
                reward_result = award_points(
                    user=request.user,
                    cafe=cafe,
                    action=RewardActionRule.Action.WANT_TO_GO,
                )

            elif selected_status in [
                CafeRelationship.WANT_TO_RETURN,
                CafeRelationship.VISITED,
            ]:
                reward_result = award_points(
                    user=request.user,
                    cafe=cafe,
                    action=RewardActionRule.Action.RELATIONSHIP_PROGRESS,
                )

        return Response(
            {
                "success": True,
                "cafe_id": cafe.id,
                "status": active_status,
                "removed": removed,
                "reward": reward_result,
            },
            status=status.HTTP_200_OK,
        )

class MyGotasAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        reward_settings = RewardSettings.objects.first()
        program_starts_at = (
            reward_settings.program_starts_at
            if reward_settings
            else None
        )

        transactions = UserPointTransaction.objects.filter(
            user=request.user,
        ).select_related(
            "cafe",
        )

        if program_starts_at:
            transactions = transactions.filter(
                created_at__gte=program_starts_at,
            )
        else:
            transactions = transactions.none()

        balance = transactions.aggregate(
            total=Sum("points"),
        )["total"] or 0

        recent_transactions = []

        for transaction in transactions[:10]:
            recent_transactions.append(
                {
                    "id": transaction.id,
                    "action": transaction.action,
                    "action_label": transaction.get_action_display(),
                    "points": transaction.points,
                    "created_at": transaction.created_at,
                    "cafe": (
                        {
                            "id": transaction.cafe.id,
                            "name": transaction.cafe.name,
                        }
                        if transaction.cafe
                        else None
                    ),
                }
            )

        milestone_points = (
            CafeReward.objects.filter(
                is_active=True,
                unlock_type=CafeReward.UnlockType.POINTS,
                points_required__isnull=False,
            )
            .values_list("points_required", flat=True)
            .distinct()
            .order_by("points_required")
        )

        milestones = [
            {
                "points_required": points,
                "reached": balance >= points,
            }
            for points in milestone_points
        ]

        next_milestone = next(
            (
                milestone
                for milestone in milestones
                if not milestone["reached"]
            ),
            None,
        )

        available_coupons = []

        coupons = (
            UserCoupon.objects
            .filter(
                user=request.user,
                status=UserCoupon.Status.AVAILABLE,
            )
            .select_related(
                "cafe",
                "reward",
            )
            .order_by("-obtained_at")
        )

        for coupon in coupons:
            available_coupons.append(
                {
                    "id": coupon.id,
                    "code": coupon.code,
                    "reward_text": coupon.reward_text_snapshot,
                    "terms": coupon.terms_snapshot,
                    "obtained_at": coupon.obtained_at,
                    "expires_at": coupon.expires_at,
                    "cafe": {
                        "id": coupon.cafe.id,
                        "name": coupon.cafe.name,
                    },
                }
            )
        
        
        return Response(
            {
                "balance": balance,
                "recent_transactions": recent_transactions,
                "milestones": milestones,
                "next_milestone": next_milestone,
                "available_coupons": available_coupons,
            },
            status=status.HTTP_200_OK,
        )

class CafeCheckInAPIView(APIView):
    """
    POST /api/mobile/cafes/<cafe_id>/check-in/

    Valida si el usuario está físicamente cerca de la cafetería.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, cafe_id):
        cafe = get_object_or_404(
            Cafe,
            id=cafe_id,
        )

        try:
            detected_latitude = float(
                request.data.get("latitude")
            )
            detected_longitude = float(
                request.data.get("longitude")
            )
        except (TypeError, ValueError):
            return Response(
                {
                    "success": False,
                    "error": "invalid_coordinates",
                    "message": "No pudimos validar tu ubicación.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if cafe.latitude is None or cafe.longitude is None:
            return Response(
                {
                    "success": False,
                    "error": "cafe_without_coordinates",
                    "message": "Esta cafetería todavía no tiene una ubicación precisa cargada.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        settings = RewardSettings.objects.first()

        radius_meters = (
            settings.check_in_radius_meters
            if settings is not None
            else 150
        )

        distance_meters = calculate_distance_meters(
            detected_latitude,
            detected_longitude,
            float(cafe.latitude),
            float(cafe.longitude),
        )

        is_valid = distance_meters <= radius_meters

        check_in = CafeCheckIn.objects.create(
            user=request.user,
            cafe=cafe,
            latitude=detected_latitude,
            longitude=detected_longitude,
            distance_meters=distance_meters,
            is_valid=is_valid,
        )

        reward_result = None

        if is_valid:
            reward_result = award_points(
                user=request.user,
                cafe=cafe,
                action=RewardActionRule.Action.CHECK_IN,
            )

        return Response(
            {
                "success": True,
                "cafe_id": cafe.id,
                "is_valid": is_valid,
                "distance_meters": round(
                    distance_meters,
                    1,
                ),
                "allowed_radius_meters": radius_meters,
                "reward": reward_result,
                "check_in_id": check_in.id,
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

    def patch(self, request):
        user = request.user

        first_name = str(
            request.data.get(
                "first_name",
                user.first_name,
            )
        ).strip()

        last_name = str(
            request.data.get(
                "last_name",
                user.last_name,
            )
        ).strip()

        if not first_name:
            return Response(
                {
                    "success": False,
                    "message": "Ingresá tu nombre.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.first_name = first_name
        user.last_name = last_name

        user.save(
            update_fields=[
                "first_name",
                "last_name",
            ]
        )

        serializer = MobileUserSerializer(
            user,
            context={"request": request},
        )

        return Response(
            {
                "success": True,
                "user": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

class BecomeOwnerAPIView(APIView):
    """
    POST /api/mobile/become-owner/

    Convierte al usuario autenticado
    en una cuenta de dueño de cafetería.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        if user.is_owner:
            return Response(
                {
                    "success": True,
                    "already_owner": True,
                    "message": (
                        "Tu cuenta ya está configurada "
                        "como dueño de cafetería."
                    ),
                },
                status=status.HTTP_200_OK,
            )

        user.is_owner = True
        user.save(update_fields=["is_owner"])

        return Response(
            {
                "success": True,
                "already_owner": False,
                "message": (
                    "Tu cuenta ahora está configurada "
                    "como dueño de cafetería."
                ),
            },
            status=status.HTTP_200_OK,
        )