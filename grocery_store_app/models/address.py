from django.db import models
from django.contrib.auth import get_user_model
from .users import *

#User = get_user_model()

class Address(models.Model):
  user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
  first_name = models.CharField(max_length=50)
  last_name = models.CharField(max_length=50)
  address = models.CharField(max_length=100)
  address2 = models.CharField(max_length=100)
  suburb = models.CharField(max_length=50)
  state = models.CharField(max_length=50)
  postcode = models.PositiveIntegerField()

  def __str__(self):
    return f"{self.first_name} {self.last_name} - {self.address1}"