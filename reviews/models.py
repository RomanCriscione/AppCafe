from django.conf import settings
from django.db import models
from django.db.models import Avg

class Cafe(models.Model):
    name = models.CharField(max_length=100, unique=True)
    address = models.CharField(max_length=255)
    location = models.CharField(max_length=100)  # ← ya lo tenés
    description = models.TextField(blank=True, null=True)  # ← NUEVO
    phone = models.CharField(max_length=20, blank=True, null=True)
    google_maps_url = models.URLField(blank=True, null=True)
    photo1 = models.ImageField(upload_to='cafes/', blank=True, null=True)
    photo2 = models.ImageField(upload_to='cafes/', blank=True, null=True)
    photo3 = models.ImageField(upload_to='cafes/', blank=True, null=True)

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

    class Meta:
        unique_together = ('user', 'cafe')

    def __str__(self):
        return f"{self.cafe.name} - {self.user.username}"

