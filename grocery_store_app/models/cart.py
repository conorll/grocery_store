from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Cart(models.Model):
  user = models.ForeignKey(User, on_delete=models.CASCADE)

  def __str__(self):
    return f"Cart for user {self.user.first_name} {self.user.last_name}"