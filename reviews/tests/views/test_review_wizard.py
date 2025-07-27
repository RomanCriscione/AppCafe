from django.test import TestCase
from django.urls import reverse
from reviews.models import Cafe, Tag
from django.contrib.auth import get_user_model

User = get_user_model()

class ReviewWizardTests(TestCase):
    def setUp(self):
        # Creamos un usuario dueño y un usuario normal
        self.owner = User.objects.create_user(
            username="owneruser",
            password="ownerpass123",
            email="owner@example.com"
        )
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
            email="test@example.com"
        )
        self.client.login(username="testuser", password="testpass123")

        # Ahora sí, podemos crear el café con owner
        self.cafe = Cafe.objects.create(
            name="Café de prueba",
            address="Calle falsa 123",
            location="Buenos Aires",
            owner=self.owner
        )

        # Creamos algunos tags de prueba
        Tag.objects.create(name="Tranquilo", category="ambiente")
        Tag.objects.create(name="Inspira alegría", category="emocional")
        Tag.objects.create(name="Ideal para trabajar", category="actividad")

    def test_review_wizard_render(self):
        url = reverse("create_review", args=[self.cafe.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dejá tu reseña")
        self.assertContains(response, "Comentario")
        self.assertContains(response, "Puntuación")

        # Verificamos que aparezcan las categorías capitalizadas
        self.assertContains(response, "ambiente")
        self.assertContains(response, "emocional")
        self.assertContains(response, "actividad")

        # Verificamos que aparezcan algunos tags
        self.assertContains(response, "Tranquilo")
        self.assertContains(response, "Inspira alegría")
        self.assertContains(response, "Ideal para trabajar")

        # Botones del wizard
        self.assertContains(response, "Siguiente")
        self.assertContains(response, "Anterior")
        self.assertContains(response, "Enviar")
