from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from reviews.models import Cafe, Review, Tag

User = get_user_model()

class GroupedTagsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='pass1234')
        self.cafe = Cafe.objects.create(
            name='Café sensorial',
            address='Calle Falsa 123',
            location='Buenos Aires',
            owner=self.user
        )

        # Crear etiquetas con categorías distintas
        self.tag_ambiente = Tag.objects.create(name='Tranquilo', category='ambiente')
        self.tag_emocion = Tag.objects.create(name='Inspira alegría', category='emocional')
        self.tag_actividad = Tag.objects.create(name='Ideal para trabajar', category='actividad')

        # Crear reseña con etiquetas
        self.review = Review.objects.create(
            user=self.user,
            cafe=self.cafe,
            rating=4,
            comment="Me encantó el lugar"
        )
        self.review.tags.set([self.tag_ambiente, self.tag_emocion, self.tag_actividad])

    def test_tags_grouped_by_category_in_detail(self):
        url = reverse('cafe_detail', args=[self.cafe.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Asegurar que los nombres de las etiquetas aparezcan
        self.assertContains(response, 'Tranquilo')
        self.assertContains(response, 'Inspira alegría')
        self.assertContains(response, 'Ideal para trabajar')

        # Verificamos que al menos una categoría se muestre como título
        self.assertContains(response, 'Ambiente')
        self.assertContains(response, 'Emocional')
        self.assertContains(response, 'Actividad')
