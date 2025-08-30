from django.shortcuts import render

from .models import Product
from .models_ import Store
# Create your views here.
from django.http import HttpResponse


def index(request):
  return render(request, "grocery_store_app/index.html")

def products(request):
  product_objects = Product.objects.all()
  return render(request, "grocery_store_app/products.html", {
    "products": product_objects
  })

def stores(request):
  store_objects = Store.objects.all()
  return render(request, "grocery_store_app/stores.html", {
    "stores": store_objects
  })
