from django.urls import path, include
from . import views
from .views import authView

urlpatterns = [
    path("", views.index, name="index"),
    path("products", views.products, name="products"),
    path("product/<int:id>", views.product, name="product"),
    path("stores", views.stores, name="stores"),

    #Client Management
    path("signup/", authView, name="signup"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("profile/", views.profile, name="profile"),
]