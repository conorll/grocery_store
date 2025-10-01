from django.db import models
from .order import Order
from .product import Product
from .per_store_product import PerStoreProduct

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    per_store_product = models.ForeignKey(PerStoreProduct, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.quantity} × {self.product.name} (Order #{self.order.id})"

    def subtotal(self):
        return self.quantity * self.price
    
    def total_price(self):
        return self.quantity * self.price