from django.test import TestCase
from reviews.forms import ReviewForm, CafeForm
from reviews.models import Cafe, Tag
from django.contrib.auth import get_user_model


class ReviewFormTest(TestCase):
    def test_valid_review_form(self):
        form_data = {
            'rating': 4,
            'comment': 'Muy buen café, volveré pronto.'
        }
        form = ReviewForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_review_form_missing_rating(self):
        form_data = {
            'comment': 'Faltó puntaje.'
        }
        form = ReviewForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('rating', form.errors)


class CafeFormTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='cafedueño',
            email='cafedueño@example.com',
            password='testpass123'
        )
        self.tag = Tag.objects.create(name='Especialidad')

    def test_valid_cafe_form_minimal_fields(self):
        form_data = {
            'name': 'Café Test',
            'address': 'Av. Siempreviva 742',
            'location': 'Springfield',
            'description': 'Un buen café para comenzar el día.',
            'phone': '123456789',
            'google_maps_url': 'https://maps.google.com/?q=Springfield',
            'tags': [self.tag.id],
        }
        form = CafeForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_cafe_form_missing_name(self):
        form_data = {
            'address': 'Sin nombre',
            'location': 'Desconocida',
        }
        form = CafeForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
