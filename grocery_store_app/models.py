from django.db import models

# Create your models here.

class Category(models.Model):
  name = models.CharField(max_length=50)

  def __str__(self):
    return self.name

  
class Product(models.Model):
  name = models.CharField(max_length=50)
  description = models.CharField(max_length=500)
  price = models.DecimalField(max_digits=10, decimal_places= 2)
  category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")
  quantity = models.PositiveIntegerField()

  def __str__(self):
    return self.name