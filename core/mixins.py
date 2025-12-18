from allauth.account.models import EmailAddress
from django.core.exceptions import PermissionDenied


class EmailVerifiedRequiredMixin:
    """
    Requiere que el usuario tenga al menos un email verificado.
    Usar SOLO en vistas que modifican datos.
    """

    def dispatch(self, request, *args, **kwargs):
        user = request.user

        if not user.is_authenticated:
            raise PermissionDenied("Debés iniciar sesión.")

        is_verified = EmailAddress.objects.filter(
            user=user,
            verified=True
        ).exists()

        if not is_verified:
            raise PermissionDenied(
                "Debés confirmar tu email para realizar esta acción."
            )

        return super().dispatch(request, *args, **kwargs)
