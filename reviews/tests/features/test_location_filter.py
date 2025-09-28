from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from reviews.models import Cafe

class LocationFilterTestCase(TestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user(username='duenio', password='1234', is_owner=True)
        self.user = User.objects.create_user(username='cliente', password='1234')

        self.cafe_nearby = Cafe.objects.create(
            name="Café Cercano",
            address="Cerca 123",
            location="Zona Cerca",
            latitude=-34.60,
            longitude=-58.38,
            owner=self.owner
        )
        self.cafe_far = Cafe.objects.create(
            name="Café Lejano",
            address="Lejos 999",
            location="Zona Lejos",
            latitude=-34.80,
            longitude=-58.50,
            owner=self.owner
        )

        self.client = Client()
        self.client.login(username='cliente', password='1234')

    def test_location_filter_shows_nearby(self):
        url = reverse('cafe_list') + '?lat=-34.60&lon=-58.38&orden=algoritmo'
        response = self.client.get(url)
        self.assertContains(response, "Café Cercano")
        self.assertNotContains(response, "Café Lejano")
