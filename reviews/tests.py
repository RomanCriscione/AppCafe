from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from reviews.models import Cafe, Review

class CafeTestCase(TestCase):
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

    def test_create_cafe(self):
        self.client.logout()
        self.client.login(username='duenio', password='1234')

        data = {
            'name': 'Nueva Cafetería',
            'address': 'Av. Siempreviva 742',
            'location': 'Zona Norte',
            'phone': '555-1234',
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
            'phone': '999-8888',
        }

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

        self.cafe.refresh_from_db()
        self.assertEqual(self.cafe.name, 'Café Editado')
        self.assertEqual(self.cafe.address, 'Calle Nueva 456')
        self.assertEqual(self.cafe.location, 'Zona Sur')
        self.assertEqual(self.cafe.phone, '999-8888')


    def test_cafe_list_view_status_code(self):
        response = self.client.get(reverse('cafe_list'))
        self.assertEqual(response.status_code, 200)

    def test_cafe_detail_view(self):
        response = self.client.get(reverse('cafe_detail', args=[self.cafe.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.cafe.name)

    def test_create_review(self):
        self.client.login(username='cliente', password='1234')

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
        review = Review.objects.first()
        self.assertEqual(review.comment, 'Muy buen café!')
        self.assertEqual(review.user, self.user)

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
        self.assertContains(response, self.cafe.name)
