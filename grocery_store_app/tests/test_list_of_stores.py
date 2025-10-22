from unittest.mock import patch
from django.test import TestCase, Client
from grocery_store_app.models import Store, StoreOpeningHours

class ListOfStoresTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create two stores with known locations
        self.store_a = Store.objects.create(
            name="Store A",
            address="100 Main St",
            postcode="2000",
            phone_number="123456789",
            latitude=-33.8675,
            longitude=151.2070
        )
        self.store_b = Store.objects.create(
            name="Store B",
            address="200 Side St",
            postcode="3000",
            phone_number="987654321",
            latitude=-37.814,
            longitude=144.96332
        )

        # Add opening hours (new related model)
        StoreOpeningHours.objects.create(store=self.store_a)
        StoreOpeningHours.objects.create(store=self.store_b)

    @patch("grocery_store_app.views.geocode_postcode")
    def test_closest_store_geolocation(self, mock_geocode):
        # Mock the coordinates returned from postcode geocoding
        mock_geocode.return_value = (-33.86, 151.20)  # Near Sydney

        response = self.client.post("/stores", data={"postcode": "2000"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your closest store is")
        self.assertContains(response, "Store A")