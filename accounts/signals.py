from django.dispatch import receiver
from django.db.models.signals import post_save
from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings

from accounts.models import CustomUser
from accounts.utils.email_confirmation import create_email_confirmation_token


@receiver(post_save, sender=CustomUser)
def send_confirmation_email(sender, instance, created, **kwargs):
    if not created:
        return

    token_obj = create_email_confirmation_token(instance)

    confirm_url = (
        settings.SITE_URL +
        reverse("accounts:confirm_email", args=[str(token_obj.token)])
    )

    send_mail(
        subject="Confirmá tu email en Gota ☕",
        message=(
            "Gracias por registrarte en Gota.\n\n"
            "Confirmá tu email haciendo click acá:\n"
            f"{confirm_url}\n\n"
            "Este link vence en 24 horas."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[instance.email],
        fail_silently=True,
    )
