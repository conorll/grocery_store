from django.contrib import admin
<<<<<<< HEAD
from django.contrib.auth.models import User, Group
from .models import Store, StoreOpeningHours
=======
from django.contrib.auth.admin import UserAdmin 
>>>>>>> a62b766b85c62f2e946df2fb8743f7fc6db27e8d

# Register your models here.

from .models import Category, Product, Store, PerStoreProduct, Address, Cart, CartEntry, CustomUser, CustomUserAdmin, Order, OrderItem

# Remove the default Groups from admin
## admin.site.unregister(Group)

# Unregister the default User admin and register our custom one
# admin.site.unregister(User)
# admin.site.register(User, CustomUserAdmin)

class MyUserAdmin(UserAdmin):
    model = CustomUser
    fieldsets = UserAdmin.fieldsets + ((None, {'fields': ('store',)}),)

admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Address)
admin.site.register(Cart)
admin.site.register(CartEntry)
admin.site.register(Order)
admin.site.register(OrderItem)
<<<<<<< HEAD

class StoreOpeningHoursInline(admin.StackedInline):
    model = StoreOpeningHours
    extra = 0  # No extra blank forms
    max_num = 1  # Only one opening hours block per store
=======
# admin.site.register(CustomUser)
admin.site.register(CustomUser, MyUserAdmin)
>>>>>>> a62b766b85c62f2e946df2fb8743f7fc6db27e8d

@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    exclude = ('latitude', 'longitude')  # hides the fields from admin form
<<<<<<< HEAD
    inlines = [StoreOpeningHoursInline]
=======

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
>>>>>>> a62b766b85c62f2e946df2fb8743f7fc6db27e8d
