from django.contrib.auth.models import AbstractUser
from django.db import models
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
import os


class CustomUser(AbstractUser):
    age = models.PositiveIntegerField(null=True, blank=True)
    is_owner = models.BooleanField(default=False)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.avatar and hasattr(self.avatar, 'path'):
            try:
                img = Image.open(self.avatar.path)
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")

                max_size = 512
                if img.width > max_size:
                    ratio = max_size / float(img.width)
                    new_height = int(float(img.height) * ratio)
                    img = img.resize((max_size, new_height), Image.LANCZOS)

                buffer = BytesIO()
                img.save(buffer, format='JPEG', optimize=True, quality=70)
                file_content = ContentFile(buffer.getvalue())
                self.avatar.save(os.path.basename(self.avatar.name), file_content, save=False)

            except Exception as e:
                print(f"⚠️ Error al procesar avatar: {e}")

        super().save(update_fields=['avatar'])

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
