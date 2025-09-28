from io import BytesIO
from django.core.files.base import ContentFile
from PIL import Image

def resize_and_compress(image_field, max_side=1600, quality=80):
    if not image_field or not hasattr(image_field, 'file'):
        return
    img = Image.open(image_field)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    # Redimensiona manteniendo proporción
    img.thumbnail((max_side, max_side), Image.LANCZOS)

    buf = BytesIO()
    img.save(buf, format="JPEG", quality=quality, optimize=True, progressive=True)
    buf.seek(0)

    # Reescribe el archivo original con .jpg
    base_name = image_field.name.rsplit('.', 1)[0]
    new_name = f"{base_name}.jpg"
    image_field.save(new_name, ContentFile(buf.read()), save=False)
