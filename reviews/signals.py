# reviews/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key

from .models import Review


def _invalidate_cafe_reviews_cache(cafe_id: int) -> None:
    """Invalidar el fragmento cacheado de la lista de reseñas del café."""
    key = make_template_fragment_key("cafe_reviews_list", [cafe_id])
    cache.delete(key)


@receiver(post_save, sender=Review)
def review_saved(sender, instance: Review, **kwargs):
    _invalidate_cafe_reviews_cache(instance.cafe_id)


@receiver(post_delete, sender=Review)
def review_deleted(sender, instance: Review, **kwargs):
    _invalidate_cafe_reviews_cache(instance.cafe_id)
