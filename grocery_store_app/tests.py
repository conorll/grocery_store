# grocery_store_app/tests.py
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from grocery_store_app.models import Category, Product, Store, PerStoreProduct


class ProductViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Categories
        cls.cat_fruits = Category.objects.create(name="Fruits")
        cls.cat_bread = Category.objects.create(name="Bread")
        cls.cat_veg = Category.objects.create(name="Vegetables")

        # Products (match your current seed data style)
        cls.p1 = Product.objects.create(
            name="Lemon Each", price=Decimal("1.30"), category=cls.cat_fruits
        )
        cls.p2 = Product.objects.create(
            name="Granny Smith Apple Each",
            price=Decimal("0.99"),
            category=cls.cat_fruits,
        )
        cls.p3 = Product.objects.create(
            name="Cara Cara Oranges 1kg", price=Decimal("5.00"), category=cls.cat_fruits
        )
        cls.p4 = Product.objects.create(
            name="Lebanese Cucumbers 600g", price=Decimal("7.00"), category=cls.cat_veg
        )
        cls.p5 = Product.objects.create(
            name="Brown Onion Each", price=Decimal("0.80"), category=cls.cat_veg
        )
        cls.p6 = Product.objects.create(
            name="Broccoli 500g", price=Decimal("3.80"), category=cls.cat_veg
        )
        cls.p7 = Product.objects.create(
            name="White Sandwich Sliced Bread 650g",
            price=Decimal("3.00"),
            category=cls.cat_bread,
        )
        cls.p8 = Product.objects.create(
            name="Chocolate Chip Brioche Sliced Loaf 500g",
            price=Decimal("5.59"),
            category=cls.cat_bread,
        )
        cls.p9 = Product.objects.create(
            name="Bakehouse Traditional White Bread 700g",
            price=Decimal("4.00"),
            category=cls.cat_bread,
        )

        # Minimal store, plus stock for in_stock=1 filter
        cls.store = Store.objects.create(name="City Store")
        PerStoreProduct.objects.create(
            product=cls.p7, store=cls.store, quantity=5
        )  # Bread in stock
        PerStoreProduct.objects.create(
            product=cls.p2, store=cls.store, quantity=2
        )  # Apple in stock

    def _names(self, page_obj):
        return [p.name for p in page_obj.object_list]

    def test_products_page_loads(self):
        r = self.client.get(reverse("products"))
        self.assertEqual(r.status_code, 200)
        self.assertIn("page_obj", r.context)
        per_page = r.context["paginator"].per_page
        # We only created 9 products; first page will be <= per_page
        self.assertLessEqual(len(r.context["page_obj"].object_list), per_page)
        # Smoke: a couple known names appear
        self.assertContains(r, "Lemon Each")
        self.assertContains(r, "White Sandwich Sliced Bread 650g")

    def test_pagination_last_page_size(self):
        r1 = self.client.get(reverse("products"))
        paginator = r1.context["paginator"]
        last_page = paginator.num_pages
        r_last = self.client.get(reverse("products"), {"page": last_page})
        self.assertEqual(r_last.status_code, 200)
        per_page = paginator.per_page
        total = paginator.count
        expected_last = total % per_page or per_page
        self.assertEqual(len(r_last.context["page_obj"].object_list), expected_last)

    def test_keyword_filter(self):
        # Keyword matches name only (not category). 'bread' won't match brioche.
        r = self.client.get(reverse("products"), {"q": "apple"})
        names = self._names(r.context["page_obj"])
        self.assertIn("Granny Smith Apple Each", names)
        self.assertNotIn("Lemon Each", names)

    def test_category_filter(self):
        r = self.client.get(reverse("products"), {"category": "Fruits"})
        names = self._names(r.context["page_obj"])
        self.assertIn("Lemon Each", names)
        self.assertIn("Granny Smith Apple Each", names)
        self.assertNotIn("Bakehouse Traditional White Bread 700g", names)  # not Fruits

    def test_price_range_filter(self):
        # 3.00..4.00 inclusive should include 3.00, 3.80, 4.00
        r = self.client.get(
            reverse("products"), {"price_min": "3.00", "price_max": "4.00"}
        )
        names = self._names(r.context["page_obj"])
        self.assertIn("White Sandwich Sliced Bread 650g", names)  # 3.00
        self.assertIn("Broccoli 500g", names)  # 3.80
        self.assertIn("Bakehouse Traditional White Bread 700g", names)  # 4.00
        self.assertNotIn("Chocolate Chip Brioche Sliced Loaf 500g", names)  # 5.59
        self.assertNotIn("Lebanese Cucumbers 600g", names)  # 7.00

    def test_min_price_filter(self):
        # >= 2.00 should NOT include cheap fruit like 0.80/0.99
        r = self.client.get(reverse("products"), {"price_min": "2"})
        names = self._names(r.context["page_obj"])
        self.assertNotIn("Granny Smith Apple Each", names)  # 0.99
        self.assertNotIn("Brown Onion Each", names)  # 0.80
        self.assertIn("Broccoli 500g", names)  # 3.80
        self.assertIn("Bakehouse Traditional White Bread 700g", names)  # 4.00

    def test_max_price_filter(self):
        # <= 2.00 should include the cheap items
        r = self.client.get(reverse("products"), {"price_max": "2"})
        names = self._names(r.context["page_obj"])
        self.assertIn("Granny Smith Apple Each", names)  # 0.99
        self.assertIn("Brown Onion Each", names)  # 0.80
        self.assertIn("Lemon Each", names)  # 1.30
        self.assertNotIn("Broccoli 500g", names)  # 3.80

    def test_in_stock_filter(self):
        r = self.client.get(reverse("products"), {"in_stock": "1"})
        names = self._names(r.context["page_obj"])
        # Only the two we stocked should appear
        self.assertEqual(
            set(names), {"White Sandwich Sliced Bread 650g", "Granny Smith Apple Each"}
        )

    def test_combined_filters(self):
        # Within Bread category, priced 3.50..6.00 => 4.00 and 5.59
        params = {"category": "Bread", "price_min": "3.50", "price_max": "6.00"}
        r = self.client.get(reverse("products"), params)
        names = self._names(r.context["page_obj"])
        self.assertEqual(
            set(names),
            {
                "Bakehouse Traditional White Bread 700g",
                "Chocolate Chip Brioche Sliced Loaf 500g",
            },
        )

    def test_sorting_price_desc(self):
        r = self.client.get(reverse("products"), {"sort": "price_desc"})
        prices = [p.price for p in r.context["page_obj"].object_list]
        self.assertEqual(prices, sorted(prices, reverse=True))

    def test_invalid_price_input_is_ignored(self):
        # price_min invalid ⇒ ignored; price_max valid ⇒ acts as <= 3.10
        r = self.client.get(
            reverse("products"), {"price_min": "abc", "price_max": "3.10"}
        )
        names = self._names(r.context["page_obj"])
        self.assertIn("White Sandwich Sliced Bread 650g", names)  # 3.00
        self.assertNotIn("Broccoli 500g", names)  # 3.80 out of range

    def test_session_persists_filters_u120(self):
        # First request saves filters to session
        first = self.client.get(
            reverse("products"), {"q": "apple", "price_max": "2.00"}
        )
        self.assertEqual(first.status_code, 200)
        names_first = self._names(first.context["page_obj"])
        self.assertIn("Granny Smith Apple Each", names_first)
        # Second request with NO querystring should restore filters (U120)
        second = self.client.get(reverse("products"))
        names_second = self._names(second.context["page_obj"])
        self.assertEqual(names_first, names_second)

    def test_json_api_uses_same_filters(self):
        r = self.client.get(reverse("products_api"), {"q": "cucumber"})
        self.assertEqual(r.status_code, 200)
        data = r.json()
        names = [row["name"] for row in data["results"]]
        self.assertIn("Lebanese Cucumbers 600g", names)
        self.assertNotIn("Lemon Each", names)
