# reviews/admin.py
# reviews/admin.py
from django.contrib import admin

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
    UserPointTransaction,
    CafeCheckIn,
)

from .claims import (
    ClaimRequest,
    ClaimEvidence,
    ClaimStatus,
    ClaimMethod,
)

from import_export.admin import ImportExportModelAdmin


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
        "check_in_radius_meters",
        "check_in_valid_hours",
        "welcome_reward_radius_km",
        "updated_at",
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
        "points_required",
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
