from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from grocery_store_app.models import Category, Product, PerStoreProduct, Store, Cart, Address, Payment
from django.contrib.auth import get_user_model

User = get_user_model()

class ProductViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        #create a default store for all test products
        cls.store = Store.objects.create(
            name="Test Store",
            address="123 Test Street",
            postcode="2000",
            latitude=0,
            longitude=0
        )
        # Categories
        cls.fruits = Category.objects.create(name="Fruits")
        cls.veggies = Category.objects.create(name="Vegetables")

        # Three named products for deterministic checks
        apple = Product.objects.create(
            name="Apple", price=Decimal("1.50"), category=cls.fruits
        )
        banana = Product.objects.create(
            name="Banana", price=Decimal("2.00"), category=cls.fruits
        )
        carrot = Product.objects.create(
            name="Carrot", price=Decimal("3.00"), category=cls.veggies
        )

        # Assign stock via PerStoreProduct
        PerStoreProduct.objects.bulk_create([
            PerStoreProduct(product=apple, store=cls.store, quantity=10),
            PerStoreProduct(product=banana, store=cls.store, quantity=20),
            PerStoreProduct(product=carrot, store=cls.store, quantity=30),
        ])

        # Extra items to exercise pagination (> 1 page)
        # We’ll make total 25 so last page is partial for most per_page values.
        for i in range(1, 23):
            prod = Product.objects.create(
                name=f"Item {i}",
                price=Decimal(i),
                category=cls.fruits if i % 2 else cls.veggies,
            )
            PerStoreProduct.objects.create(product=prod, store=cls.store, quantity=5)

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

class OrderCreationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")

        # Create store
        self.store = Store.objects.create(
            name="Test Store",
            address="123 Test St",
            postcode="2000",
            latitude=0,
            longitude=0
        )

        # Create product without quantity
        self.product = Product.objects.create(
            name="Test Product",
            price=Decimal("10.00"),
            category=None  
        )

        # Create PerStoreProduct with quantity
        self.per_store_product = PerStoreProduct.objects.create(
            product=self.product,
            store=self.store,
            quantity=5
        )

        # Create a cart
        self.cart = Cart.objects.create(user=self.user)
        self.cart.cart_entries.create(
            per_store_product=self.per_store_product,
            quantity=2
        )

        # Address + payment
        self.address = Address.objects.create(
            user=self.user,
            first_name="Test",
            last_name="User",
            address="123",
            suburb="Suburb",
            postcode="2000"
        )
        self.payment = Payment.objects.create(
            user=self.user,
            card_number="1234",
            expiration_month="12",
            expiration_year="2025",
            cvc="123"
        )