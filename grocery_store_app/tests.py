# grocery_store_app/tests.py
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from .models import Category, Product, CustomUser


class ProductViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Categories
        cls.fruits = Category.objects.create(name="Fruits")
        cls.veggies = Category.objects.create(name="Vegetables")

        # Three named products for deterministic checks
        Product.objects.create(
            name="Apple", price=Decimal("1.50"), category=cls.fruits
        )
        Product.objects.create(
            name="Banana", price=Decimal("2.00"), category=cls.fruits
        )
        Product.objects.create(
            name="Carrot", price=Decimal("3.00"), category=cls.veggies
        )

        # Extra items to exercise pagination (> 1 page)
        # We’ll make total 25 so last page is partial for most per_page values.
        for i in range(1, 22 + 1):  # 22 more products: Item 1..22
            Product.objects.create(
                name=f"Item {i}",
                price=Decimal(i),  # 1..22
                category=cls.fruits if i % 2 else cls.veggies,
            )

    def test_products_page_loads(self):
        r = self.client.get(reverse("products"))
        self.assertEqual(r.status_code, 200)
        # Use the paginator’s per_page so test matches whatever the view uses (12, 20, etc.)
        self.assertIn("page_obj", r.context)
        per_page = r.context["paginator"].per_page
        self.assertEqual(len(r.context["page_obj"].object_list), per_page)
        # Basic smoke: named items are present somewhere (first page likely has at least some)
        self.assertContains(r, "Apple")
        self.assertContains(r, "Banana")
        self.assertContains(r, "Carrot")

    def test_pagination_last_page_size(self):
        # Go to the last page and compute expected size dynamically
        r1 = self.client.get(reverse("products"))
        paginator = r1.context["paginator"]
        last_page = paginator.num_pages

        r_last = self.client.get(reverse("products"), {"page": last_page})
        self.assertEqual(r_last.status_code, 200)

        per_page = paginator.per_page
        total = paginator.count
        expected_last = total % per_page or per_page
        self.assertEqual(len(r_last.context["page_obj"].object_list), expected_last)

    def test_search_by_name(self):
        r = self.client.get(reverse("products"), {"q": "Apple"})
        self.assertContains(r, "Apple")
        self.assertNotContains(r, "Banana")
        self.assertNotContains(r, "Carrot")

    def test_min_price_filter(self):
        r = self.client.get(reverse("products"), {"min_price": "2"})
        self.assertContains(r, "Banana")
        self.assertContains(r, "Carrot")
        self.assertNotContains(r, "Apple")

    def test_max_price_filter(self):
        r = self.client.get(reverse("products"), {"max_price": "2"})
        self.assertContains(r, "Apple")
        self.assertContains(r, "Banana")
        self.assertNotContains(r, "Carrot")


    def test_sort_price_desc(self):
        # Support either param name; your UI uses sort=price_desc
        r = self.client.get(
            reverse("products"), {"sort": "price_desc", "ordering": "-price"}
        )
        self.assertEqual(r.status_code, 200)
        page_list = list(r.context["page_obj"].object_list)
        # Non-increasing prices across the page
        self.assertTrue(
            all(
                page_list[i].price >= page_list[i + 1].price
                for i in range(len(page_list) - 1)
            )
        )

