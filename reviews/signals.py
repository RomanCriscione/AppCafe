from typing import Iterable, Optional, Tuple

from django.conf import settings
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.core.mail import EmailMultiAlternatives
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.template import TemplateDoesNotExist
from django.urls import reverse
from django.contrib.sites.models import Site

from .models import Review, ReviewReport


# -----------------------------
# Cache: invalidación fragmento
# -----------------------------
def _invalidate_cafe_reviews_cache(cafe_id: int, extra_user_ids: Optional[Iterable[int]] = None) -> None:
    """
    Invalida el fragment cacheado de la lista de reseñas del detalle del café.

    El template usa:
        {% cache 600 cafe_reviews_list cafe.id user.id %}

    Eso significa que la key varía por (cafe_id, user_id).
    No podemos borrar *todas* las combinaciones de usuarios, pero sí:
      - las variantes anónimas ("", "None")
      - y opcionalmente algunas ids relevantes (autor de la reseña, dueño)
    """
    user_keys = ["", "None"]
    if extra_user_ids:
        user_keys.extend([str(uid) for uid in extra_user_ids if uid])

    for u in user_keys:
        key = make_template_fragment_key("cafe_reviews_list", [cafe_id, u])
        cache.delete(key)


# -----------------------------
# Sitemap ping (compat Django 5)
# -----------------------------
def _safe_ping_sitemap() -> None:
    """
    Intenta notificar a buscadores que cambió el contenido.
    - No explota en dev/CI.
    - En prod intenta ping a Google/Bing con GET a sus endpoints.
    """
    # En dev no hacemos nada
    if getattr(settings, "DEBUG", False):
        return

    # Construimos la URL absoluta del sitemap.xml usando Sites
    try:
        site = Site.objects.get_current()
        domain = site.domain.strip()
        if not domain:
            return
        if not domain.startswith("http"):
            sitemap_url = f"https://{domain}/sitemap.xml"
        else:
            sitemap_url = f"{domain.rstrip('/')}/sitemap.xml"
    except Exception:
        return

    # Pings “best effort” (si fallan, seguimos)
    try:
        import urllib.parse
        import urllib.request

        encoded = urllib.parse.quote(sitemap_url, safe="")
        endpoints = [
            f"https://www.google.com/ping?sitemap={encoded}",
            f"https://www.bing.com/ping?sitemap={encoded}",
        ]
        for url in endpoints:
            try:
                urllib.request.urlopen(url, timeout=2)  # no bloqueamos el request principal
            except Exception:
                pass
    except Exception:
        pass


@receiver(post_save, sender=Review)
def _review_saved_invalidate(sender, instance: Review, created: bool, **kwargs):
    # Autor y dueño son buenos candidatos para invalidar su versión cacheada
    extra = [getattr(instance, "user_id", None), getattr(instance.cafe, "owner_id", None)]
    _invalidate_cafe_reviews_cache(instance.cafe_id, extra_user_ids=extra)
    # Nuevo contenido público: avisamos a buscadores (seguro/no bloqueante)
    _safe_ping_sitemap()


@receiver(post_delete, sender=Review)
def _review_deleted_invalidate(sender, instance: Review, **kwargs):
    extra = [getattr(instance, "user_id", None), getattr(instance.cafe, "owner_id", None)]
    _invalidate_cafe_reviews_cache(instance.cafe_id, extra_user_ids=extra)
    _safe_ping_sitemap()


# ----------------------------------------
# Emails al dueño: nueva reseña / denuncia
# ----------------------------------------
def _render_email(subject_tpl: str, text_tpl: str, html_tpl: str, ctx: dict) -> Tuple[str, str, str]:
    """
    Intenta renderizar subject, texto y HTML desde templates.
    Si falta algún template, usa un fallback simple.
    """
    # Subject
    try:
        subject = render_to_string(subject_tpl, ctx).strip()
    except TemplateDoesNotExist:
        cafe = ctx.get("cafe")
        subject = f"Novedades en {getattr(cafe, 'name', 'tu cafetería')}"

    # Texto
    try:
        text_body = render_to_string(text_tpl, ctx)
    except TemplateDoesNotExist:
        # Fallback muy básico
        review = ctx.get("review")
        detail_url = ctx.get("detail_url", "#")
        text_body = (
            f"Novedades en {ctx.get('cafe')}\n\n"
            f"Usuario: {getattr(getattr(review, 'user', None), 'username', '(desconocido)')}\n"
            f"Puntaje: {getattr(review, 'rating', '-')}\n\n"
            f"Ver: {detail_url}\n"
        )

    # HTML
    try:
        html_body = render_to_string(html_tpl, ctx)
    except TemplateDoesNotExist:
        html_body = text_body.replace("\n", "<br>")

    return subject, text_body, html_body


def _send_owner_email(subject_tpl: str, text_tpl: str, html_tpl: str, ctx: dict, to_email: str) -> None:
    subject, text_body, html_body = _render_email(subject_tpl, text_tpl, html_tpl, ctx)
    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@gota.local"),
        to=[to_email],
    )
    msg.attach_alternative(html_body, "text/html")
    # No interrumpimos el flujo si el envío falla
    msg.send(fail_silently=True)


@receiver(post_save, sender=Review)
def _notify_owner_new_review(sender, instance: Review, created: bool, **kwargs):
    """Email al dueño cuando se crea una reseña nueva."""
    if not created:
        return

    cafe = instance.cafe
    owner = getattr(cafe, "owner", None)
    if not owner or not owner.email:
        return

    ctx = {
        "cafe": cafe,
        "review": instance,
        # URLs relativas (si querés absolutas, podés anteponer un DOMAIN del settings)
        "detail_url": reverse("reviews:cafe_detail", kwargs={"cafe_id": cafe.id}),
        "owner_reply_url": reverse("reviews:owner_reviews"),
    }

    _send_owner_email(
        subject_tpl="emails/owner_new_review_subject.txt",
        text_tpl="emails/owner_new_review.txt",
        html_tpl="emails/owner_new_review.html",
        ctx=ctx,
        to_email=owner.email,
    )


@receiver(post_save, sender=ReviewReport)
def _notify_owner_review_report(sender, instance: ReviewReport, created: bool, **kwargs):
    """Email al dueño cuando alguien denuncia una reseña de su local."""
    if not created:
        return

    review = instance.review
    cafe = review.cafe
    owner = getattr(cafe, "owner", None)
    if not owner or not owner.email:
        return

    ctx = {
        "cafe": cafe,
        "review": review,
        "report": instance,
        "detail_url": reverse("reviews:cafe_detail", kwargs={"cafe_id": cafe.id}),
    }

    _send_owner_email(
        subject_tpl="emails/owner_review_report_subject.txt",
        text_tpl="emails/owner_review_report.txt",
        html_tpl="emails/owner_review_report.html",
        ctx=ctx,
        to_email=owner.email,
    )
