from django.test import TestCase
from django.urls import reverse
from .models import Product
from .category import Category


class ProductViewTests(TestCase):
    def setUp(self):
        # Create categories
        fruits = Category.objects.create(name="Fruits")
        veggies = Category.objects.create(name="Vegetables")

        # Create products in categories
        Product.objects.create(
            name="Apple",
            price=1.50,
            quantity=10,
            image_url="https://upload.wikimedia.org/wikipedia/commons/1/15/Red_Apple.jpg",
            category=fruits,
        )
        Product.objects.create(
            name="Banana",
            price=2.00,
            quantity=20,
            image_url="https://upload.wikimedia.org/wikipedia/commons/8/8a/Banana-Single.jpg",
            category=fruits,
        )
        Product.objects.create(
            name="Carrot",
            price=3.00,
            quantity=30,
            image_url="https://upload.wikimedia.org/wikipedia/commons/c/c3/Carrots_at_Ljubljana_Central_Market.JPG",
            category=veggies,
        )

    def test_products_page_loads(self):
        response = self.client.get(reverse("products"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Apple")
        self.assertContains(response, "Banana")
        self.assertContains(response, "Carrot")

    def test_search_by_name(self):
        response = self.client.get(reverse("products"), {"q": "Apple"})
        self.assertContains(response, "Apple")
        self.assertNotContains(response, "Banana")
        self.assertNotContains(response, "Carrot")

    def test_min_price_filter(self):
        response = self.client.get(reverse("products"), {"min_price": "2"})
        self.assertContains(response, "Banana")
        self.assertContains(response, "Carrot")
        self.assertNotContains(response, "Apple")

    def test_max_price_filter(self):
        response = self.client.get(reverse("products"), {"max_price": "2"})
        self.assertContains(response, "Apple")
        self.assertContains(response, "Banana")
        self.assertNotContains(response, "Carrot")

    def test_sort_price_desc(self):
        response = self.client.get(reverse("products"), {"sort": "price_desc"})
        products = list(response.context["products"])
        self.assertGreaterEqual(products[0].price, products[-1].price)

    def test_pagination(self):
        response = self.client.get(reverse("products"), {"per_page": 2})
        self.assertContains(response, "Apple")
        self.assertContains(response, "Banana")
        self.assertNotContains(response, "Carrot")

        response_page2 = self.client.get(
            reverse("products"), {"per_page": 2, "page": 2}
        )
        self.assertContains(response_page2, "Carrot")
        self.assertNotContains(response_page2, "Apple")

    def test_category_filter(self):
        response = self.client.get(reverse("products"), {"category": "Fruits"})
        self.assertContains(response, "Apple")
        self.assertContains(response, "Banana")
        self.assertNotContains(response, "Carrot")

        response2 = self.client.get(reverse("products"), {"category": "Vegetables"})
        self.assertContains(response2, "Carrot")
        self.assertNotContains(response2, "Apple")
        self.assertNotContains(response2, "Banana")
