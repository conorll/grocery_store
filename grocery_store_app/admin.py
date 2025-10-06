from django.contrib import admin
from django.contrib.auth.models import User, Group

# Register your models here.

from .models import Category, Product, Store, PerStoreProduct, Address, Cart, CartEntry, CustomUserAdmin

# Remove the default Groups from admin
admin.site.unregister(Group)

# Unregister the default User admin and register our custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

admin.site.register(Category)
admin.site.register(Product)
admin.site.register(PerStoreProduct)
admin.site.register(Address)
admin.site.register(Cart)
admin.site.register(CartEntry)

@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    exclude = ('latitude', 'longitude')  # hides the fields from admin form