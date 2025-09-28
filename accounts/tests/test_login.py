from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

class LoginViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_login_view_status_code(self):
        response = self.client.get(reverse('account_login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Iniciar sesión")

    def test_login_success(self):
        login = self.client.login(username='testuser', password='testpass123')
        self.assertTrue(login)

    def test_login_invalid_credentials(self):
        login = self.client.login(username='testuser', password='wrongpass')
        self.assertFalse(login)

    def test_login_post_valid(self):
        data = {
            'login': 'testuser',
            'password': 'testpass123',
        }
        response = self.client.post(reverse('account_login'), data)
        self.assertEqual(response.status_code, 302)  # redirige tras login

    def test_login_post_invalid(self):
        data = {
            'login': 'testuser',
            'password': 'wrongpass',
        }
        response = self.client.post(reverse('account_login'), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Usuario o contraseña inválidos")
