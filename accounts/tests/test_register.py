from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

class RegisterViewTests(TestCase):

    def test_register_view_status_code(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/register.html')

    def test_register_new_user_success(self):
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'Newpass123!',
            'password2': 'Newpass123!',
        }
        response = self.client.post(reverse('register'), data)
        self.assertEqual(response.status_code, 302)  # Redirección exitosa
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_register_user_invalid_password_mismatch(self):
        data = {
            'username': 'baduser',
            'email': 'bad@example.com',
            'password1': 'password123',
            'password2': 'differentpassword',
        }
        response = self.client.post(reverse('register'), data)
        self.assertEqual(response.status_code, 200)  # No redirige
        self.assertContains(response, "Los dos campos de contraseña no coinciden", html=False)
        self.assertFalse(User.objects.filter(username='baduser').exists())
