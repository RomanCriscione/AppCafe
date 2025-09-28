from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from reviews.models import Cafe, Review

class ReviewViewsTestCase(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='cliente', password='1234')
        self.owner = User.objects.create_user(username='duenio', password='1234', is_owner=True)

        self.cafe = Cafe.objects.create(
            name="Café de prueba",
            address="Calle Falsa 123",
            location="Zona Test",
            phone="123456",
            owner=self.owner
        )

        self.client = Client()
        self.client.login(username='cliente', password='1234')

    def test_create_review(self):
        data = {
            'comment': 'Muy buen café!',
            'rating': '4',
            'location': self.cafe.location,
        }
        response = self.client.post(reverse('cafe_detail', args=[self.cafe.id]), data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Review.objects.count(), 1)

    def test_review_form_validation(self):
        data = {
            'comment': '',
            'rating': '6',  # fuera de rango
            'location': self.cafe.location
        }
        response = self.client.post(reverse('cafe_detail', args=[self.cafe.id]), data)
        self.assertEqual(Review.objects.count(), 0)
        self.assertContains(response, "form")

    def test_owner_can_reply_review(self):
        review = Review.objects.create(cafe=self.cafe, user=self.user, rating=4, comment='Bien')
        self.client.logout()
        self.client.login(username='duenio', password='1234')
        response = self.client.post(reverse('reply_review', args=[review.id]), {'reply': '¡Gracias!'})
        review.refresh_from_db()
        self.assertEqual(review.owner_reply, '¡Gracias!')

    def test_owner_reviews_view(self):
        Review.objects.create(cafe=self.cafe, user=self.user, rating=4, comment='Muy buena atención')
        self.client.logout()
        self.client.login(username='duenio', password='1234')
        response = self.client.get(reverse('owner_reviews'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Muy buena atención')
