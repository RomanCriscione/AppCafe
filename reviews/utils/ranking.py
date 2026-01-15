from django.utils import timezone
from datetime import timedelta


def calcular_score_cafe(
    cafe,
    *,
    user=None,
    user_lat=None,
    user_lon=None,
    cafes_vistos_ids=None,
):
    score = 0.0

    # === A. Calidad ===
    rating = getattr(cafe, "average_rating", 0) or 0
    reviews = getattr(cafe, "total_reviews", 0) or 0

    score += rating * 3.2
    score += min(reviews, 20) * 0.45

    # === B. Popularidad ===
    score += min(cafe.favorites.count(), 30) * 0.4

    # === C. Fotos ===
    fotos = sum(bool(getattr(cafe, f"photo{i}", None)) for i in (1, 2, 3))
    score += fotos * 1.2

    # === D. Características ===
    features = [
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
        cafe.has_air_conditioning,
    ]
    score += sum(features) * 0.3

    # === E. Actividad reciente ===
    hace_14_dias = timezone.now() - timedelta(days=14)
    boost = 0.0

    reviews_recientes = cafe.reviews.filter(
        created_at__gte=hace_14_dias
    ).count()
    boost += min(reviews_recientes, 2) * 1.0

    if cafe.reviews.filter(
        owner_reply__isnull=False,
        created_at__gte=hace_14_dias
    ).exists():
        boost += 1.2

    if fotos:
        boost += 0.6

    score += min(boost, 3.0)

    # === F. Plan ===
    if cafe.visibility_level == 1:
        score *= 1.10
    elif cafe.visibility_level == 2:
        score *= 1.25

    # === G. Diversidad ===
    recent_vistos = set((cafes_vistos_ids or [])[-10:])
    if cafe.id in recent_vistos:
        score *= 0.82
    else:
        score *= 1.08

    # === H. Cercanía ===
    distance_boost = 0.0
    if user_lat and user_lon and cafe.latitude and cafe.longitude:
        from reviews.utils.geo import haversine_distance
        dist = haversine_distance(
            user_lat, user_lon, cafe.latitude, cafe.longitude
        )

        if dist <= 0.5:
            distance_boost = 3.5
        elif dist <= 1:
            distance_boost = 2.5
        elif dist <= 2:
            distance_boost = 1.5
        elif dist <= 3:
            distance_boost = 0.8

    score += min(distance_boost, 3.0)

    # === I. Afinidad ===
    if user and hasattr(user, "favorite_cafes"):
        favoritos = list(user.favorite_cafes.all()[:5])
        affinity = 0.0

        for fav in favoritos:
            if cafe.is_pet_friendly and fav.is_pet_friendly:
                affinity += 0.4
            if cafe.is_vegan_friendly and fav.is_vegan_friendly:
                affinity += 0.4
            if cafe.has_wifi and fav.has_wifi:
                affinity += 0.3
            if cafe.has_outdoor_seating and fav.has_outdoor_seating:
                affinity += 0.3
            if cafe.has_books_or_games and fav.has_books_or_games:
                affinity += 0.2

        score += min(affinity, 2.0)

    return round(score, 2)
