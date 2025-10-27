from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from grocery_store_app.utils import geocode_postcode
from datetime import time

class Store(models.Model):
  name = models.CharField(max_length=50)
  address = models.CharField(max_length=255)
  postcode = models.CharField(max_length=10, null=True, blank=True)
  phone_number = models.CharField(max_length=20)
  # make latitude and longitude not required
  latitude = models.FloatField(null =True, blank=True)
  longitude = models.FloatField(null =True, blank=True)
  
  def __str__(self):
    return self.name

class StoreOpeningHours(models.Model):
    store = models.OneToOneField("Store", on_delete=models.CASCADE, related_name="hours")

    monday_open = models.TimeField(default=time(9, 0))
    monday_close = models.TimeField(default=time(17, 0))
    tuesday_open = models.TimeField(default=time(9, 0))
    tuesday_close = models.TimeField(default=time(17, 0))
    wednesday_open = models.TimeField(default=time(9, 0))
    wednesday_close = models.TimeField(default=time(17, 0))
    thursday_open = models.TimeField(default=time(9, 0))
    thursday_close = models.TimeField(default=time(17, 0))
    friday_open = models.TimeField(default=time(9, 0))
    friday_close = models.TimeField(default=time(17, 0))
    saturday_open = models.TimeField(default=time(10, 0))
    saturday_close = models.TimeField(default=time(16, 0))
    sunday_open = models.TimeField(default=time(10, 0))
    sunday_close = models.TimeField(default=time(16, 0))

    def __str__(self):
        return f"Opening Hours for {self.store.name}"
  
#when the store model sends a pre_save signal, run this function
@receiver(pre_save, sender=Store)
def geocode_store(sender, instance: Store, **kwargs):
    if instance.postcode and (instance.latitude is None or instance.longitude is None):
        lat, lon = geocode_postcode(instance.postcode)
        instance.latitude = lat
        instance.longitude = lon
