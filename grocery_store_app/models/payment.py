from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Payment(models.Model):
  user = models.ForeignKey(User, on_delete=models.CASCADE)
  card_number = models.PositiveIntegerField()
  expiration_month = models.PositiveIntegerField()
  expiration_year = models.PositiveIntegerField()
  cvc = models.PositiveIntegerField()

  def __str__(self):
    return f"Payment method id:{self.id}"