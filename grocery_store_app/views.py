from django.shortcuts import render, redirect

from .models import Product
from .models import Store
from .forms import PostcodeForm, CustomUserCreationForm
from .utils import geocode_postcode, haversine
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import login

# Create your views here.

def index(request):
  return render(request, "grocery_store_app/index.html")

def products(request):
  product_objects = Product.objects.all()
  return render(request, "grocery_store_app/products.html", {
    "products": product_objects
  })

#Stores listing and closest store finder view
def stores(request):
    # Get all stores with valid coordinates
    store_objects = Store.objects.exclude(latitude__isnull=True, longitude__isnull=True)
    closest_store = None
    distance_km = None

    # Handle postcode form submission
    if request.method == 'POST':
        form = PostcodeForm(request.POST)
        if form.is_valid():
            postcode = form.cleaned_data['postcode']
            # Geocode the postcode to get latitude and longitude
            user_lat, user_lng = geocode_postcode(postcode)

            if user_lat and user_lng:
                min_distance = float('inf')
                # Find the closest store using haversine formula
                for store in store_objects:
                    dist = haversine(user_lat, user_lng, store.latitude, store.longitude)
                    if dist < min_distance:
                        min_distance = dist
                        closest_store = store
                        distance_km = round(min_distance, 2)
    else:
        form = PostcodeForm()

    # Render the stores page with form and closest store info
    return render(request, "grocery_store_app/stores.html", {
        "stores": store_objects,
        "form": form,
        "closest_store": closest_store,
        "distance_km": distance_km
    })

#Client Management
def authView(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("index")
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserCreationForm()
    
    return render(request, "registration/signup.html", {"form": form})

def profile(request):
    return render(request, "grocery_store_app/profile.html", {"user": request.user})