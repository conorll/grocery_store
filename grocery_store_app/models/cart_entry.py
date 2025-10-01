from django.db import models
from .cart import Cart 
from .product import Product 
from .per_store_product import PerStoreProduct 

class CartEntry(models.Model):
  cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="cart_entries")
  per_store_product = models.ForeignKey(PerStoreProduct, on_delete=models.CASCADE)
  quantity = models.PositiveIntegerField()

  def __str__(self):
    return f"{self.per_store_product.product.name} in cart for user {self.cart.user.first_name} {self.cart.user.last_name}"