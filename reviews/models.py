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
import secrets

User = get_user_model()


class Tag(models.Model):
    CATEGORY_CHOICES = [
        ("sensorial", "☕ Sensorial"),
        ("experiencia", "✍️ Experiencia"),
        ("ambiente", "🪑 Ambiente"),
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
    PROVINCE_CHOICES = [
        ("", "Seleccioná una provincia"),
        ("CABA", "Ciudad Autónoma de Buenos Aires"),
        ("Buenos Aires", "Buenos Aires"),
        ("Catamarca", "Catamarca"),
        ("Chaco", "Chaco"),
        ("Chubut", "Chubut"),
        ("Córdoba", "Córdoba"),
        ("Corrientes", "Corrientes"),
        ("Entre Ríos", "Entre Ríos"),
        ("Formosa", "Formosa"),
        ("Jujuy", "Jujuy"),
        ("La Pampa", "La Pampa"),
        ("La Rioja", "La Rioja"),
        ("Mendoza", "Mendoza"),
        ("Misiones", "Misiones"),
        ("Neuquén", "Neuquén"),
        ("Río Negro", "Río Negro"),
        ("Salta", "Salta"),
        ("San Juan", "San Juan"),
        ("San Luis", "San Luis"),
        ("Santa Cruz", "Santa Cruz"),
        ("Santa Fe", "Santa Fe"),
        ("Santiago del Estero", "Santiago del Estero"),
        ("Tierra del Fuego", "Tierra del Fuego"),
        ("Tucumán", "Tucumán"),
    ]

    province = models.CharField(
        max_length=100,
        choices=PROVINCE_CHOICES,
        blank=True,
        default="",
        verbose_name="Provincia"
    )
    description = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    google_maps_url = models.URLField(blank=True, null=True)
    email = models.EmailField(
        blank=True, null=True,
        verbose_name="Email del negocio",
        help_text="Se usa para verificar al dueño por dominio (no se muestra públicamente)."
    )
    instagram = models.CharField(
        max_length=50,
        blank=True,
        help_text="Usuario de Instagram sin @ (ej: cafepepito)"
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

    # Mascotas / familias
    is_pet_friendly = models.BooleanField(
        default=False,
        verbose_name="Pet friendly",
    )
    is_kids_friendly = models.BooleanField(
        default=False,
        verbose_name="Kids friendly",
    )

    # Oferta gastronómica
    has_specialty_coffee = models.BooleanField(default=False, verbose_name="Café de especialidad")
    serves_brunch = models.BooleanField(default=False, verbose_name="Brunch")
    serves_breakfast = models.BooleanField(default=False, verbose_name="Sirve desayuno")
    serves_alcohol = models.BooleanField(default=False, verbose_name="Sirve alcohol")
    has_artisanal_pastries = models.BooleanField(default=False, verbose_name="Pastelería artesanal")
    offers_ice_cream = models.BooleanField(default=False, verbose_name="Ofrece helados")

    # Opciones alimentarias
    is_vegan_friendly = models.BooleanField(
        default=False,
        verbose_name="Opciones veganas",
    )
    has_vegetarian_options = models.BooleanField(
        default=False,
        verbose_name="Opciones vegetarianas",
    )
    has_gluten_free_options = models.BooleanField(
        default=False,
        verbose_name="Opciones sin gluten / Sin TACC",
    )
    has_healthy_options = models.BooleanField(
        default=False,
        verbose_name="Opciones saludables",
    )
    has_sugar_free_options = models.BooleanField(
        default=False,
        verbose_name="Opciones sin azúcar",
    )
    has_plant_based_milk = models.BooleanField(
        default=False,
        verbose_name="Leches vegetales",
    )

    # Espacio y entorno
    has_garden = models.BooleanField(
        default=False,
        verbose_name="Con jardín",
    )
    has_water_view = models.BooleanField(
        default=False,
        verbose_name="Vista al agua",
    )
    has_mountain_view = models.BooleanField(
        default=False,
        verbose_name="Vista a las sierras / montañas",
    )
    surrounded_by_nature = models.BooleanField(
        default=False,
        verbose_name="Rodeado de naturaleza",
    )
    has_rooftop = models.BooleanField(
        default=False,
        verbose_name="Terraza o rooftop",
    )
    has_large_windows = models.BooleanField(
        default=False,
        verbose_name="Grandes ventanales",
    )
    is_old_house = models.BooleanField(
        default=False,
        verbose_name="En una casa antigua",
    )
    is_historic_building = models.BooleanField(
        default=False,
        verbose_name="En un edificio histórico",
    )
    inside_bookstore = models.BooleanField(
        default=False,
        verbose_name="Dentro de una librería",
    )
    inside_cultural_space = models.BooleanField(
        default=False,
        verbose_name="En un espacio cultural",
    )

    # Uso del espacio
    laptop_friendly = models.BooleanField(default=False, verbose_name="Apto para trabajar")
    quiet_space = models.BooleanField(default=False, verbose_name="Espacio tranquilo")

    # Extras
    has_books_or_games = models.BooleanField(default=False, verbose_name="Libros o juegos disponibles")


    # Relaciones
    
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

    # ⭐ Curaduría Gota (editorial)
    is_curated = models.BooleanField(
        default=False,
        help_text="Café destacado manualmente por Gota"
    )


    # Dueño
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
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
        super().save(*args, **kwargs)

    def average_rating(self):
        result = self.reviews.aggregate(Avg('rating'))
        return round(result['rating__avg'], 1) if result['rating__avg'] else 'Sin calificación'

    def __str__(self):
        return self.name


class Review(models.Model):
    PLAN_CHOICES = [
        ("trabajar", "💻 Trabajar o estudiar"),
        ("al_paso", "🚶 Tomar algo rápido"),
        ("amigos", "💬 Charlar con amigos"),
        ("cita", "❤️ Cita"),
        ("leer", "📖 Leer o desconectar"),
        ("solo", "☕ Salir solo"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    cafe = models.ForeignKey(Cafe, on_delete=models.CASCADE, related_name='reviews')
    location = models.CharField(max_length=200)
    rating = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    owner_reply = models.TextField(blank=True, null=True)
    tags = models.ManyToManyField("Tag", blank=True, related_name="reviews")

    best_for_plan = models.CharField(
        max_length=20,
        choices=PLAN_CHOICES,
        blank=True,
        null=True,
        verbose_name="¿Para qué plan es mejor este café?",
    )

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
    
class CafeRelationship(models.Model):

    WANT_TO_GO = "want_to_go"
    WANT_TO_RETURN = "want_to_return"
    VISITED = "visited"

    STATUS_CHOICES = [
        (WANT_TO_GO, "☕ Quiero ir"),
        (WANT_TO_RETURN, "❤️ Quiero volver"),
        (VISITED, "✔️ Ya fui"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cafe_relationships",
    )

    cafe = models.ForeignKey(
        "Cafe",
        on_delete=models.CASCADE,
        related_name="relationships",
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
    )

    # ✨ nota personal privada
    private_note = models.TextField(
        blank=True,
    )

    # ✨ timestamps emocionales
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    last_status_change_at = models.DateTimeField(
        auto_now=True
    )

    # ✨ futuras features
    visit_count = models.PositiveIntegerField(
        default=0
    )

    would_return = models.BooleanField(
        null=True,
        blank=True,
    )

    would_return_answered_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    second_impression = models.CharField(
        max_length=30,
        null=True,
        blank=True,
    )

    collection = models.CharField(
        max_length=30,
        null=True,
        blank=True,
    )

    class Meta:
        unique_together = ("user", "cafe")

        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["updated_at"]),
        ]

    def __str__(self):
        return f"{self.user} → {self.cafe} ({self.status})"

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

class CafeWhisper(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cafe_whispers",
    )

    cafe = models.ForeignKey(
        "Cafe",
        on_delete=models.CASCADE,
        related_name="whispers",
    )

    text = models.CharField(
        max_length=40,
    )

    reports_count = models.PositiveIntegerField(
        default=0
    )

    is_hidden = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-created_at"]

        indexes = [
            models.Index(fields=["cafe"]),
            models.Index(fields=["user"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.user} → {self.cafe}: {self.text}"

class RewardActionRule(models.Model):

    class Action(models.TextChoices):
        WANT_TO_GO = "want_to_go", "Quiero ir"
        RELATIONSHIP_PROGRESS = "relationship_progress", "Ya fui / Quiero volver"
        CHECK_IN = "check_in", "Estoy acá"
        REVIEW = "review", "Dejar reseña"
        PHOTO = "photo", "Agregar foto"
        WHISPER = "whisper", "Dejar huella"
        REVIEW_TAG_BONUS = "review_tag_bonus", "Bonus reseña con etiquetas"

    action = models.CharField(
        max_length=30,
        choices=Action.choices,
        unique=True,
        verbose_name="Acción",
    )

    points = models.PositiveIntegerField(
        default=0,
        verbose_name="Gotas",
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Activa",
    )

    max_rewards_per_window = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Máximo de recompensas por ventana",
        help_text=(
            "Dejar vacío si esta acción no tiene límite por ventana."
        ),
    )

    window_hours = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Duración de la ventana (horas)",
        help_text=(
            "Ejemplo: 24 para limitar recompensas dentro de una ventana de 24 horas."
        ),
    )

    repeat_after_days = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Puede volver a sumar después de (días)",
        help_text=(
            "Dejar vacío si la recompensa sólo puede obtenerse una vez por cafetería."
        ),
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        verbose_name = "Regla de Gotas"
        verbose_name_plural = "Reglas de Gotas"
        ordering = ["action"]

    def __str__(self):
        return f"{self.get_action_display()} (+{self.points} Gotas)"

class UserPointTransaction(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="gota_transactions",
        verbose_name="Usuario",
    )

    cafe = models.ForeignKey(
        "Cafe",
        on_delete=models.CASCADE,
        related_name="gota_transactions",
        null=True,
        blank=True,
        verbose_name="Cafetería",
    )

    action = models.CharField(
        max_length=30,
        choices=RewardActionRule.Action.choices,
        verbose_name="Acción",
    )

    points = models.IntegerField(
        verbose_name="Gotas",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        verbose_name = "Movimiento de Gotas"
        verbose_name_plural = "Movimientos de Gotas"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "action", "created_at"]),
            models.Index(fields=["user", "cafe", "action"]),
        ]

    def __str__(self):
        return (
            f"{self.user} · {self.get_action_display()} "
            f"· {self.points:+d} Gotas"
        )

class CafeCheckIn(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cafe_checkins",
        verbose_name="Usuario",
    )

    cafe = models.ForeignKey(
        "Cafe",
        on_delete=models.CASCADE,
        related_name="checkins",
        verbose_name="Cafetería",
    )

    latitude = models.FloatField(
        verbose_name="Latitud detectada",
    )

    longitude = models.FloatField(
        verbose_name="Longitud detectada",
    )

    distance_meters = models.FloatField(
        verbose_name="Distancia a la cafetería (m)",
    )

    is_valid = models.BooleanField(
        default=False,
        verbose_name="Visita validada",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        verbose_name = "Visita validada"
        verbose_name_plural = "Visitas validadas"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "cafe", "created_at"]),
            models.Index(fields=["user", "is_valid"]),
        ]

    def __str__(self):
        estado = "válida" if self.is_valid else "no válida"
        return (
            f"{self.user} · {self.cafe} "
            f"· {estado} · {self.distance_meters:.0f} m"
        )

class RewardSettings(models.Model):

    rewards_enabled = models.BooleanField(
        default=False,
        verbose_name="Programa de Gotas activo",
        help_text=(
            "Interruptor maestro. Mientras esté desactivado, "
            "ninguna acción otorga Gotas ni beneficios."
        ),
    )

    program_starts_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Inicio oficial del programa",
        help_text=(
            "Las acciones anteriores a esta fecha no forman parte "
            "de la economía oficial de Gotas."
        ),
    )

    welcome_reward_enabled = models.BooleanField(
        default=False,
        verbose_name="Beneficio de bienvenida activo",
        help_text=(
            "Permite entregar el beneficio inicial en la primera "
            "acción elegible realizada desde el inicio del programa."
        ),
    )


    check_in_radius_meters = models.PositiveIntegerField(
        default=150,
        verbose_name="Radio máximo para Estoy acá (metros)",
        help_text=(
            "Distancia máxima entre el usuario y la cafetería "
            "para validar una visita."
        ),
    )

    check_in_valid_hours = models.PositiveIntegerField(
        default=24,
        verbose_name="Vigencia del Estoy acá (horas)",
        help_text=(
            "Durante cuántas horas una visita validada puede "
            "habilitar recompensas como una reseña."
        ),
    )

    welcome_reward_radius_km = models.FloatField(
        default=3.0,
        verbose_name="Radio para beneficio inicial (km)",
        help_text=(
            "Si la cafetería elegida no tiene beneficio, "
            "buscar uno cercano dentro de este radio."
        ),
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        verbose_name = "Configuración de recompensas"
        verbose_name_plural = "Configuración de recompensas"

    def __str__(self):
        return "Configuración de recompensas"

class CafeReward(models.Model):

    class RewardType(models.TextChoices):
        PERCENTAGE = "percentage", "Descuento porcentual"
        FIXED_AMOUNT = "fixed_amount", "Descuento fijo"
        FREE_PRODUCT = "free_product", "Producto gratis"
        TWO_FOR_ONE = "two_for_one", "2x1"
        SPECIAL_PRICE = "special_price", "Precio especial"
        CUSTOM = "custom", "Beneficio personalizado"

    class UnlockType(models.TextChoices):
        POINTS = "points", "Por Gotas"
        AUTOMATIC = "automatic", "Automático"

    cafe = models.ForeignKey(
        "Cafe",
        on_delete=models.CASCADE,
        related_name="rewards",
        verbose_name="Cafetería",
    )

    name = models.CharField(
        max_length=120,
        verbose_name="Nombre interno",
    )

    reward_type = models.CharField(
        max_length=30,
        choices=RewardType.choices,
        verbose_name="Tipo de beneficio",
    )

    unlock_type = models.CharField(
        max_length=20,
        choices=UnlockType.choices,
        default=UnlockType.POINTS,
        verbose_name="Forma de desbloqueo",
    )

    points_required = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Gotas necesarias",
        help_text=(
            "Dejar vacío si el beneficio se desbloquea automáticamente."
        ),
    )

    percentage_value = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Porcentaje de descuento",
    )

    fixed_amount_value = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Monto de descuento",
    )

    user_text = models.CharField(
        max_length=200,
        verbose_name="Texto para mostrar al usuario",
        help_text=(
            "Ejemplo: 20% de descuento en tu consumo."
        ),
    )

    terms = models.TextField(
        blank=True,
        verbose_name="Condiciones",
    )

    is_welcome_reward = models.BooleanField(
        default=False,
        verbose_name="Puede usarse como primer beneficio",
    )

    priority = models.PositiveIntegerField(
        default=100,
        verbose_name="Prioridad",
        help_text=(
            "Menor número = mayor prioridad cuando haya varios beneficios posibles."
        ),
    )

    stock = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Cantidad disponible",
        help_text="Dejar vacío para stock ilimitado.",
    )

    valid_from = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Válido desde",
    )

    valid_until = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Válido hasta",
    )

    coupon_valid_days = models.PositiveIntegerField(
        default=7,
        verbose_name="Vencimiento del cupón (días)",
        help_text=(
            "Cantidad de días que tendrá el usuario para usarlo "
            "desde que lo recibe."
        ),
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Activo",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        verbose_name = "Beneficio de cafetería"
        verbose_name_plural = "Beneficios de cafeterías"
        ordering = ["priority", "cafe__name", "name"]
        indexes = [
            models.Index(fields=["cafe", "is_active"]),
            models.Index(fields=["is_welcome_reward", "is_active"]),
        ]

    def __str__(self):
        return f"{self.cafe} · {self.name}"

class UserCoupon(models.Model):

    class Status(models.TextChoices):
        AVAILABLE = "available", "Disponible"
        USED = "used", "Usado"
        EXPIRED = "expired", "Vencido"
        CANCELLED = "cancelled", "Cancelado"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="coupons",
        verbose_name="Usuario",
    )

    cafe = models.ForeignKey(
        "Cafe",
        on_delete=models.CASCADE,
        related_name="user_coupons",
        verbose_name="Cafetería",
    )

    reward = models.ForeignKey(
        "CafeReward",
        on_delete=models.PROTECT,
        related_name="user_coupons",
        verbose_name="Beneficio original",
    )

    code = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        verbose_name="Código",
    )

    qr_token = models.CharField(
        max_length=64,
        unique=True,
        editable=False,
        verbose_name="Token QR",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.AVAILABLE,
        verbose_name="Estado",
    )

    reward_text_snapshot = models.CharField(
        max_length=200,
        verbose_name="Beneficio otorgado",
    )

    terms_snapshot = models.TextField(
        blank=True,
        verbose_name="Condiciones al momento de otorgarlo",
    )

    obtained_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Obtenido",
    )

    expires_at = models.DateTimeField(
        verbose_name="Vence",
    )

    used_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Usado",
    )

    used_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="validated_coupons",
        verbose_name="Validado por",
    )

    class Meta:
        verbose_name = "Cupón de usuario"
        verbose_name_plural = "Cupones de usuarios"
        ordering = ["-obtained_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["cafe", "status"]),
            models.Index(fields=["qr_token"]),
            models.Index(fields=["expires_at"]),
        ]

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self._generate_unique_code()

        if not self.qr_token:
            self.qr_token = secrets.token_urlsafe(32)

        super().save(*args, **kwargs)

    @classmethod
    def _generate_unique_code(cls):
        while True:
            code = f"GOTA-{secrets.token_hex(3).upper()}"

            if not cls.objects.filter(code=code).exists():
                return code

    def __str__(self):
        return (
            f"{self.code} · {self.user} · "
            f"{self.cafe} · {self.get_status_display()}"
        )