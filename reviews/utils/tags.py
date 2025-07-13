from collections import defaultdict
from reviews.models import Tag

def get_tags_grouped_by_cafe(cafes):
    grouped = defaultdict(lambda: defaultdict(list))

    cafe_ids = [cafe.id for cafe in cafes]
    tags = Tag.objects.filter(reviews__cafe__id__in=cafe_ids).prefetch_related('reviews__cafe')

    for tag in tags:
        for review in tag.review_set.all():
            cafe_id = review.cafe.id
            grouped[cafe_id][tag.category].append(tag)

    return grouped
