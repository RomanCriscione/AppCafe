from django.test import TestCase
from reviews.utils.geo import haversine_distance

class UtilsTestCase(TestCase):
    def test_haversine_distance_zero(self):
        # Misma ubicación → distancia 0 km
        lat1, lon1 = -34.6037, -58.3816  # Buenos Aires
        lat2, lon2 = -34.6037, -58.3816
        distance = haversine_distance(lat1, lon1, lat2, lon2)
        self.assertAlmostEqual(distance, 0.0, places=2)

    def test_haversine_distance_nonzero(self):
        # Buenos Aires a Córdoba (~647 km)
        lat1, lon1 = -34.6037, -58.3816
        lat2, lon2 = -31.4201, -64.1888
        distance = haversine_distance(lat1, lon1, lat2, lon2)
        self.assertTrue(640 <= distance <= 660)
