from reviews.models import Cafe
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os

def corregir_rutas_duplicadas():
    fotos = ['photo1', 'photo2', 'photo3']

    for cafe in Cafe.objects.all():
        actualizado = False

        for campo in fotos:
            imagen = getattr(cafe, campo)
            if imagen and imagen.name.count("cafes/") > 1:
                old_path = imagen.name
                filename = os.path.basename(old_path)
                corrected_path = f"cafes/{filename}"

                if default_storage.exists(old_path):
                    file_data = default_storage.open(old_path).read()
                    default_storage.save(corrected_path, ContentFile(file_data))
                    default_storage.delete(old_path)
                    setattr(cafe, campo, corrected_path)
                    actualizado = True
                    print(f"✅ Corregido: {campo} - {old_path} ➜ {corrected_path}")
                else:
                    print(f"⚠️ Archivo no encontrado: {old_path}")

        if actualizado:
            cafe.save()

def limpiar_rutas_invalidas():
    fotos = ['photo1', 'photo2', 'photo3']
    for cafe in Cafe.objects.all():
        actualizado = False
        for campo in fotos:
            imagen = getattr(cafe, campo)
            if imagen and "cafes/cafes/" in imagen.name:
                print(f"🧹 Limpiando {campo} de: {cafe.name}")
                imagen.delete(save=False)
                setattr(cafe, campo, None)
                actualizado = True
        if actualizado:
            cafe.save()

