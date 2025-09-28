from django.db import models
from .product import Product 
from .store import Store 

class PerStoreProduct(models.Model):
  product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="per_store_products")
  store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="per_store_products")
  quantity = models.PositiveIntegerField()

  def __str__(self):
    return f"{self.product.name} at {self.store.name} - {self.quantity} in stock"