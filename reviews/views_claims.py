# reviews/views_claims.py
from __future__ import annotations
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from reviews.models import Cafe
from .forms import ClaimStartForm, ClaimVerifyEmailForm, ClaimEvidenceForm
from .claims import ClaimRequest, ClaimStatus, ClaimMethod, ClaimEvidence
from reviews.utils.ownership import assign_owner


RATE_LIMIT_KEY = "claim_attempts_u{uid}"
RATE_LIMIT_MAX = 3           # intentos por día
RATE_LIMIT_TTL = 60 * 60 * 24


def _rate_limit(user) -> bool:
    if not user.is_authenticated:
        return False
    key = RATE_LIMIT_KEY.format(uid=user.id)
    val = cache.get(key, 0)
    if val >= RATE_LIMIT_MAX:
        return True
    cache.set(key, val + 1, RATE_LIMIT_TTL)
    return False


@login_required
def claim_start(request, cafe_id):
    cafe = get_object_or_404(Cafe, pk=cafe_id)

    if cafe.claim_status == ClaimStatus.VERIFIED:
        messages.info(request, "Este local ya está verificado.")
        return redirect("reviews:cafe_detail", cafe_id=cafe.id)

    if request.method == "POST":
        if _rate_limit(request.user):
            messages.error(request, "Demasiados intentos hoy. Probá de nuevo mañana.")
            return redirect("reviews:cafe_detail", cafe_id=cafe.id)

        form = ClaimStartForm(request.POST, cafe=cafe)
        if form.is_valid():
            # Reusar un claim PENDING existente para evitar IntegrityError (unique constraint)
            claim = ClaimRequest.objects.filter(
                cafe=cafe, user=request.user, status=ClaimStatus.PENDING
            ).first()

            if not claim:
                claim = form.save(commit=False)
                claim.cafe = cafe
                claim.user = request.user
                claim.status = ClaimStatus.PENDING
            else:
                # Si ya existe, actualizamos método/datos con lo del form
                form_claim = form.save(commit=False)
                claim.method = form_claim.method

            # Si es email, seteamos email_to
            if claim.method == ClaimMethod.EMAIL_DOMAIN and getattr(cafe, "email", None):
                claim.email_to = cafe.email

            try:
                claim.save()
            except IntegrityError:
                # En caso de carrera, recuperamos el existente
                claim = ClaimRequest.objects.get(
                    cafe=cafe, user=request.user, status=ClaimStatus.PENDING
                )

            if claim.method == ClaimMethod.EMAIL_DOMAIN and claim.email_to:
                code = claim.issue_email_code()
                send_mail(
                    subject=f"Código para reclamar {cafe.name}",
                    message=f"Tu código es: {code}\nVence en 60 minutos.",
                    from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                    recipient_list=[claim.email_to],
                    fail_silently=True,
                )
                messages.success(request, f"Te enviamos un código a {claim.email_to}.")
                return redirect("reviews:claim_verify_email", cafe_id=cafe.id, claim_id=claim.id)

            elif claim.method == ClaimMethod.PHOTO_CODE:
                messages.info(request, "Subí las evidencias para que podamos verificarte.")
                return redirect("reviews:claim_upload_evidence", cafe_id=cafe.id, claim_id=claim.id)

            else:  # PHONE
                messages.info(request, "Recibimos tu solicitud. Te contactaremos para verificar por teléfono.")
                return redirect("reviews:cafe_detail", cafe_id=cafe.id)
    else:
        form = ClaimStartForm(cafe=cafe)

    return render(request, "reviews/claims/start.html", {"cafe": cafe, "form": form})


@login_required
def claim_verify_email(request, cafe_id, claim_id):
    cafe   = get_object_or_404(Cafe, pk=cafe_id)
    claim  = get_object_or_404(ClaimRequest, pk=claim_id, cafe=cafe, user=request.user)

    if claim.method != ClaimMethod.EMAIL_DOMAIN:
        return redirect("reviews:claim_start", cafe_id=cafe.id)

    if request.method == "POST":
        form = ClaimVerifyEmailForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data["code"].strip()
            if claim.check_email_code(code):
                with transaction.atomic():
                    assign_owner(cafe, request.user)
                    claim.status = ClaimStatus.VERIFIED
                    claim.approved_by = request.user  # auto-aprobado por verificación
                    claim.save(update_fields=["status", "approved_by", "updated_at"])
                messages.success(request, "¡Listo! Ya sos dueño/verificado de este local.")
                return redirect("reviews:cafe_detail", cafe_id=cafe.id)
            messages.error(request, "Código inválido o vencido.")
    else:
        form = ClaimVerifyEmailForm()

    return render(request, "reviews/claims/verify_email.html", {"cafe": cafe, "claim": claim, "form": form})


@login_required
def claim_upload_evidence(request, cafe_id, claim_id):
    cafe  = get_object_or_404(Cafe, pk=cafe_id)
    claim = get_object_or_404(ClaimRequest, pk=claim_id, cafe=cafe, user=request.user)

    if claim.method != ClaimMethod.PHOTO_CODE:
        return redirect("reviews:claim_start", cafe_id=cafe.id)

    if request.method == "POST":
        form = ClaimEvidenceForm(request.POST, request.FILES)
        if form.is_valid():
            files = form.cleaned_data["files"]
            for f in files:
                ClaimEvidence.objects.create(claim=claim, file=f)
            messages.success(request, "Recibimos tus evidencias. Un moderador las revisará pronto.")
            return redirect("reviews:cafe_detail", cafe_id=cafe.id)
    else:
        form = ClaimEvidenceForm()

    # código efímero del día (solo visual; no lo persistimos)
    daily_code = f"GOTA-{timezone.localdate().strftime('%m%d')}"
    return render(
        request,
        "reviews/claims/evidence.html",
        {"cafe": cafe, "claim": claim, "form": form, "daily_code": daily_code},
    )
