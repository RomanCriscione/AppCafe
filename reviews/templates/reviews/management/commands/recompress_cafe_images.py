from django.core.management.base import BaseCommand
from reviews.models import Cafe
from reviews.utils.images import resize_and_compress

class Command(BaseCommand):
    help = "Recomprime y redimensiona imágenes de cafés existentes."

    def handle(self, *args, **options):
        qs = Cafe.objects.all()
        for cafe in qs:
            changed = False
            for field in ['photo1', 'photo2', 'photo3']:
                f = getattr(cafe, field, None)
                if f:
                    resize_and_compress(f, max_side=1600, quality=80)
                    changed = True
            if changed:
                cafe.save(update_fields=['photo1','photo2','photo3'])
        self.stdout.write(self.style.SUCCESS("Listo: imágenes recomprimidas."))
