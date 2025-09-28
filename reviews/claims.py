# reviews/models/claims.py
from __future__ import annotations
from datetime import timedelta
import secrets

from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils import timezone


class ClaimStatus(models.TextChoices):
    UNCLAIMED = "UNCLAIMED", "Sin reclamar"
    PENDING   = "PENDING", "Pendiente"
    VERIFIED  = "VERIFIED", "Verificado"
    REJECTED  = "REJECTED", "Rechazado"
    DISPUTED  = "DISPUTED", "En disputa"


class ClaimMethod(models.TextChoices):
    EMAIL_DOMAIN = "EMAIL_DOMAIN", "Email del negocio"
    PHOTO_CODE   = "PHOTO_CODE", "Fotos con código del día"
    PHONE        = "PHONE", "Verificación telefónica"


class ClaimRequest(models.Model):
    cafe   = models.ForeignKey("reviews.Cafe", on_delete=models.CASCADE, related_name="claim_requests")
    user   = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="claim_requests")

    status = models.CharField(max_length=12, choices=ClaimStatus.choices, default=ClaimStatus.PENDING)
    method = models.CharField(max_length=20, choices=ClaimMethod.choices)

    # Para EMAIL_DOMAIN
    email_to          = models.EmailField(blank=True, null=True)
    token_hash        = models.CharField(max_length=128, blank=True)  # hash del código
    token_expires_at  = models.DateTimeField(blank=True, null=True)

    # Evidencias / moderación
    notes_user        = models.TextField(blank=True)
    moderation_notes  = models.TextField(blank=True)
    approved_by       = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        unique_together = [("cafe", "user", "status")]  # evita múltiples PENDING iguales por usuario

    # --- helpers de token (email) ---
    def issue_email_code(self, length: int = 6, ttl_minutes: int = 60) -> str:
        """Genera código numérico y setea vencimiento."""
        code = "".join(secrets.choice("0123456789") for _ in range(length))
        self.token_hash = make_password(code)
        self.token_expires_at = timezone.now() + timedelta(minutes=ttl_minutes)
        self.save(update_fields=["token_hash", "token_expires_at", "updated_at"])
        return code

    def check_email_code(self, code: str) -> bool:
        if not self.token_hash or not self.token_expires_at:
            return False
        if timezone.now() > self.token_expires_at:
            return False
        return check_password(code, self.token_hash)


def evidence_upload_path(instance: "ClaimEvidence", filename: str) -> str:
    return f"claims/{instance.claim.id}/{filename}"


class ClaimEvidence(models.Model):
    claim   = models.ForeignKey(ClaimRequest, on_delete=models.CASCADE, related_name="evidences")
    file    = models.FileField(
        upload_to=evidence_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png", "pdf"])],
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
