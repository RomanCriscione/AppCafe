from django.test import TestCase
from django.contrib.auth import get_user_model
from reviews.models import Cafe, Review
from django.urls import reverse

User = get_user_model()

class FiltersAndSortingTestCase(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="dueño1", email="dueno@example.com", password="testpass123"
        )
        self.user2 = User.objects.create_user(
            username="usuario2", email="usuario2@example.com", password="testpass123"
        )

        self.cafe1 = Cafe.objects.create(
            name="Café A",
            address="Calle 123",
            location="Palermo",
            has_wifi=True,
            is_pet_friendly=True,
            owner=self.owner
        )

        self.cafe2 = Cafe.objects.create(
            name="Café B",
            address="Av. Siempreviva 742",
            location="Belgrano",
            has_wifi=False,
            is_pet_friendly=False,
            owner=self.owner
        )

        Review.objects.create(cafe=self.cafe1, rating=4, user=self.owner)
        Review.objects.create(cafe=self.cafe1, rating=5, user=self.user2)
        Review.objects.create(cafe=self.cafe2, rating=3, user=self.user2)

    def test_filter_by_pet_friendly(self):
        response = self.client.get(reverse("cafe_list") + "?pet=on")
        self.assertContains(response, "Café A")
        self.assertNotContains(response, "Café B")

    def test_filter_by_wifi(self):
        response = self.client.get(reverse("cafe_list") + "?wifi=on")
        self.assertContains(response, "Café A")
        self.assertNotContains(response, "Café B")

    def test_filter_by_zona(self):
        response = self.client.get(reverse("cafe_list") + "?zona=Palermo")
        self.assertContains(response, "Café A")
        self.assertNotContains(response, "Café B")

    def test_sort_by_rating(self):
        response = self.client.get(reverse("cafe_list") + "?orden=rating")
        cafes = list(response.context["cafes"])
        self.assertGreaterEqual(cafes[0].average_rating, cafes[1].average_rating)

    def test_sort_by_reviews_count(self):
        response = self.client.get(reverse("cafe_list") + "?orden=reviews_count")
        cafes = list(response.context["cafes"])
        self.assertGreaterEqual(cafes[0].reviews.count(), cafes[1].reviews.count())

    def test_sort_by_algorithm_default(self):
        response = self.client.get(reverse("cafe_list"))
        cafes = list(response.context["cafes"])
        self.assertTrue(len(cafes) >= 2)
