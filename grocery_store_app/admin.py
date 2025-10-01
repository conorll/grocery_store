from django.contrib import admin

# Register your models here.

from .models import Category, Product, Store, PerStoreProduct, Address, Cart, CartEntry

admin.site.register(Category)
admin.site.register(Product)
admin.site.register(PerStoreProduct)
admin.site.register(Address)
admin.site.register(Cart)
admin.site.register(CartEntry)
@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    exclude = ('latitude', 'longitude')  # hides the fields from admin form