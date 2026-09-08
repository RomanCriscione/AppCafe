from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from .models import (
    RewardActionRule,
    RewardSettings,
    UserPointTransaction,
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
    }