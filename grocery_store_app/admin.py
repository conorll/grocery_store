from django.contrib import admin

# Register your models here.

from .models import Category, Product, Store, PerStoreProduct, Address, CustomUser

admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Address)
admin.site.register(CustomUser)

@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    exclude = ('latitude', 'longitude')  # hides the fields from admin form

@admin.register(PerStoreProduct)
class QuantityAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        #qs.filter()