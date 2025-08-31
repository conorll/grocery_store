from django.contrib import admin

# Register your models here.

from .models import Category, Product, Store

admin.site.register(Category)
admin.site.register(Product)
@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    exclude = ('latitude', 'longitude')  # hides the fields from admin form