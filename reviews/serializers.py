# reviews/serializers.py
from rest_framework import serializers
from reviews.models import Cafe, Tag

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "category"]

class CafeSerializer(serializers.ModelSerializer):
    # Este campo viene anotado en la queryset (api.py)
    average_rating = serializers.FloatField(read_only=True)

    # Si querés devolver los nombres de tags:
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Cafe
        fields = [
            "id",
            "name",
            "address",
            "location",
            "latitude",
            "longitude",
            "has_wifi",
            "is_pet_friendly",
            "is_vegan_friendly",
            "average_rating",
            "tags",
        ]
