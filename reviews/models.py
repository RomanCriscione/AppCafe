from django.conf import settings
from django.db import models
from django.db.models import Avg
from django.contrib.auth import get_user_model
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
import os
from reviews.utils.images import resize_and_compress

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

    class Meta:
        verbose_name_plural = "Tags"


class Cafe(models.Model):
    name = models.CharField(max_length=100, unique=True)
    address = models.CharField(max_length=255)
    location = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    google_maps_url = models.URLField(blank=True, null=True)

    # Fotos
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
    has_gluten_free = models.BooleanField(default=False, verbose_name="Sin TACC / Gluten Free")
    has_specialty_coffee = models.BooleanField(default=False, verbose_name="Café de especialidad")
    has_artisanal_pastries = models.BooleanField(default=False, verbose_name="Pastelería artesanal")
    accepts_cards = models.BooleanField(default=False, verbose_name="Acepta tarjetas")
    gluten_free_options = models.BooleanField(default=False, verbose_name="Opciones sin gluten")
    has_baby_changing = models.BooleanField(default=False, verbose_name="Cambiador para bebés")
    has_power_outlets = models.BooleanField(default=False, verbose_name="Enchufes disponibles")
    laptop_friendly = models.BooleanField(default=False, verbose_name="Apto para trabajar")
    quiet_space = models.BooleanField(default=False, verbose_name="Espacio tranquilo")
    specialty_coffee = models.BooleanField(default=False, verbose_name="Café de especialidad")
    brunch = models.BooleanField(default=False, verbose_name="Brunch")
    accepts_reservations = models.BooleanField(default=False, verbose_name="Acepta reservas")

    # Relaciones
    favorites = models.ManyToManyField(User, related_name='favorite_cafes', blank=True)
    tags = models.ManyToManyField(Tag, related_name='cafes', blank=True)

    # Ubicación
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    # Visibilidad
    VISIBILITY_CHOICES = (
        (0, 'Gratis'),
        (1, 'Destacado'),
        (2, 'Premium'),
    )
    visibility_level = models.IntegerField(choices=VISIBILITY_CHOICES, default=0)

    # Dueño
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cafes'
    )

    def save(self, *args, **kwargs):
        procesar = kwargs.pop("procesar_imagenes", True)
        super().save(*args, **kwargs)

        if procesar:
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

            for campo in ['photo1', 'photo2', 'photo3']:
                procesar_imagen(campo)

            super().save(update_fields=['photo1', 'photo2', 'photo3'])

    def average_rating(self):
        result = self.reviews.aggregate(Avg('rating'))
        return round(result['rating__avg'], 1) if result['rating__avg'] else 'Sin calificación'

    def __str__(self):
        return self.name

    class Meta:
        indexes = [
            models.Index(fields=["location"]),
            models.Index(fields=["visibility_level"]),
            models.Index(fields=["latitude", "longitude"]),
            models.Index(fields=["owner"]),
        ]


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
        indexes = [
            models.Index(fields=["cafe"]),
            models.Index(fields=["rating"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return f'Reseña de {self.user} en {self.cafe}'

class CafeStat(models.Model):
    cafe = models.ForeignKey('Cafe', on_delete=models.CASCADE, related_name='stats')
    date = models.DateField()
    views = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('cafe', 'date')
        ordering = ['-date']

    def __str__(self):
        return f'{self.cafe.name} - {self.date}: {self.views} vistas'