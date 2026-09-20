import math
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from .models import (
    CafeCheckIn,
    CafeReward,
    RewardActionRule,
    RewardClaim,
    RewardSettings,
    UserCoupon,
    UserPointTransaction,
    UserRewardUnlock,
)

def _get_current_window_transactions(
    user,
    action,
    window_hours,
    program_starts_at,
):
    """
    Devuelve los movimientos pertenecientes a la ventana fija actual.

    La ventana empieza cuando se otorgó la primera recompensa.
    Ejemplo:
    primera recompensa 16:20
    → ventana válida hasta 16:20 del día siguiente.

    No funciona como una ventana móvil de "últimas 24 horas".
    """

    transactions = list(
        UserPointTransaction.objects.filter(
            user=user,
            action=action,
            created_at__gte=program_starts_at,
        ).order_by("created_at")
    )

    if not transactions:
        return []

    window_duration = timedelta(
        hours=window_hours,
    )

    current_window = []
    window_started_at = None

    for point_transaction in transactions:

        if (
            window_started_at is None
            or point_transaction.created_at
            >= window_started_at + window_duration
        ):
            window_started_at = (
                point_transaction.created_at
            )
            current_window = [
                point_transaction
            ]
            continue

        current_window.append(
            point_transaction
        )

    if (
        window_started_at is None
        or timezone.now()
        >= window_started_at + window_duration
    ):
        return []

    return current_window

def _unlock_point_rewards(
    *,
    user,
    balance,
):
    """
    Registra los hitos de Gotas alcanzados por el usuario.

    Alcanzar un hito NO genera todavía un cupón.
    El usuario elegirá posteriormente entre los beneficios
    disponibles para ese nivel de Gotas.
    """

    available_thresholds = (
        CafeReward.objects
        .filter(
            is_active=True,
            unlock_type=CafeReward.UnlockType.POINTS,
            points_required__isnull=False,
            points_required__lte=balance,
        )
        .values_list(
            "points_required",
            flat=True,
        )
        .distinct()
        .order_by("points_required")
    )

    unlocked_rewards = []

    for points_required in available_thresholds:
        unlock, created = (
            UserRewardUnlock.objects.get_or_create(
                user=user,
                points_required=points_required,
            )
        )

        if created:
            unlocked_rewards.append(unlock)

    return unlocked_rewards

def get_available_rewards_for_unlock(
    *,
    unlock,
):
    """
    Devuelve los beneficios que el usuario puede elegir
    para un hito de Gotas.

    Valida disponibilidad y, cuando existe una ubicación
    de referencia, calcula la distancia a cada cafetería.
    """

    now = timezone.now()

    reference_location = get_user_reward_reference_location(
        user=unlock.user,
    )

    rewards = (
        CafeReward.objects
        .filter(
            is_active=True,
            unlock_type=CafeReward.UnlockType.POINTS,
            points_required=unlock.points_required,
        )
        .select_related("cafe")
        .order_by(
            "priority",
            "cafe__name",
            "id",
        )
    )

    available_rewards = []

    for reward in rewards:

        if (
            reward.valid_from is not None
            and now < reward.valid_from
        ):
            continue

        if (
            reward.valid_until is not None
            and now > reward.valid_until
        ):
            continue

        if UserCoupon.objects.filter(
            user=unlock.user,
            reward=reward,
        ).exists():
            continue

        if reward.stock is not None:
            delivered_count = (
                UserCoupon.objects
                .filter(
                    reward=reward,
                )
                .exclude(
                    status=UserCoupon.Status.CANCELLED,
                )
                .count()
            )

            if delivered_count >= reward.stock:
                continue

        distance_km = None

        if (
            reference_location is not None
            and reward.cafe.latitude is not None
            and reward.cafe.longitude is not None
        ):
            distance_km = calculate_distance_km(
                latitude_1=reference_location["latitude"],
                longitude_1=reference_location["longitude"],
                latitude_2=reward.cafe.latitude,
                longitude_2=reward.cafe.longitude,
            )

        available_rewards.append({
            "reward": reward,
            "distance_km": distance_km,
        })

    available_rewards.sort(
        key=lambda item: (
            item["distance_km"] is None,
            (
                item["distance_km"]
                if item["distance_km"] is not None
                else float("inf")
            ),
            item["reward"].priority,
            item["reward"].id,
        )
    )

    return available_rewards

def get_reward_options_for_unlock(
    *,
    unlock,
):
    """
    Determina qué beneficios mostrar para un hito desbloqueado.

    Prioridad:
    1. Beneficios dentro del radio cercano.
    2. Si no hay, beneficios dentro del radio ampliado.
    3. Si tampoco hay, informa que no existen opciones cercanas.
    """

    settings_obj = RewardSettings.objects.first()

    nearby_radius_km = (
        settings_obj.reward_nearby_radius_km
        if settings_obj
        else 10.0
    )

    extended_radius_km = (
        settings_obj.reward_extended_radius_km
        if settings_obj
        else 25.0
    )

    available_rewards = get_available_rewards_for_unlock(
        unlock=unlock,
    )

    reference_location = get_user_reward_reference_location(
        user=unlock.user,
    )

    if reference_location is None:
        return {
            "status": "location_required",
            "radius_km": None,
            "rewards": [],
        }

    rewards_with_distance = [
        item
        for item in available_rewards
        if item["distance_km"] is not None
    ]

    nearby_rewards = [
        item
        for item in rewards_with_distance
        if item["distance_km"] <= nearby_radius_km
    ]

    if nearby_rewards:
        return {
            "status": "nearby",
            "radius_km": nearby_radius_km,
            "rewards": nearby_rewards,
        }

    extended_rewards = [
        item
        for item in rewards_with_distance
        if item["distance_km"] <= extended_radius_km
    ]

    if extended_rewards:
        return {
            "status": "extended",
            "radius_km": extended_radius_km,
            "rewards": extended_rewards,
        }

    return {
        "status": "no_nearby_rewards",
        "radius_km": extended_radius_km,
        "rewards": [],
    }

def get_reward_options_for_location(
    *,
    unlock,
    location,
):
    """
    Devuelve beneficios disponibles para un hito
    filtrados por una localidad elegida por el usuario.
    """

    location = (location or "").strip()

    if not location:
        return []

    available_rewards = get_available_rewards_for_unlock(
        unlock=unlock,
    )

    return [
        item
        for item in available_rewards
        if (
            item["reward"].cafe.location
            and item["reward"].cafe.location.strip().casefold()
            == location.casefold()
        )
    ]

def get_reward_locations_for_unlock(
    *,
    unlock,
):
    """
    Devuelve las localidades que tienen al menos
    un beneficio disponible para este hito de Gotas.
    """

    available_rewards = get_available_rewards_for_unlock(
        unlock=unlock,
    )

    locations = {}

    for item in available_rewards:
        location = (
            item["reward"].cafe.location
            or ""
        ).strip()

        if not location:
            continue

        key = location.casefold()

        if key not in locations:
            locations[key] = {
                "name": location,
                "rewards_count": 0,
            }

        locations[key]["rewards_count"] += 1

    return sorted(
        locations.values(),
        key=lambda item: item["name"].casefold(),
    )

@transaction.atomic
def claim_reward_from_unlock(
    *,
    user,
    unlock_id,
    reward_id,
    location=None,
):
    """
    Convierte un hito pendiente en un cupón concreto.

    El beneficio debe pertenecer a las opciones que Gota
    ofreció al usuario, ya sea por cercanía o por una
    localidad elegida manualmente.
    """

    unlock = (
        UserRewardUnlock.objects
        .select_for_update()
        .filter(
            id=unlock_id,
            user=user,
        )
        .first()
    )

    if unlock is None:
        return {
            "ok": False,
            "reason": "unlock_not_found",
        }

    if unlock.status != UserRewardUnlock.Status.PENDING:
        return {
            "ok": False,
            "reason": "unlock_already_claimed",
        }

    location = (location or "").strip()

    if location:
        offered_rewards = get_reward_options_for_location(
            unlock=unlock,
            location=location,
        )
    else:
        options = get_reward_options_for_unlock(
            unlock=unlock,
        )
        offered_rewards = options["rewards"]

    reward = next(
        (
            item["reward"]
            for item in offered_rewards
            if item["reward"].id == reward_id
        ),
        None,
    )

    if reward is None:
        return {
            "ok": False,
            "reason": "reward_not_offered",
        }

    # Bloqueamos el beneficio antes de consumir stock.
    reward = (
        CafeReward.objects
        .select_for_update()
        .get(id=reward.id)
    )

    # Revalidamos que siga activo y vigente.
    now = timezone.now()

    if not reward.is_active:
        return {
            "ok": False,
            "reason": "reward_not_available",
        }

    if (
        reward.valid_from is not None
        and now < reward.valid_from
    ):
        return {
            "ok": False,
            "reason": "reward_not_available",
        }

    if (
        reward.valid_until is not None
        and now > reward.valid_until
    ):
        return {
            "ok": False,
            "reason": "reward_not_available",
        }

    # Revalidamos stock dentro de la transacción.
    if reward.stock is not None:
        delivered_count = (
            UserCoupon.objects
            .filter(reward=reward)
            .exclude(
                status=UserCoupon.Status.CANCELLED,
            )
            .count()
        )

        if delivered_count >= reward.stock:
            return {
                "ok": False,
                "reason": "reward_out_of_stock",
            }

    expires_at = (
        now
        + timedelta(days=reward.coupon_valid_days)
    )

    coupon = UserCoupon.objects.create(
        user=user,
        cafe=reward.cafe,
        reward=reward,
        reward_text_snapshot=reward.user_text,
        terms_snapshot=reward.terms,
        expires_at=expires_at,
    )

    unlock.status = UserRewardUnlock.Status.CLAIMED
    unlock.coupon = coupon
    unlock.claimed_at = now

    unlock.save(
        update_fields=[
            "status",
            "coupon",
            "claimed_at",
        ]
    )

    return {
        "ok": True,
        "coupon": coupon,
        "unlock": unlock,
    }

def get_user_reward_reference_location(
    *,
    user,
):
    """
    Obtiene una ubicación de referencia para ofrecer beneficios.

    Usa hasta las últimas 20 visitas validadas del usuario
    y toma como zona principal la localidad con mayor actividad.

    En caso de empate, gana la localidad de la visita
    más reciente.

    No representa el domicilio del usuario ni almacena
    una nueva ubicación.
    """

    recent_check_ins = list(
        CafeCheckIn.objects
        .filter(
            user=user,
            is_valid=True,
            cafe__latitude__isnull=False,
            cafe__longitude__isnull=False,
        )
        .select_related("cafe")
        .order_by("-created_at")[:20]
    )

    if not recent_check_ins:
        return None

    location_counts = {}

    for check_in in recent_check_ins:
        location = (
            check_in.cafe.location
            or ""
        ).strip()

        if not location:
            continue

        key = location.casefold()

        if key not in location_counts:
            location_counts[key] = {
                "count": 0,
                "latest_check_in": check_in,
            }

        location_counts[key]["count"] += 1

    if not location_counts:
        return None

    reference_data = max(
        location_counts.values(),
        key=lambda item: (
            item["count"],
            item["latest_check_in"].created_at,
        ),
    )

    reference_check_in = (
        reference_data["latest_check_in"]
    )

    return {
        "latitude": reference_check_in.cafe.latitude,
        "longitude": reference_check_in.cafe.longitude,
        "cafe_id": reference_check_in.cafe_id,
        "location": reference_check_in.cafe.location,
        "source": "predominant_valid_check_ins",
        "sample_size": len(recent_check_ins),
        "location_visits": reference_data["count"],
    }

def calculate_distance_km(
    *,
    latitude_1,
    longitude_1,
    latitude_2,
    longitude_2,
):
    """
    Calcula la distancia aproximada en kilómetros
    entre dos coordenadas geográficas.
    """

    earth_radius_km = 6371.0

    lat_1 = math.radians(latitude_1)
    lon_1 = math.radians(longitude_1)
    lat_2 = math.radians(latitude_2)
    lon_2 = math.radians(longitude_2)

    delta_lat = lat_2 - lat_1
    delta_lon = lon_2 - lon_1

    haversine = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat_1)
        * math.cos(lat_2)
        * math.sin(delta_lon / 2) ** 2
    )

    central_angle = 2 * math.atan2(
        math.sqrt(haversine),
        math.sqrt(1 - haversine),
    )

    return earth_radius_km * central_angle

@transaction.atomic
def award_points(
    *,
    user,
    cafe,
    action,
):
    """
    Intenta otorgar Gotas por una acción.

    Django decide siempre si corresponde otorgarlas.

    Devuelve un diccionario con:
    - awarded: si se otorgaron Gotas
    - points: cantidad otorgada
    - reason: motivo si no se otorgaron
    - reached_window_limit: si esta acción agotó el cupo
      de recompensas de la ventana actual
    """

    # Serializa las recompensas de un mismo usuario.
    # Evita dobles premios si llegan dos requests al mismo tiempo.
    User = get_user_model()
    User.objects.select_for_update().get(
        pk=user.pk,
    )

    settings = RewardSettings.objects.first()

    if settings is None or not settings.rewards_enabled:
        return {
            "awarded": False,
            "points": 0,
            "reason": "rewards_disabled",
            "reached_window_limit": False,
        }

    if (
        settings.program_starts_at is None
        or timezone.now() < settings.program_starts_at
    ):
        return {
            "awarded": False,
            "points": 0,
            "reason": "program_not_started",
            "reached_window_limit": False,
        }

    try:
        rule = RewardActionRule.objects.get(
            action=action,
        )
    except RewardActionRule.DoesNotExist:
        return {
            "awarded": False,
            "points": 0,
            "reason": "rule_not_found",
            "reached_window_limit": False,
        }

    if not rule.is_active:
        return {
            "awarded": False,
            "points": 0,
            "reason": "rule_inactive",
            "reached_window_limit": False,
        }

    # Si el usuario ya recibió la recompensa de progreso
    # (Ya fui / Quiero volver), no puede volver atrás
    # a Quiero ir para obtener Gotas adicionales.
    if action == RewardActionRule.Action.WANT_TO_GO:
        progressed_already = UserPointTransaction.objects.filter(
            user=user,
            cafe=cafe,
            action=RewardActionRule.Action.RELATIONSHIP_PROGRESS,
            created_at__gte=settings.program_starts_at,
        ).exists()

        if progressed_already:
            return {
                "awarded": False,
                "points": 0,
                "reason": "relationship_already_progressed",
                "reached_window_limit": False,
            }

    previous_transactions = (
        UserPointTransaction.objects.filter(
            user=user,
            cafe=cafe,
            action=action,
            created_at__gte=settings.program_starts_at,
        )
    )

    # Acción que sólo puede premiarse una vez
    # por cafetería.
    if rule.repeat_after_days is None:
        if previous_transactions.exists():
            return {
                "awarded": False,
                "points": 0,
                "reason": "already_rewarded",
                "reached_window_limit": False,
            }

    # Acción repetible después de X días.
    else:
        last_transaction = (
            previous_transactions
            .order_by("-created_at")
            .first()
        )

        if last_transaction is not None:
            next_available_at = (
                last_transaction.created_at
                + timedelta(
                    days=rule.repeat_after_days,
                )
            )

            if timezone.now() < next_available_at:
                return {
                    "awarded": False,
                    "points": 0,
                    "reason": "repeat_cooldown",
                    "reached_window_limit": False,
                    "next_available_at": (
                        next_available_at
                    ),
                }

    reached_window_limit = False

    # Límite por ventana.
    if (
        rule.max_rewards_per_window
        and rule.window_hours
    ):
        current_window = (
            _get_current_window_transactions(
                user=user,
                action=action,
                window_hours=rule.window_hours,
                program_starts_at=settings.program_starts_at,
            )
        )

        if (
            len(current_window)
            >= rule.max_rewards_per_window
        ):
            return {
                "awarded": False,
                "points": 0,
                "reason": "window_limit_reached",
                "reached_window_limit": True,
            }

        if (
            len(current_window) + 1
            == rule.max_rewards_per_window
        ):
            reached_window_limit = True

    point_transaction = (
        UserPointTransaction.objects.create(
            user=user,
            cafe=cafe,
            action=action,
            points=rule.points,
        )
    )

    current_balance = sum(
        UserPointTransaction.objects.filter(
            user=user,
            created_at__gte=settings.program_starts_at,
        ).values_list(
            "points",
            flat=True,
        )
    )

    new_unlocks = _unlock_point_rewards(
        user=user,
        balance=current_balance,
    )

    return {
        "awarded": True,
        "points": rule.points,
        "reason": "awarded",
        "reached_window_limit": (
            reached_window_limit
        ),
        "transaction_id": (
            point_transaction.id
        ),
        "unlocked_rewards": [
            {
                "unlock_id": unlock.id,
                "points_required": unlock.points_required,
                "status": unlock.status,
            }
            for unlock in new_unlocks
        ],
    }

@transaction.atomic
def approve_reward_claim(
    *,
    claim,
    resolved_by,
    has_tag_bonus=False,
):
    """
    Aprueba un reclamo de Gotas y acredita las recompensas
    que correspondían a la reseña.

    No crea un CafeCheckIn retroactivo.

    Es idempotente:
    un mismo reclamo no puede acreditar dos veces
    los mismos movimientos.
    """

    claim = (
        RewardClaim.objects
        .select_for_update()
        .select_related(
            "user",
            "cafe",
            "review",
        )
        .get(pk=claim.pk)
    )

    if claim.status != RewardClaim.Status.PENDING:
        return {
            "approved": False,
            "reason": "claim_already_resolved",
            "points": 0,
            "unlocked_rewards": [],
        }

    if claim.review is None:
        return {
            "approved": False,
            "reason": "review_required",
            "points": 0,
            "unlocked_rewards": [],
        }

    if (
        claim.review.user_id != claim.user_id
        or claim.review.cafe_id != claim.cafe_id
    ):
        return {
            "approved": False,
            "reason": "review_mismatch",
            "points": 0,
            "unlocked_rewards": [],
        }

    settings = RewardSettings.objects.first()

    if settings is None or not settings.rewards_enabled:
        return {
            "approved": False,
            "reason": "rewards_disabled",
            "points": 0,
            "unlocked_rewards": [],
        }

    if (
        settings.program_starts_at is None
        or timezone.now() < settings.program_starts_at
    ):
        return {
            "approved": False,
            "reason": "program_not_started",
            "points": 0,
            "unlocked_rewards": [],
        }

    User = get_user_model()

    User.objects.select_for_update().get(
        pk=claim.user_id,
    )

    total_points = 0
    unlocked_rewards = []

    actions = [
        (
            RewardActionRule.Action.REVIEW,
            "review_transaction",
        ),
    ]

    if has_tag_bonus:
        actions.append(
            (
                RewardActionRule.Action.REVIEW_TAG_BONUS,
                "tag_bonus_transaction",
            )
        )

    for action, transaction_field in actions:

        if getattr(claim, f"{transaction_field}_id"):
            continue

        try:
            rule = RewardActionRule.objects.get(
                action=action,
                is_active=True,
            )
        except RewardActionRule.DoesNotExist:
            continue

        # Si la misma acción ya fue premiada para esta cafetería,
        # no volvemos a acreditarla.
        already_rewarded = (
            UserPointTransaction.objects
            .filter(
                user=claim.user,
                cafe=claim.cafe,
                action=action,
                created_at__gte=settings.program_starts_at,
            )
            .exists()
        )

        if already_rewarded:
            continue

        point_transaction = (
            UserPointTransaction.objects.create(
                user=claim.user,
                cafe=claim.cafe,
                action=action,
                points=rule.points,
            )
        )

        setattr(
            claim,
            transaction_field,
            point_transaction,
        )

        total_points += rule.points

    current_balance = sum(
        UserPointTransaction.objects.filter(
            user=claim.user,
            created_at__gte=settings.program_starts_at,
        ).values_list(
            "points",
            flat=True,
        )
    )

    new_unlocks = _unlock_point_rewards(
        user=claim.user,
        balance=current_balance,
    )

    unlocked_rewards = [
        {
            "unlock_id": unlock.id,
            "points_required": unlock.points_required,
            "status": unlock.status,
        }
        for unlock in new_unlocks
    ]

    claim.status = RewardClaim.Status.APPROVED
    claim.resolved_by = resolved_by
    claim.resolved_at = timezone.now()

    claim.save(
        update_fields=[
            "status",
            "resolved_by",
            "resolved_at",
            "review_transaction",
            "tag_bonus_transaction",
            "updated_at",
        ]
    )

    return {
        "approved": True,
        "reason": "approved",
        "points": total_points,
        "unlocked_rewards": unlocked_rewards,
    }