from django.db.models import Count
from rest_framework import serializers
from reviews.models import Cafe, Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "category"]


class CafeSerializer(serializers.ModelSerializer):
    average_rating = serializers.FloatField(read_only=True)

    tags = TagSerializer(many=True, read_only=True)

    photo1_url = serializers.SerializerMethodField()
    photo2_url = serializers.SerializerMethodField()
    photo3_url = serializers.SerializerMethodField()

    top_tags = serializers.SerializerMethodField()

    def build_image_url(self, image_field):
        if image_field:
            request = self.context.get("request")

            if request:
                return request.build_absolute_uri(image_field.url)

            return image_field.url

        return None

    def get_photo1_url(self, obj):
        return self.build_image_url(obj.photo1)

    def get_photo2_url(self, obj):
        return self.build_image_url(obj.photo2)

    def get_photo3_url(self, obj):
        return self.build_image_url(obj.photo3)

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
            "photo2_url",
            "photo3_url",
            "top_tags",
            "tags",
        ]