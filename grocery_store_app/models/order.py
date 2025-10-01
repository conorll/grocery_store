from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal

class Order(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    total = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} by {self.user.username}"
    
    def subtotal(self):
        return sum(item.price() for item in self.items.all())

    def gst(self):
        return self.subtotal() * Decimal('0.10')  # 10% GST

    def total_with_gst(self):
        return self.subtotal() + self.gst()