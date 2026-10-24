# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile

import os


class CustomUser(AbstractUser):
    age = models.PositiveIntegerField(null=True, blank=True)
    is_owner = models.BooleanField(default=False)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    apple_sub = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
    )
    apple_refresh_token = models.TextField(
        null=True,
        blank=True,
    )

    @property
    def public_name(self):
        full_name = self.get_full_name().strip()

        if full_name:
            return full_name

        username = (self.username or "").strip()

        if username:
            return username.split("@")[0]

        email = (self.email or "").strip()

        if email:
            return email.split("@")[0]

        return "Usuario de Gota"

    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        """
        - Guarda el usuario normalmente.
        - Si hay avatar y es un archivo accesible (path), lo reescala/comprime.
        - Evita loops: solo reescribe si realmente puede procesarlo.
        """
        super().save(*args, **kwargs)

        if not self.avatar:
            return

        # Procesar avatares solo cuando se carga una imagen nueva.
        # Evita acceder a rutas físicas en almacenamiento remoto.
        if not getattr(self.avatar, "_committed", True):
            return

        try:
            avatar_path = self.avatar.path
        except (NotImplementedError, ValueError):
            return

        try:
            img = Image.open(avatar_path)

            # Normalizar modo
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            max_size = 512
            if img.width > max_size:
                ratio = max_size / float(img.width)
                new_height = int(float(img.height) * ratio)
                img = img.resize((max_size, new_height), Image.LANCZOS)

            buffer = BytesIO()
            img.save(buffer, format="JPEG", optimize=True, quality=70)
            buffer.seek(0)

            filename = os.path.basename(self.avatar.name)
            self.avatar.save(filename, ContentFile(buffer.read()), save=False)

            # Guardar SOLO el campo avatar (sin re-ejecutar el procesamiento completo)
            super().save(update_fields=["avatar"])

        except Exception as e:
            # Evitá print en producción si querés; por ahora lo dejamos simple.
            print(f"⚠️ Error al procesar avatar: {e}")

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
