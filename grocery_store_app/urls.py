from django.urls import path, include
from django.contrib import admin
from . import views
from .views import authView

admin.site.site_title = "GSC Site Administration"
admin.site.site_header = "GSC Administration"
admin.site.index_title = "Site Administration"

urlpatterns = [
    path("", views.products, name="index"),
    path("products", views.products, name="products"),
    path("product/<int:id>", views.product, name="product"),
    path("stores", views.stores, name="stores"),
    path("product/<int:id>/select_store", views.product_select_store, name="product_select_store"),
    path("cart", views.cart, name="cart"),
    path("checkout_address", views.checkout_address, name="checkout_address"),
    path("checkout_payment", views.checkout_payment, name="checkout_payment"),
    path("confirm", views.confirm, name="confirm"),

    #Client Management
    #Registration
    path("signup/", authView, name="signup"),
    #Login/Logout/Password Management
    path("accounts/", include("django.contrib.auth.urls")),
    #Profile
    path("profile/", views.profile, name="profile"),
]