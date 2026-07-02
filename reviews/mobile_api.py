from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from reviews.models import CafeRelationship
from reviews.serializers import CafeRelationshipSerializer
from rest_framework.response import Response
from reviews.serializers import MobileUserSerializer


class MyMapAPIView(generics.ListAPIView):
    """
    GET /api/mobile/my-map/

    Devuelve el recorrido del usuario autenticado.
    """

    serializer_class = CafeRelationshipSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            CafeRelationship.objects
            .filter(user=self.request.user)
            .select_related("cafe")
            .order_by("-updated_at")
        )

class MeAPIView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MobileUserSerializer

    def get(self, request):
        serializer = MobileUserSerializer(
            request.user,
            context={"request": request},
        )

        return Response(serializer.data)