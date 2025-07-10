from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from reviews.models import Cafe

class FavoritesTestCase(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='cliente', password='1234')
        self.owner = User.objects.create_user(username='duenio', password='1234', is_owner=True)

        self.cafe = Cafe.objects.create(
            name="Café Favorito",
            address="Dirección 123",
            location="Zona Centro",
            phone="123456789",
            owner=self.owner
        )

        self.client = Client()
        self.client.login(username='cliente', password='1234')

    def test_add_to_favorites(self):
        response = self.client.post(reverse('toggle_favorite', args=[self.cafe.id]))
        self.assertEqual(response.status_code, 302)
        self.assertIn(self.user, self.cafe.favorites.all())

    def test_remove_from_favorites(self):
        self.cafe.favorites.add(self.user)
        response = self.client.post(reverse('toggle_favorite', args=[self.cafe.id]))
        self.assertEqual(response.status_code, 302)
        self.assertNotIn(self.user, self.cafe.favorites.all())
