from django.db import models
from .category import Category

class Product(models.Model):
  name = models.CharField(max_length=50)
  price = models.DecimalField(max_digits=10, decimal_places= 2)
  category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")
  quantity = models.PositiveIntegerField()
  image_url = models.CharField(max_length=1000)

  def __str__(self):
    return self.name