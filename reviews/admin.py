# reviews/admin.py
from django.contrib import admin
from .models import Cafe, Review, CafeStat, ReviewLike, ReviewReport
from .claims import ClaimRequest, ClaimEvidence, ClaimStatus, ClaimMethod


@admin.register(Cafe)
class CafeAdmin(admin.ModelAdmin):
    # Lo más útil a la vista
    list_display = (
        "name", "location", "email", "phone",
        "visibility_level", "claim_status", "claimed_by",
    )
    list_filter = ("location", "visibility_level", "claim_status")
    search_fields = ("name", "location", "address", "phone", "email")
    ordering = ("name",)

    # Evitamos autocompletar de User si no está configurado; raw_id_fields siempre funciona
    raw_id_fields = ("claimed_by", "owner")

    fieldsets = (
        ("Identificación", {
            "fields": ("name", "address", "location", "phone", "email", "google_maps_url")
        }),
        ("Imágenes", {
            "fields": ("photo1", "photo1_title", "photo2", "photo2_title", "photo3", "photo3_title")
        }),
        ("Características", {
            "fields": (
                "is_vegan_friendly", "is_pet_friendly", "has_wifi", "has_outdoor_seating",
                "has_parking", "is_accessible", "has_vegetarian_options",
                "serves_breakfast", "serves_alcohol",
                "has_books_or_games", "has_air_conditioning",
                "has_gluten_free", "has_specialty_coffee", "has_artisanal_pastries",
                "accepts_cards", "gluten_free_options", "has_baby_changing",
                "has_power_outlets", "laptop_friendly", "quiet_space",
                "specialty_coffee", "brunch", "accepts_reservations",
            )
        }),
        ("Estado / Plan", {
            "fields": ("visibility_level", "claim_status", "claimed_by", "owner")
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