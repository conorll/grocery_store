from django.test import TestCase
from django.contrib.auth.models import User
from grocery_store_app.models import Cart, Store, PerStoreProduct, Product, Category, CartEntry
from grocery_store_app.views import update_cart


class UpdateCartTests(TestCase):
  def setUp(self):
    self.user = User.objects.create_user(username="testuser", password="password")

    self.store = Store.objects.create(
      name="Test Store",
      latitude=10.0,
      longitude=10.0,
    )

    self.category = Category.objects.create(name="Test Category")

    self.product = Product.objects.create(
      name="Test Product",
      price=1.04,
      category=self.category,
    )

    self.per_store_product = PerStoreProduct.objects.create(
      product=self.product,
      store=self.store,
      quantity=10
    )

    self.cart = Cart.objects.create(user=self.user)

  def test_valid_quantity(self):
    update_cart(self.cart, self.per_store_product, 3)


    entries = self.cart.cart_entries.select_related("per_store_product")

    self.assertEqual(len(entries), 1)

    cart_entry = CartEntry.objects.get(cart=self.cart, per_store_product=self.per_store_product) 

    self.assertEqual(cart_entry.quantity, 3)

  def test_remove_with_quantity_zero(self):
    update_cart(self.cart, self.per_store_product, 3)
    update_cart(self.cart, self.per_store_product, 0)
    self.assertFalse(CartEntry.objects.filter(cart=self.cart).exists())

  def test_invalid_negative_quantity(self):
    with self.assertRaises(Exception) as context:
      update_cart(self.cart, self.per_store_product, -1)
    self.assertEqual(str(context.exception), "Purchase quantity cannot be negative")
    self.assertFalse(CartEntry.objects.filter(cart=self.cart).exists())

  def test_invalid_exceeding_quantity(self):
    with self.assertRaises(Exception) as context:
      update_cart(self.cart, self.per_store_product, 11)
    self.assertEqual(str(context.exception), "Purchase quantity must be less than or equal to the available quantity: 10")
    self.assertFalse(CartEntry.objects.filter(cart=self.cart).exists())