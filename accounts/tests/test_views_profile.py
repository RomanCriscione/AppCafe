from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

class ProfileViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="password123",
            age=30
        )
        self.client.login(username="testuser", password="password123")

    def test_profile_view_status_code(self):
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 200)

    def test_profile_view_content(self):
        response = self.client.get(reverse("profile"))
        self.assertContains(response, "Perfil de Usuario")
        self.assertContains(response, "testuser")
        self.assertContains(response, "test@example.com")
        self.assertContains(response, "30")
