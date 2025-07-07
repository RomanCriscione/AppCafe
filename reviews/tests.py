from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from reviews.models import Cafe, Review
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core import signing


class CafeTestCase(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='cliente', password='1234')
        self.owner = User.objects.create_user(username='duenio', password='1234', is_owner=True)
        self.other_user = User.objects.create_user(username='intruso', password='1234')

        self.cafe = Cafe.objects.create(
            name="Café de prueba",
            address="Calle Falsa 123",
            location="Zona Test",
            phone="123456",
            owner=self.owner
        )

        self.client = Client()
        self.client.login(username='cliente', password='1234')

    def test_create_cafe(self):
        self.client.logout()
        self.client.login(username='duenio', password='1234')

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
        new_cafe = Cafe.objects.get(name='Nueva Cafetería')
        self.assertEqual(new_cafe.owner, self.owner)

    def test_edit_cafe(self):
        self.client.logout()
        self.client.login(username='duenio', password='1234')

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


    def test_cafe_list_view_status_code(self):
        response = self.client.get(reverse('cafe_list'))
        self.assertEqual(response.status_code, 200)

    def test_cafe_detail_view(self):
        response = self.client.get(reverse('cafe_detail', args=[self.cafe.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.cafe.name)

    def test_create_review(self):
        data = {
            'comment': 'Muy buen café!',
            'rating': '4',
            'location': self.cafe.location,
        }
        response = self.client.post(reverse('cafe_detail', args=[self.cafe.id]), data, follow=True)

        if hasattr(response, 'context') and response.context and 'form' in response.context:
            print("Form errors:", response.context['form'].errors)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Review.objects.count(), 1)

    def test_owner_can_reply_review(self):
        review = Review.objects.create(cafe=self.cafe, user=self.user, rating=4, comment='Bien')
        self.client.logout()
        self.client.login(username='duenio', password='1234')
        response = self.client.post(reverse('reply_review', args=[review.id]), {'reply': '¡Gracias!'})
        review.refresh_from_db()
        self.assertEqual(review.owner_reply, '¡Gracias!')

    def test_owner_dashboard_access(self):
        self.client.login(username='duenio', password='1234')
        response = self.client.get(reverse('owner_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.cafe.name)

    def test_delete_cafe(self):
        self.client.logout()
        self.client.login(username='duenio', password='1234')
        url = reverse('delete_cafe', args=[self.cafe.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Cafe.objects.filter(id=self.cafe.id).exists())

    def test_owner_reviews_view(self):
        Review.objects.create(cafe=self.cafe, user=self.user, rating=4, comment='Muy buena atención')
        self.client.logout()
        self.client.login(username='duenio', password='1234')
        url = reverse('owner_reviews')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Muy buena atención')

    # NUEVOS TESTS 🔽

    def test_add_to_favorites(self):
        response = self.client.post(reverse('toggle_favorite', args=[self.cafe.id]))
        self.assertEqual(response.status_code, 302)
        self.assertIn(self.user, self.cafe.favorites.all())

    def test_remove_from_favorites(self):
        self.cafe.favorites.add(self.user)
        response = self.client.post(reverse('toggle_favorite', args=[self.cafe.id]))
        self.assertEqual(response.status_code, 302)
        self.assertNotIn(self.user, self.cafe.favorites.all())

    def test_filter_by_zona(self):
        response = self.client.get(reverse('cafe_list') + '?zona=Zona+Test')
        self.assertContains(response, self.cafe.name)

    def test_sort_by_rating(self):
        Review.objects.create(cafe=self.cafe, user=self.user, rating=5, comment='Buenísimo')
        response = self.client.get(reverse('cafe_list') + '?orden=rating')
        self.assertContains(response, self.cafe.name)

    def test_restrict_edit_access_to_non_owner(self):
        self.client.logout()
        self.client.login(username='intruso', password='1234')
        response = self.client.get(reverse('edit_cafe', args=[self.cafe.id]))
        self.assertEqual(response.status_code, 403)  # acceso prohibido

    def test_review_form_validation(self):
        data = {
            'comment': '',
            'rating': '6',  # fuera de rango
            'location': self.cafe.location
        }
        response = self.client.post(reverse('cafe_detail', args=[self.cafe.id]), data)
        self.assertEqual(Review.objects.count(), 0)
        self.assertContains(response, "form")

    def test_filter_by_wifi(self):
        self.cafe.has_wifi = True
        self.cafe.save()
        response = self.client.get(reverse('cafe_list') + '?has_wifi=on')
        self.assertContains(response, self.cafe.name)

    def test_filter_by_pet_friendly(self):
        self.cafe.is_pet_friendly = True
        self.cafe.save()
        response = self.client.get(reverse('cafe_list') + '?is_pet_friendly=on')
        self.assertContains(response, self.cafe.name)

    def test_sort_by_reviews_count(self):
        # Creamos dos cafés, uno con más reseñas que otro
        cafe2 = Cafe.objects.create(
            name="Café Segundo",
            address="Otra calle",
            location="Zona Test",
            phone="321321",
            owner=self.owner
        )
        Review.objects.create(cafe=self.cafe, user=self.user, rating=4, comment='Bien')
        Review.objects.create(cafe=self.cafe, user=self.other_user, rating=5, comment='Excelente')
        Review.objects.create(cafe=cafe2, user=self.user, rating=3, comment='Ok')

        response = self.client.get(reverse('cafe_list') + '?orden=reviews')
        self.assertContains(response, self.cafe.name)
        self.assertContains(response, cafe2.name)

        # Asegurarse que el café con más reseñas está primero
        content = response.content.decode()
        self.assertLess(content.index("Café de prueba"), content.index("Café Segundo"))

    def test_sort_by_algorithm_default(self):
        response = self.client.get(reverse('cafe_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.cafe.name)

    def test_location_filter_shows_nearby_cafes(self):
        # Simular coordenadas del usuario cerca del café
        self.cafe.latitude = -34.60
        self.cafe.longitude = -58.38
        self.cafe.save()

        response = self.client.get(reverse('cafe_list') + '?lat=-34.60&lon=-58.38&orden=algoritmo')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.cafe.name)
