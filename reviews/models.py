from django.conf import settings
from django.db import models
from django.db.models import Avg
from django.contrib.auth import get_user_model
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
import os

User = get_user_model()

class Tag(models.Model):
    CATEGORY_CHOICES = [
        ("sensorial", "☕ Experiencia sensorial"),
        ("ambiente", "💬 Ambiente humano"),
        ("hacer", "✍️ Para hacer cosas"),
        ("estetica", "🌿 Estética y atmósfera"),
        ("emocional", "🧠 Estados mentales"),
    ]

    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)

    def __str__(self):
        return self.name


class Cafe(models.Model):
    name = models.CharField(max_length=100, unique=True)
    address = models.CharField(max_length=255)
    location = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    google_maps_url = models.URLField(blank=True, null=True)

    photo1 = models.ImageField(upload_to='cafes/', blank=True, null=True)
    photo1_title = models.CharField(max_length=200, blank=True, null=True)
    photo2 = models.ImageField(upload_to='cafes/', blank=True, null=True)
    photo2_title = models.CharField(max_length=200, blank=True, null=True)
    photo3 = models.ImageField(upload_to='cafes/', blank=True, null=True)
    photo3_title = models.CharField(max_length=200, blank=True, null=True)

    # Características
    is_vegan_friendly = models.BooleanField(default=False, verbose_name="Vegano friendly")
    is_pet_friendly = models.BooleanField(default=False, verbose_name="Pet friendly")
    has_wifi = models.BooleanField(default=False, verbose_name="WiFi")
    has_outdoor_seating = models.BooleanField(default=False, verbose_name="Mesas al aire libre")
    has_parking = models.BooleanField(default=False, verbose_name="Estacionamiento disponible")
    is_accessible = models.BooleanField(default=False, verbose_name="Accesible para personas con movilidad reducida")
    has_vegetarian_options = models.BooleanField(default=False, verbose_name="Opciones vegetarianas")
    serves_breakfast = models.BooleanField(default=False, verbose_name="Sirve desayuno")
    serves_alcohol = models.BooleanField(default=False, verbose_name="Sirve alcohol")
    has_books_or_games = models.BooleanField(default=False, verbose_name="Libros o juegos disponibles")
    has_air_conditioning = models.BooleanField(default=False, verbose_name="Aire acondicionado")

    # Otras opciones extra
    has_gluten_free = models.BooleanField(default=False, verbose_name="Sin TACC / Gluten Free")
    has_specialty_coffee = models.BooleanField(default=False, verbose_name="Café de especialidad")
    has_artisanal_pastries = models.BooleanField(default=False, verbose_name="Pastelería artesanal")

    # Relacionales
    favorites = models.ManyToManyField(User, related_name='favorite_cafes', blank=True)
    tags = models.ManyToManyField(Tag, related_name='cafes', blank=True)

    # Ubicación
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)

    # Visibilidad / suscripción
    VISIBILITY_CHOICES = (
        (0, 'Gratis'),
        (1, 'Destacado'),
        (2, 'Premium'),
    )
    visibility_level = models.IntegerField(choices=VISIBILITY_CHOICES, default=0)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cafes'
    )

    def save(self, *args, **kwargs):
        # Guardado inicial
        super().save(*args, **kwargs)

        def procesar_imagen(campo):
            img_field = getattr(self, campo)
            if img_field and hasattr(img_field, 'path'):
                try:
                    img = Image.open(img_field.path)
                    formato_original = img.format or 'JPEG'

                    if img.mode in ("RGBA", "P"):
                        img = img.convert("RGB")

                    max_width = 1280
                    if img.width > max_width:
                        ratio = max_width / float(img.width)
                        new_height = int(float(img.height) * ratio)
                        img = img.resize((max_width, new_height), Image.LANCZOS)

                    buffer = BytesIO()
                    img.save(
                        buffer,
                        format='JPEG' if formato_original not in ['JPEG', 'PNG'] else formato_original,
                        optimize=True,
                        quality=70
                    )

                    file_content = ContentFile(buffer.getvalue())
                    img_field.save(os.path.basename(img_field.name), file_content, save=False)
                except Exception as e:
                    print(f"⚠️ Error al procesar la imagen en {campo}: {e}")

        # Procesar imágenes
        for campo in ['photo1', 'photo2', 'photo3']:
            procesar_imagen(campo)

        # Guardar nuevamente con imágenes optimizadas
        super().save(update_fields=['photo1', 'photo2', 'photo3'])

    def average_rating(self):
        result = self.reviews.aggregate(Avg('rating'))
        return round(result['rating__avg'], 1) if result['rating__avg'] else 'Sin calificación'

    def __str__(self):
        return self.name


class Review(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    cafe = models.ForeignKey(Cafe, on_delete=models.CASCADE, related_name='reviews')
    location = models.CharField(max_length=200)
    rating = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    owner_reply = models.TextField(blank=True, null=True)
    tags = models.ManyToManyField("Tag", blank=True, related_name="reviews")


    class Meta:
        unique_together = ('user', 'cafe')

    def __str__(self):
        return f'Reseña de {self.user} en {self.cafe}'


