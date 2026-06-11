from django.db.models import Count
from rest_framework import serializers
from reviews.models import Cafe, Tag



class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "category"]


class CafeSerializer(serializers.ModelSerializer):
    # Este campo viene anotado en la queryset (api.py)
    average_rating = serializers.FloatField(read_only=True)

    # Tags
    tags = TagSerializer(many=True, read_only=True)

    # Foto principal para Mobile
    photo1_url = serializers.SerializerMethodField()
    top_tags = serializers.SerializerMethodField()

    def get_photo1_url(self, obj):
        if obj.photo1:
            request = self.context.get("request")

            if request:
                return request.build_absolute_uri(obj.photo1.url)

            return obj.photo1.url

        return None
    
    def get_top_tags(self, obj):
        return list(
            Tag.objects
            .filter(reviews__cafe=obj)
            .annotate(num=Count("id"))
            .order_by("-num", "name")
            .values_list("name", flat=True)[:5]
        )

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
            "photo1_url",
            "top_tags",
            "tags",
        ]