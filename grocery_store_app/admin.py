from django.contrib import admin
from django.contrib.auth.admin import UserAdmin 

# Register your models here.

from .models import Category, Product, Store, PerStoreProduct, Address, CustomUser

class MyUserAdmin(UserAdmin):
    model = CustomUser
    fieldsets = UserAdmin.fieldsets + ((None, {'fields': ('store',)}),)

admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Address)
admin.site.register(CustomUser, MyUserAdmin)

@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    exclude = ('latitude', 'longitude')  # hides the fields from admin form

@admin.register(PerStoreProduct)
class QuantityAdmin(admin.ModelAdmin):
    def has_view_permission(self, request, obj=None):
        if request.user.is_staff or request.user.is_superuser:
            return True
        return False

    def has_change_permission(self, request, obj=None):
        if request.user.is_staff or request.user.is_superuser:
            return True
        return False
    
    def has_module_permission(self, request):
        if request.user.is_staff or request.user.is_superuser:
            return True
        return False

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(store__name=request.user.store)
