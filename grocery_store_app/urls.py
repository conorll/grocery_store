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
    path("add_cart", views.add_cart, name="add_cart"),
    path("checkout_address", views.checkout_address, name="checkout_address"),
    path("checkout_payment", views.checkout_payment, name="checkout_payment"),
    path("confirm", views.confirm, name="confirm"),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),

    #Client Management
    #Registration
    path("signup/", authView, name="signup"),
    #Login/Logout/Password Management
    path("accounts/", include("django.contrib.auth.urls")),
    #Profile
    path("profile/", views.profile, name="profile"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),
    #Payment Management
    path("profile/payment/add/", views.add_payment_method, name="add_payment"),
    path("profile/payment/edit/", views.edit_payment_method, name="edit_payment"),
    path("profile/payment/remove/", views.remove_payment_method, name="remove_payment"),
    #Admin Dashboard
    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),
]