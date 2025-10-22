from decimal import Decimal
from django.test import TestCase
from grocery_store_app.models import Category, Product, PerStoreProduct, Store, Cart, Address, Payment
from grocery_store_app.views import create_order_from_cart
from django.contrib.auth import get_user_model

User = get_user_model()

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

        # Create a valid category
        self.category = Category.objects.create(name="Test Category")
        
        # Create product without quantity
        self.product = Product.objects.create(
            name="Test Product",
            price=Decimal("10.00"),
            category=self.category 
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

    def test_create_order_successfully(self):
        order = create_order_from_cart(self.user)
        self.assertIsNotNone(order)
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.total, Decimal("20.00"))  # 2 × 10.00