from django.conf import settings
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model

import jwt
import requests

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from reviews.claims import ClaimStatus
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from allauth.account.forms import ResetPasswordForm


User = get_user_model()


class MobileLoginAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        email = request.data.get("email", "").strip().lower()
        password = request.data.get("password", "")

        if not email or not password:
            return Response(
                {
                    "success": False,
                    "message": "Email y contraseña son obligatorios.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(
            request,
            username=email,
            password=password,
        )

        if user is None:
            return Response(
                {
                    "success": False,
                    "message": "Email o contraseña incorrectos.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        token, _ = Token.objects.get_or_create(user=user)

        return Response(
            {
                "success": True,
                "token": token.key,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "name": user.first_name or user.username,
                },
            }
        )
class MobileGoogleLoginAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        google_id_token = request.data.get(
            "id_token",
            "",
        ).strip()

        if not google_id_token:
            return Response(
                {
                    "success": False,
                    "message": "Falta el token de Google.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            payload = id_token.verify_oauth2_token(
                google_id_token,
                google_requests.Request(),
                settings.GOOGLE_MOBILE_CLIENT_ID,
            )
        except Exception:
            return Response(
                {
                    "success": False,
                    "message": "No pudimos validar tu cuenta de Google.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        email = (
            payload.get("email", "")
            .strip()
            .lower()
        )

        email_verified = payload.get(
            "email_verified",
            False,
        )

        if not email or not email_verified:
            return Response(
                {
                    "success": False,
                    "message": "Google no confirmó un email válido.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        name = (
            payload.get("given_name")
            or payload.get("name")
            or email.split("@")[0]
        )

        user = User.objects.filter(
            email__iexact=email,
        ).first()

        if user is None:
            user = User.objects.create_user(
                username=email,
                email=email,
                first_name=name,
            )

            user.set_unusable_password()
            user.save(
                update_fields=["password"],
            )

        token, _ = Token.objects.get_or_create(
            user=user,
        )

        return Response(
            {
                "success": True,
                "token": token.key,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "name": (
                        user.first_name
                        or user.username
                    ),
                },
            },
            status=status.HTTP_200_OK,
        )

class MobileAppleLoginAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        apple_id_token = request.data.get(
            "id_token",
            "",
        ).strip()

        name = request.data.get(
            "name",
            "",
        ).strip()

        if not apple_id_token:
            return Response(
                {
                    "success": False,
                    "message": "Falta el token de Apple.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            jwks_client = jwt.PyJWKClient(
                "https://appleid.apple.com/auth/keys"
            )

            signing_key = jwks_client.get_signing_key_from_jwt(
                apple_id_token
            )

            payload = jwt.decode(
                apple_id_token,
                signing_key.key,
                algorithms=["RS256"],
                audience="ar.gogota.app",
                issuer="https://appleid.apple.com",
            )

        except Exception:
            return Response(
                {
                    "success": False,
                    "message": "No pudimos validar tu cuenta de Apple.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        email = (
            payload.get("email", "")
            .strip()
            .lower()
        )

        if not email:
            return Response(
                {
                    "success": False,
                    "message": "Apple no confirmó un email válido.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.filter(
            email__iexact=email,
        ).first()

        if user is None:
            user = User.objects.create_user(
                username=email,
                email=email,
                first_name=name or email.split("@")[0],
            )

            user.set_unusable_password()
            user.save(
                update_fields=["password"],
            )

        elif name and not user.first_name:
            user.first_name = name
            user.save(
                update_fields=["first_name"],
            )

        token, _ = Token.objects.get_or_create(
            user=user,
        )

        return Response(
            {
                "success": True,
                "token": token.key,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "name": (
                        user.first_name
                        or user.username
                    ),
                },
            },
            status=status.HTTP_200_OK,
        )


class MobileRegisterAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):

        name = request.data.get("name", "").strip()
        email = request.data.get("email", "").strip().lower()
        password = request.data.get("password", "")

        if not name or not email or not password:
            return Response(
                {
                    "success": False,
                    "message": "Todos los campos son obligatorios.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(email=email).exists():
            return Response(
                {
                    "success": False,
                    "message": "Ya existe una cuenta con ese email.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=name,
        )

        token, _ = Token.objects.get_or_create(user=user)

        return Response(
            {
                "success": True,
                "token": token.key,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "name": user.first_name,
                },
            },
            status=status.HTTP_201_CREATED,
        )

class MobilePasswordResetAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        email = (
            request.data.get("email", "")
            .strip()
            .lower()
        )

        if not email:
            return Response(
                {
                    "success": False,
                    "message": "Ingresá tu email.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        form = ResetPasswordForm(
            data={
                "email": email,
            }
        )

        if not form.is_valid():
            return Response(
                {
                    "success": False,
                    "message": "Ingresá un email válido.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        form.save(request)

        return Response(
            {
                "success": True,
                "message": (
                    "Si existe una cuenta asociada a ese email, "
                    "te enviamos las instrucciones para restablecer "
                    "tu contraseña."
                ),
            },
            status=status.HTTP_200_OK,
        )

class MobileChangePasswordAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        current_password = request.data.get(
            "current_password",
            "",
        )

        new_password = request.data.get(
            "new_password",
            "",
        )

        confirm_password = request.data.get(
            "confirm_password",
            "",
        )

        if not new_password or not confirm_password:
            return Response(
                {
                    "success": False,
                    "message": "Completá la nueva contraseña.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if new_password != confirm_password:
            return Response(
                {
                    "success": False,
                    "message": "Las contraseñas nuevas no coinciden.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user.has_usable_password():
            if not current_password:
                return Response(
                    {
                        "success": False,
                        "message": "Ingresá tu contraseña actual.",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if not user.check_password(current_password):
                return Response(
                    {
                        "success": False,
                        "message": "La contraseña actual es incorrecta.",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        try:
            validate_password(
                new_password,
                user=user,
            )
        except ValidationError as error:
            return Response(
                {
                    "success": False,
                    "message": " ".join(error.messages),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.save(
            update_fields=["password"],
        )

        Token.objects.filter(
            user=user,
        ).delete()

        token = Token.objects.create(
            user=user,
        )

        return Response(
            {
                "success": True,
                "message": "Contraseña actualizada correctamente.",
                "token": token.key,
            },
            status=status.HTTP_200_OK,
        )


class MobileLogoutAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):

        Token.objects.filter(user=request.user).delete()

        return Response(
            {
                "success": True,
            }
        )


class MobileDeleteAccountAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = request.user

        # Liberar las cafeterías asociadas a esta cuenta
        user.cafes.update(
            owner=None,
            claim_status=ClaimStatus.UNCLAIMED,
        )

        Token.objects.filter(user=user).delete()

        user.delete()

        return Response(
            {
                "success": True,
                "message": "Tu cuenta fue eliminada correctamente.",
            },
            status=status.HTTP_200_OK,
        )

