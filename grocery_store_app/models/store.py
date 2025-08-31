from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from grocery_store_app.utils import geocode_postcode

class Store(models.Model):
  name = models.CharField(max_length=50)
  address = models.CharField(max_length=255)
  postcode = models.CharField(max_length=10, null=True, blank=True)
  phone_number = models.CharField(max_length=20)
  opening_hours = models.CharField(max_length=500)
  # make latitude and longitude not required
  latitude = models.FloatField(null =True, blank=True)
  longitude = models.FloatField(null =True, blank=True)
  
  def __str__(self):
    return self.name
  
#when the store model sends a pre_save signal, run this function
@receiver(pre_save, sender=Store)
def geocode_store(sender, instance: Store, **kwargs):
    if instance.postcode and (instance.latitude is None or instance.longitude is None):
        lat, lon = geocode_postcode(instance.postcode)
        instance.latitude = lat
        instance.longitude = lon
