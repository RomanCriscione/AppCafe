from django.conf import settings
from django.db import models
from django.db.models import Avg
from django.contrib.auth import get_user_model
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
import os
from reviews.utils.images import resize_and_compress
from .claims import ClaimStatus

User = get_user_model()


class Tag(models.Model):
    CATEGORY_CHOICES = [
        ("sensorial", "🧠 Sensorial / Emocional"),
        ("estetica", "🌿 Estética y detalles"),
        ("experiencia", "✍️ Actividades y experiencia"),
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
    email = models.EmailField(
    blank=True, null=True,
    verbose_name="Email del negocio",
    help_text="Se usa para verificar al dueño por dominio (no se muestra públicamente)."
)

    # Fotos
    photo1 = models.ImageField(upload_to='cafes/', blank=True, null=True)
    photo1_title = models.CharField(max_length=200, blank=True, null=True)
    photo2 = models.ImageField(upload_to='cafes/', blank=True, null=True)
    photo2_title = models.CharField(max_length=200, blank=True, null=True)
    photo3 = models.ImageField(upload_to='cafes/', blank=True, null=True)
    photo3_title = models.CharField(max_length=200, blank=True, null=True)

    # Características del café (declaradas por el dueño)

    # Servicios / infraestructura
    has_wifi = models.BooleanField(default=False, verbose_name="Wi-Fi disponible")
    has_air_conditioning = models.BooleanField(default=False, verbose_name="Aire acondicionado")
    has_power_outlets = models.BooleanField(default=False, verbose_name="Enchufes disponibles")
    has_outdoor_seating = models.BooleanField(default=False, verbose_name="Mesas al aire libre")
    has_parking = models.BooleanField(default=False, verbose_name="Estacionamiento disponible")
    is_accessible = models.BooleanField(
        default=False,
        verbose_name="Accesible para personas con movilidad reducida"
    )
    accepts_cards = models.BooleanField(default=False, verbose_name="Acepta tarjetas")
    accepts_reservations = models.BooleanField(default=False, verbose_name="Acepta reservas")
    has_baby_changing = models.BooleanField(default=False, verbose_name="Cambiador para bebés")

    # Mascotas
    is_pet_friendly = models.BooleanField(default=False, verbose_name="Apto mascotas")

    # Oferta gastronómica
    has_specialty_coffee = models.BooleanField(default=False, verbose_name="Café de especialidad")
    serves_brunch = models.BooleanField(default=False, verbose_name="Brunch")
    serves_breakfast = models.BooleanField(default=False, verbose_name="Sirve desayuno")
    serves_alcohol = models.BooleanField(default=False, verbose_name="Sirve alcohol")
    has_artisanal_pastries = models.BooleanField(default=False, verbose_name="Pastelería artesanal")
    offers_ice_cream = models.BooleanField(default=False, verbose_name="Ofrece helados")

    # Opciones alimentarias
    is_vegan_friendly = models.BooleanField(default=False, verbose_name="Opciones veganas")
    has_vegetarian_options = models.BooleanField(default=False, verbose_name="Opciones vegetarianas")
    has_gluten_free_options = models.BooleanField(default=False, verbose_name="Opciones sin gluten / Sin TACC")

    # Uso del espacio
    laptop_friendly = models.BooleanField(default=False, verbose_name="Apto para trabajar")
    quiet_space = models.BooleanField(default=False, verbose_name="Espacio tranquilo")

    # Extras
    has_books_or_games = models.BooleanField(default=False, verbose_name="Libros o juegos disponibles")


    # Relaciones
    favorites = models.ManyToManyField(User, related_name='favorite_cafes', blank=True)
    tags = models.ManyToManyField('Tag', related_name='cafes', blank=True)

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

    # Dueño (ya lo tenías)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cafes'
    )

    # ✅ NUEVO: estado de reclamo y quién lo reclamó (fallback)
    claim_status = models.CharField(
        max_length=12,
        choices=ClaimStatus.choices,
        default=ClaimStatus.UNCLAIMED,
    )
    claimed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="cafes_claimed",
    )

    class Meta:
        indexes = [
            models.Index(fields=["location"]),
            models.Index(fields=["visibility_level"]),
            models.Index(fields=["latitude", "longitude"]),
            models.Index(fields=["owner"]),
        ]

    def save(self, *args, **kwargs):
        if self.photo1 and self.photo1.size > 2_000_000:
            raise ValueError("Imagen muy grande")
        super().save(*args, **kwargs)

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


class Review(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    cafe = models.ForeignKey(Cafe, on_delete=models.CASCADE, related_name='reviews')
    location = models.CharField(max_length=200)
    rating = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    owner_reply = models.TextField(blank=True, null=True)
    tags = models.ManyToManyField("Tag", blank=True, related_name="reviews")
    precio_capuccino = models.PositiveIntegerField(
    null=True,
    blank=True,
    help_text="Precio pagado por un capuccino mediano"
)

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
    
    # --- Likes de reseñas ---
class ReviewLike(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="review_likes",
    )
    review = models.ForeignKey(
        "Review",
        on_delete=models.CASCADE,
        related_name="likes",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (("user", "review"),)
        indexes = [
            models.Index(fields=["review"]),
            models.Index(fields=["user"]),
            models.Index(fields=["created_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"❤️ {self.user} → Review {self.review_id}"


# --- Reportes/denuncias de reseñas ---
class ReviewReport(models.Model):
    class Reason(models.TextChoices):
        SPAM = "SPAM", "Spam o autopromo"
        OFFENSIVE = "OFFENSIVE", "Ofensivo / lenguaje inapropiado"
        FALSE = "FALSE_INFO", "Información falsa"
        OTHER = "OTHER", "Otro"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pendiente"
        ACCEPTED = "ACCEPTED", "Aceptado (acción tomada)"
        REJECTED = "REJECTED", "Rechazado"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="review_reports",
    )
    review = models.ForeignKey(
        "Review",
        on_delete=models.CASCADE,
        related_name="reports",
    )
    reason = models.CharField(max_length=20, choices=Reason.choices, default=Reason.OTHER)
    message = models.TextField(blank=True, null=True)

    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="review_reports_resolved",
    )

    class Meta:
        unique_together = (("user", "review"),)  # un reporte por usuario por reseña
        indexes = [
            models.Index(fields=["review"]),
            models.Index(fields=["user"]),
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"🚩 {self.review_id} por {self.user} ({self.reason})"
