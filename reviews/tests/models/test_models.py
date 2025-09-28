from django.test import TestCase
from django.contrib.auth import get_user_model
from reviews.models import Cafe, Review, Tag

class ModelsTestCase(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='usuario_test',
            email='usuario@example.com',
            password='testpass123'
        )
        self.tag = Tag.objects.create(name='Pet Friendly')
        self.cafe = Cafe.objects.create(
            name='Café Central',
            address='Calle Falsa 123',
            location='Buenos Aires',
            description='Café de prueba para tests.',
            phone='123456789',
            google_maps_url='https://maps.example.com',
            owner=self.user,
        )
        self.cafe.tags.add(self.tag)

    def test_create_cafe(self):
        self.assertEqual(Cafe.objects.count(), 1)
        self.assertEqual(self.cafe.name, 'Café Central')
        self.assertIn(self.tag, self.cafe.tags.all())

    def test_create_review(self):
        review = Review.objects.create(
            cafe=self.cafe,
            user=self.user,
            rating=5,
            comment='Excelente café, me encantó.',
        )
        self.assertEqual(Review.objects.count(), 1)
        self.assertEqual(review.rating, 5)
        self.assertEqual(str(review), f'Reseña de {self.user} en {self.cafe}')
