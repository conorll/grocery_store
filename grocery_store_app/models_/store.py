from django.db import models

class Store(models.Model):
  name = models.CharField(max_length=50)
  address = models.CharField()
  phone_number = models.CharField()
  description = models.CharField()
  latitude = models.FloatField()
  longitude = models.FloatField()