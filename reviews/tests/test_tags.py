from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from reviews.models import Cafe, Review, Tag

User = get_user_model()

class TagAssociationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='pass1234')
        self.cafe = Cafe.objects.create(name='Café de prueba', address='Av. Siempreviva 123', location='Buenos Aires', owner=self.user)
        self.tag1 = Tag.objects.create(name='Ambiente relajado', category='ambiente')
        self.tag2 = Tag.objects.create(name='Ideal para leer', category='actividad')

        self.review = Review.objects.create(user=self.user, cafe=self.cafe, rating=5, comment="Excelente ambiente")
        self.review.tags.set([self.tag1, self.tag2])

    def test_tags_are_associated_with_review(self):
        self.assertEqual(self.review.tags.count(), 2)
        self.assertIn(self.tag1, self.review.tags.all())
        self.assertIn(self.tag2, self.review.tags.all())

    def test_tags_show_up_in_cafe_detail(self):
        response = self.client.get(reverse('cafe_detail', args=[self.cafe.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.tag1.name)
        self.assertContains(response, self.tag2.name)
