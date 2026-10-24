# reviews/admin.py
from django.contrib import admin, messages
from django.utils import timezone
from django.db.models import Count, Q
from django.conf import settings
from django.core.mail import send_mail

from .rewards import (
    approve_reward_claim,
    _unlock_point_rewards,
)
from .sensory_tags import SENSORY_REVIEW_TAG_NAMES


from .models import (
    Cafe,
    Review,
    CafeStat,
    ReviewLike,
    ReviewReport,
    CafeWhisper,
    RewardActionRule,
    RewardSettings,
    CafeReward,
    UserCoupon,
    UserRewardUnlock,
    UserPointTransaction,
    CafeCheckIn,
    RewardClaim,
)

from .claims import (
    ClaimRequest,
    ClaimEvidence,
    ClaimStatus,
    ClaimMethod,
)

from import_export.admin import ImportExportModelAdmin

def get_reward_statistics():
    now = timezone.now()

    unlocks = UserRewardUnlock.objects.all()
    coupons = UserCoupon.objects.all()

    total_unlocks = unlocks.count()

    pending_unlocks = unlocks.filter(
        status=UserRewardUnlock.Status.PENDING
    ).count()

    claimed_unlocks = unlocks.filter(
        status=UserRewardUnlock.Status.CLAIMED
    ).count()

    total_coupons = coupons.count()

    used_coupons = coupons.filter(
        status=UserCoupon.Status.USED
    ).count()

    expired_coupons = coupons.filter(
        Q(status=UserCoupon.Status.EXPIRED)
        | Q(
            status=UserCoupon.Status.AVAILABLE,
            expires_at__lte=now,
        )
    ).count()

    cancelled_coupons = coupons.filter(
        status=UserCoupon.Status.CANCELLED
    ).count()

    available_coupons = coupons.filter(
        status=UserCoupon.Status.AVAILABLE,
        expires_at__gt=now,
    ).count()

    return {
        "total_unlocks": total_unlocks,
        "pending_unlocks": pending_unlocks,
        "claimed_unlocks": claimed_unlocks,
        "total_coupons": total_coupons,
        "used_coupons": used_coupons,
        "expired_coupons": expired_coupons,
        "cancelled_coupons": cancelled_coupons,
        "available_coupons": available_coupons,
        "claim_rate": (
            round(claimed_unlocks / total_unlocks * 100, 1)
            if total_unlocks else 0
        ),
        "usage_rate": (
            round(used_coupons / total_coupons * 100, 1)
            if total_coupons else 0
        ),
    }


def get_cafe_reward_statistics():
    now = timezone.now()

    cafes = (
        UserCoupon.objects
        .values("cafe_id", "cafe__name")
        .annotate(
            total_coupons=Count("id"),
            unique_users=Count("user_id", distinct=True),
            used_coupons=Count(
                "id",
                filter=Q(status=UserCoupon.Status.USED),
            ),
            expired_coupons=Count(
                "id",
                filter=(
                    Q(status=UserCoupon.Status.EXPIRED)
                    | Q(
                        status=UserCoupon.Status.AVAILABLE,
                        expires_at__lte=now,
                    )
                ),
            ),
            available_coupons=Count(
                "id",
                filter=Q(
                    status=UserCoupon.Status.AVAILABLE,
                    expires_at__gt=now,
                ),
            ),
            welcome_coupons=Count(
                "id",
                filter=Q(
                    reward_unlock__unlock_type=(
                        UserRewardUnlock.UnlockType.WELCOME
                    )
                ),
            ),
            milestone_coupons=Count(
                "id",
                filter=Q(
                    reward_unlock__unlock_type=(
                        UserRewardUnlock.UnlockType.MILESTONE
                    )
                ),
            ),
        )
        .order_by("-total_coupons", "cafe__name")
    )


    results = []

    for cafe in cafes:
        total = cafe["total_coupons"]
        used = cafe["used_coupons"]

        cafe["usage_rate"] = (
            round(used / total * 100, 1)
            if total else 0
        )

        results.append(cafe)

    return results


@admin.register(Cafe)
class CafeAdmin(ImportExportModelAdmin):
    list_display = (
        "name", "location", "email", "phone",
        "visibility_level", "claim_status", "claimed_by",
    )

    list_filter = (
        "location",
        "visibility_level",
        "claim_status",

        # Filtros útiles reales
        "has_wifi",
        "is_pet_friendly",
        "has_specialty_coffee",
        "laptop_friendly",
        "quiet_space",
    )

    search_fields = ("name", "location", "address", "phone", "email")
    ordering = ("name",)
    raw_id_fields = ("claimed_by", "owner")

    fieldsets = (
        ("Identificación", {
            "fields": (
                "name", "address", "location",
                "phone", "email", "google_maps_url",
            )
        }),

        ("Imágenes", {
            "fields": (
                "photo1", "photo1_title",
                "photo2", "photo2_title",
                "photo3", "photo3_title",
            )
        }),

        ("Características", {
            "fields": (
                # Servicios / infraestructura
                "has_wifi",
                "has_air_conditioning",
                "has_power_outlets",
                "has_outdoor_seating",
                "has_parking",
                "is_accessible",
                "accepts_cards",
                "accepts_reservations",
                "has_baby_changing",

                # Mascotas
                "is_pet_friendly",

                # Oferta gastronómica
                "has_specialty_coffee",
                "serves_brunch",
                "serves_breakfast",
                "serves_alcohol",
                "has_artisanal_pastries",
                "offers_ice_cream",

                # Opciones alimentarias
                "is_vegan_friendly",
                "has_vegetarian_options",
                "has_gluten_free_options",

                # Uso del espacio
                "laptop_friendly",
                "quiet_space",

                # Extras
                "has_books_or_games",
            )
        }),

        ("Estado / Plan", {
            "fields": (
                "visibility_level",
                "claim_status",
                "claimed_by",
                "owner",
            )
        }),

        ("Ubicación", {
            "fields": ("latitude", "longitude")
        }),
    )



@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("cafe", "user", "rating", "created_at")
    list_filter = ("cafe", "rating", "created_at")
    search_fields = ("comment",)
    date_hierarchy = "created_at"
    raw_id_fields = ("cafe", "user")


@admin.register(CafeStat)
class CafeStatAdmin(admin.ModelAdmin):
    list_display = ("cafe", "date", "views")
    list_filter = ("cafe", "date")
    date_hierarchy = "date"
    raw_id_fields = ("cafe",)


class ClaimEvidenceInline(admin.TabularInline):
    model = ClaimEvidence
    extra = 0
    readonly_fields = ("uploaded_at",)


@admin.register(ClaimRequest)
class ClaimRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "cafe", "user", "status", "method", "email_to", "created_at")
    list_filter = ("status", "method", "created_at")
    search_fields = ("cafe__name", "user__username", "email_to")
    date_hierarchy = "created_at"
    raw_id_fields = ("cafe", "user", "approved_by")
    inlines = (ClaimEvidenceInline,)


@admin.register(ClaimEvidence)
class ClaimEvidenceAdmin(admin.ModelAdmin):
    list_display = ("id", "claim", "uploaded_at")
    search_fields = ("claim__cafe__name",)
    raw_id_fields = ("claim",)

@admin.register(ReviewLike)
class ReviewLikeAdmin(admin.ModelAdmin):
    list_display = ("review", "user", "created_at")
    list_filter = ("created_at",)
    search_fields = ("review__cafe__name", "user__username")
    raw_id_fields = ("review", "user")
    date_hierarchy = "created_at"


@admin.register(ReviewReport)
class ReviewReportAdmin(admin.ModelAdmin):
    list_display = ("id", "review", "user", "reason", "status", "created_at", "resolved_at")
    list_filter = ("status", "reason", "created_at")
    search_fields = ("review__comment", "user__username")
    raw_id_fields = ("review", "user", "resolved_by")
    date_hierarchy = "created_at"
    fieldsets = (
        ("Reporte", {"fields": ("review", "user", "reason", "comment")}),
        ("Estado", {"fields": ("status", "resolved_by", "resolved_at", "resolution_notes")}),
    )

@admin.register(CafeWhisper)
class CafeWhisperAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "cafe",
        "user",
        "text",
        "reports_count",
        "is_hidden",
        "created_at",
    )

    list_filter = (
        "is_hidden",
        "created_at",
        "cafe",
    )

    search_fields = (
        "text",
        "cafe__name",
        "user__username",
    )

    raw_id_fields = (
        "cafe",
        "user",
    )

    date_hierarchy = "created_at"

    actions = [
        "hide_whispers",
        "show_whispers",
    ]

    @admin.action(description="Ocultar huellas seleccionadas")
    def hide_whispers(self, request, queryset):
        queryset.update(is_hidden=True)

    @admin.action(description="Mostrar huellas seleccionadas")
    def show_whispers(self, request, queryset):
        queryset.update(is_hidden=False)

@admin.register(RewardActionRule)
class RewardActionRuleAdmin(admin.ModelAdmin):
    list_display = (
        "action",
        "points",
        "is_active",
        "max_rewards_per_window",
        "window_hours",
        "repeat_after_days",
    )

    list_filter = (
        "is_active",
    )


@admin.register(RewardSettings)
class RewardSettingsAdmin(admin.ModelAdmin):
    list_display = (
        "rewards_enabled",
        "program_starts_at",
        "welcome_reward_enabled",
        "reward_thresholds",
        "reward_repeat_every",
        "check_in_radius_meters",
        "check_in_valid_hours",
        "welcome_reward_radius_km",
        "updated_at",
    )

    list_display_links = (
        "check_in_radius_meters",
    )

    def has_add_permission(self, request):
        if RewardSettings.objects.exists():
            return False
        return super().has_add_permission(request)


@admin.register(CafeReward)
class CafeRewardAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "cafe",
        "reward_type",
        "unlock_type",
        "is_welcome_reward",
        "priority",
        "stock",
        "is_active",
    )

    list_filter = (
        "reward_type",
        "unlock_type",
        "is_welcome_reward",
        "is_active",
    )

    search_fields = (
        "name",
        "cafe__name",
        "user_text",
    )

    raw_id_fields = (
        "cafe",
    )

@admin.register(UserRewardUnlock)
class UserRewardUnlockAdmin(admin.ModelAdmin):
    actions = ("send_pending_reward_reminders",)
    list_display = (
        "user",
        "unlock_type",
        "points_required",
        "status",
        "unlocked_at",
        "claimed_at",
        "coupon",
        "reminder_sent_at",
    )

    list_filter = (
        "unlock_type",
        "status",
        "unlocked_at",
    )

    search_fields = (
        "user__email",
        "user__username",
        "coupon__code",
    )

    raw_id_fields = (
        "user",
        "coupon",
    )

    readonly_fields = (
        "user",
        "unlock_type",
        "points_required",
        "status",
        "coupon",
        "unlocked_at",
        "claimed_at",
    )

    date_hierarchy = "unlocked_at"

    change_list_template = "admin/reviews/userrewardunlock/change_list.html"


    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}

        extra_context["reward_stats"] = get_reward_statistics()
        extra_context["cafe_reward_stats"] = get_cafe_reward_statistics()

        return super().changelist_view(
            request,
            extra_context=extra_context,
        )

    @admin.action(description="Enviar recordatorio de beneficio pendiente")
    def send_pending_reward_reminders(self, request, queryset):
        pending = (
            queryset.filter(
                status=UserRewardUnlock.Status.PENDING,
                coupon__isnull=True,
                reminder_sent_at__isnull=True,
            )
            .select_related("user")
            .order_by("user_id", "id")
        )

        users_sent = set()
        sent_count = 0
        skipped_count = 0

        for unlock in pending:
            user = unlock.user

            if user.pk in users_sent:
                continue

            email = (user.email or "").strip()

            if not email:
                skipped_count += 1
                continue

            subject = "☕ ¡Tenés un beneficio esperando en Gota!"

            message = (
                "¡Hola!\n\n"
                "¿Sabías que tenés un beneficio esperando en Gota? ☕🎁\n\n"
                "Ya desbloqueaste la posibilidad de elegir un beneficio "
                "en una cafetería, pero todavía no lo aprovechaste.\n\n"
                "Puede ser un descuento, un 2x1 o alguna sorpresa "
                "para tu próximo café.\n\n"
                "Para aprovecharlo:\n\n"
                "1. Entrá a Gota con tu cuenta.\n"
                "2. Ingresá a la sección Mis Gotas.\n"
                "3. Elegí uno de los beneficios disponibles.\n"
                "4. Obtené tu cupón para usarlo en la cafetería.\n\n"
                "Entrá a Gota: https://gogota.ar/\n\n"
                "¡Tu próximo café puede venir con algo extra!\n\n"
                "Nos vemos en Gota ☕\n\n"
                "El equipo de Gota"
            )

            try:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
            except Exception:
                skipped_count += 1
                continue

            UserRewardUnlock.objects.filter(
                user_id=user.pk,
                status=UserRewardUnlock.Status.PENDING,
                coupon__isnull=True,
                reminder_sent_at__isnull=True,
            ).update(reminder_sent_at=timezone.now())

            users_sent.add(user.pk)
            sent_count += 1

        if sent_count:
            self.message_user(
                request,
                f"Se enviaron {sent_count} recordatorio(s).",
                level=messages.SUCCESS,
            )

        if skipped_count:
            self.message_user(
                request,
                f"{skipped_count} usuario(s) no recibieron el correo.",
                level=messages.WARNING,
            )


    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(UserCoupon)
class UserCouponAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "user",
        "cafe",
        "reward",
        "status",
        "obtained_at",
        "expires_at",
        "used_at",
    )

    list_filter = (
        "status",
        "cafe",
        "obtained_at",
    )

    search_fields = (
        "code",
        "user__email",
        "cafe__name",
    )

    raw_id_fields = (
        "user",
        "cafe",
        "reward",
        "used_by",
    )

    readonly_fields = (
        "code",
        "qr_token",
        "obtained_at",
        "used_at",
    )


@admin.register(UserPointTransaction)
class UserPointTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "cafe",
        "action",
        "points",
        "created_at",
    )

    list_filter = (
        "action",
        "created_at",
    )

    search_fields = (
        "user__email",
        "cafe__name",
    )

    raw_id_fields = (
        "user",
        "cafe",
    )

    date_hierarchy = "created_at"

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        if (
            not change
            and obj.action == RewardActionRule.Action.MANUAL_ADJUSTMENT
        ):
            balance = sum(
                UserPointTransaction.objects
                .filter(user=obj.user)
                .values_list("points", flat=True)
            )

            _unlock_point_rewards(
                user=obj.user,
                balance=balance,
            )

            self.message_user(
                request,
                f"Se acreditaron {obj.points:+d} Gotas a {obj.user}. "
                f"Saldo actual: {balance} Gotas.",
                level=messages.SUCCESS,
            )


@admin.register(CafeCheckIn)
class CafeCheckInAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "cafe",
        "distance_meters",
        "is_valid",
        "created_at",
    )

    list_filter = (
        "is_valid",
        "created_at",
    )

    search_fields = (
        "user__email",
        "cafe__name",
    )

    raw_id_fields = (
        "user",
        "cafe",
    )

    date_hierarchy = "created_at"
@admin.register(RewardClaim)
class RewardClaimAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "cafe",
        "review",
        "status",
        "visited_at",
        "created_at",
        "resolved_by",
    )

    list_filter = (
        "status",
        "created_at",
    )

    search_fields = (
        "user__email",
        "cafe__name",
        "explanation",
    )

    raw_id_fields = (
        "user",
        "cafe",
        "review",
        "resolved_by",
    )

    readonly_fields = (
        "status",
        "resolved_by",
        "resolved_at",
        "review_transaction",
        "tag_bonus_transaction",
        "created_at",
        "updated_at",
    )

    actions = (
        "approve_selected_claims",
        "reject_selected_claims",
    )

    date_hierarchy = "created_at"

    @admin.action(description="Aprobar reclamos seleccionados")
    def approve_selected_claims(self, request, queryset):
        approved_count = 0
        skipped_count = 0
        total_points = 0

        for claim in queryset:
            has_tag_bonus = (
                claim.review is not None
                and claim.review.tags.filter(
                    name__in=SENSORY_REVIEW_TAG_NAMES
                ).exists()
            )

            result = approve_reward_claim(
                claim=claim,
                resolved_by=request.user,
                has_tag_bonus=has_tag_bonus,
            )

            if result["approved"]:
                approved_count += 1
                total_points += result["points"]
            else:
                skipped_count += 1

        if approved_count:
            self.message_user(
                request,
                (
                    f"{approved_count} reclamo(s) aprobado(s). "
                    f"Se acreditaron {total_points} Gotas en total."
                ),
                level=messages.SUCCESS,
            )

        if skipped_count:
            self.message_user(
                request,
                (
                    f"{skipped_count} reclamo(s) no pudieron "
                    f"procesarse o ya estaban resueltos."
                ),
                level=messages.WARNING,
            )

    @admin.action(description="Rechazar reclamos seleccionados")
    def reject_selected_claims(self, request, queryset):
        pending_claims = queryset.filter(
            status=RewardClaim.Status.PENDING,
        )

        rejected_count = pending_claims.update(
            status=RewardClaim.Status.REJECTED,
            resolved_by=request.user,
            resolved_at=timezone.now(),
        )

        if rejected_count:
            self.message_user(
                request,
                f"{rejected_count} reclamo(s) rechazado(s).",
                level=messages.SUCCESS,
            )
        else:
            self.message_user(
                request,
                "No había reclamos pendientes para rechazar.",
                level=messages.WARNING,
            )