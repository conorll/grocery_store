from django.shortcuts import render

from .models import Product
from .models_ import Store
from .forms import PostcodeForm
from .utils import geocode_postcode, haversine
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

def stores(request):
    store_objects = Store.objects.exclude(latitude__isnull=True, longitude__isnull=True)
    closest_store = None
    distance_km = None

    if request.method == 'POST':
        form = PostcodeForm(request.POST)
        if form.is_valid():
            postcode = form.cleaned_data['postcode']
            user_lat, user_lng = geocode_postcode(postcode)

            if user_lat and user_lng:
                min_distance = float('inf')
                for store in store_objects:
                    dist = haversine(user_lat, user_lng, store.latitude, store.longitude)
                    if dist < min_distance:
                        min_distance = dist
                        closest_store = store
                        distance_km = round(min_distance, 2)
    else:
        form = PostcodeForm()

    return render(request, "grocery_store_app/stores.html", {
        "stores": store_objects,
        "form": form,
        "closest_store": closest_store,
        "distance_km": distance_km
    })

def get_postcode(request):
    if request.method == 'POST':
        form = PostcodeForm(request.POST)
        if form.is_valid():
            postcode = form.cleaned_data['postcode']
            return render(request, 'store_result.html', {'postcode': postcode})
    else:
        form = PostcodeForm()
    return render(request, 'get_postcode.html', {'form': form})
