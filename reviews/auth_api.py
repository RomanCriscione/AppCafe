from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


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