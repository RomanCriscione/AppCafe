from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView


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
                status=400,
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
                status=400,
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