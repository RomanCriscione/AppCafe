from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from reviews.models import Cafe

class CafeViewsTestCase(TestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user(username='duenio', password='1234', is_owner=True)
        self.client = Client()
        self.client.login(username='duenio', password='1234')

        self.cafe = Cafe.objects.create(
            name="Café de prueba",
            address="Calle Falsa 123",
            location="Zona Test",
            phone="123456",
            owner=self.owner
        )

    def test_create_cafe(self):
        data = {
            'name': 'Nueva Cafetería',
            'address': 'Av. Siempreviva 742',
            'location': 'Zona Norte',
            'description': 'Un lindo café de barrio.',
            'phone': '+541155512345',
            'google_maps_url': 'https://maps.google.com/?q=zona+norte',
            'latitude': '-34.6037',
            'longitude': '-58.3816',
            'is_vegan_friendly': True,
            'is_pet_friendly': True,
            'has_wifi': True,
            'has_outdoor_seating': False,
            'has_parking': False,
            'is_accessible': False,
            'has_vegetarian_options': True,
            'serves_breakfast': False,
            'serves_alcohol': False,
            'has_books_or_games': False,
            'has_air_conditioning': False,
            'has_gluten_free': False,
            'has_specialty_coffee': False,
            'has_artisanal_pastries': False,
        }

        response = self.client.post(reverse('create_cafe'), data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Cafe.objects.count(), 2)

    def test_edit_cafe(self):
        url = reverse('edit_cafe', args=[self.cafe.id])
        data = {
            'name': 'Café Editado',
            'address': 'Calle Nueva 456',
            'location': 'Zona Sur',
            'description': 'Descripción actualizada.',
            'phone': '+541155599999',
            'google_maps_url': 'https://maps.google.com/?q=zona+sur',
            'latitude': '-34.6037',
            'longitude': '-58.3816',
            'is_vegan_friendly': False,
            'is_pet_friendly': False,
            'has_wifi': False,
            'has_outdoor_seating': False,
            'has_parking': False,
            'is_accessible': False,
            'has_vegetarian_options': False,
            'serves_breakfast': False,
            'serves_alcohol': False,
            'has_books_or_games': False,
            'has_air_conditioning': False,
            'has_gluten_free': False,
            'has_specialty_coffee': False,
            'has_artisanal_pastries': False,
        }

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.cafe.refresh_from_db()
        self.assertEqual(self.cafe.name, 'Café Editado')

    def test_delete_cafe(self):
        url = reverse('delete_cafe', args=[self.cafe.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Cafe.objects.filter(id=self.cafe.id).exists())

    def test_cafe_list_view_status_code(self):
        response = self.client.get(reverse('cafe_list'))
        self.assertEqual(response.status_code, 200)

    def test_cafe_detail_view(self):
        response = self.client.get(reverse('cafe_detail', args=[self.cafe.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.cafe.name)
