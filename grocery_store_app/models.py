from django.db import models

# Create your models here.


class Category(models.Model):
    name = models.CharField(
        max_length=50, unique=True
    )  # prevents duplicates with unique

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(
        blank=True
    )  # A description for the product: Updated Description wasn't inside
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="products"
    )
    quantity = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    image_url = models.CharField(max_length=1000)

    class Meta:  # creation of indexes to enable faster sorting for DB: Bryce
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["price"]),
            models.Index(fields=["created_at"]),
        ]
        ordering = ["name"]  # default sort

    def __str__(self):
        return self.name
