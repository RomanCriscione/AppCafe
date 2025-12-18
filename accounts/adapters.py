from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.utils import user_email
from allauth.account.models import EmailAddress


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        """
        Si el usuario ya existe por email, vinculamos la cuenta social
        en lugar de crear un usuario nuevo.
        """
        email = user_email(sociallogin.user)

        if not email:
            return

        try:
            email_address = EmailAddress.objects.get(email__iexact=email)
        except EmailAddress.DoesNotExist:
            return

        user = email_address.user

        # Si ya tiene social account, no hacemos nada
        if sociallogin.is_existing:
            return

        # Vincular cuenta social al usuario existente
        sociallogin.connect(request, user)
