from django.db import models

class Store(models.Model):
  name = models.CharField(max_length=50)
  address = models.CharField(max_length=255)
  postcode = models.CharField(max_length=10, null=True, blank=True)
  phone_number = models.CharField(max_length=20)
  opening_hours = models.CharField(max_length=500)
  latitude = models.FloatField(null =True, blank=True)
  longitude = models.FloatField(null =True, blank=True)