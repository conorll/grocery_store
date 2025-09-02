from django.shortcuts import render, redirect, get_object_or_404

from .models import Product
from .models import Store
from .forms import PostcodeForm, CustomUserCreationForm
from .utils import geocode_postcode, haversine
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import login
from django.db.models import Q
from django.core.paginator import Paginator
from urllib.parse import urlencode
from decimal import Decimal, InvalidOperation

# Create your views here.


def _dec(val):
    if val in (None, ""):
        return None
    try:
        return Decimal(val)
    except (InvalidOperation, TypeError):
        return None


def index(request):
    return render(request, "grocery_store_app/index.html")


def products(request):
    product_objects = Product.objects.all()
    return render(
        request, "grocery_store_app/products.html", {"products": product_objects}
    )


def product(request, id):
    product_object = get_object_or_404(Product, id=id)
    return render(
        request, "grocery_store_app/product.html", {"product": product_object}
    )


def products(request):
    qs = Product.objects.all()

    q = (request.GET.get("q") or "").strip()
    min_price = _dec(request.GET.get("min_price"))
    max_price = _dec(request.GET.get("max_price"))
    sort = (request.GET.get("sort") or "").strip()
    per_page = request.GET.get("per_page") or "12"

    if q:
        qs = qs.filter(Q(name__icontains=q))

    if min_price is not None:
        qs = qs.filter(price__gte=min_price)
    if max_price is not None:
        qs = qs.filter(price__lte=max_price)

    sort_map = {
        "price_asc": "price",
        "price_desc": "-price",
        "name_asc": "name",
        "name_desc": "-name",
        "newest": "-id",
        "oldest": "id",
    }
    qs = qs.order_by(sort_map.get(sort, "id"))

    try:
        per_page_int = max(1, min(60, int(per_page)))
    except ValueError:
        per_page_int = 12

    paginator = Paginator(qs, per_page_int)
    page_obj = paginator.get_page(request.GET.get("page"))

    params = request.GET.dict()
    params.pop("page", None)
    querystring = urlencode(params)

    return render(
        request,
        "grocery_store_app/products.html",
        {
            "products": page_obj,
            "page_obj": page_obj,
            "paginator": paginator,
            "query": q,
            "min_price": request.GET.get("min_price") or "",
            "max_price": request.GET.get("max_price") or "",
            "sort": sort,
            "per_page": per_page_int,
            "querystring": querystring,
            "per_page_options": [12, 24, 36, 48, 60],
        },
    )


# Stores listing and closest store finder view
def stores(request):
    # Get all stores with valid coordinates
    store_objects = Store.objects.exclude(latitude__isnull=True, longitude__isnull=True)
    closest_store = None
    distance_km = None

    # Handle postcode form submission
    if request.method == "POST":
        form = PostcodeForm(request.POST)
        if form.is_valid():
            postcode = form.cleaned_data["postcode"]
            # Geocode the postcode to get latitude and longitude
            user_lat, user_lng = geocode_postcode(postcode)

            if user_lat and user_lng:
                min_distance = float("inf")
                # Find the closest store using haversine formula
                for store in store_objects:
                    dist = haversine(
                        user_lat, user_lng, store.latitude, store.longitude
                    )
                    if dist < min_distance:
                        min_distance = dist
                        closest_store = store
                        distance_km = round(min_distance, 2)
    else:
        form = PostcodeForm()

    # Render the stores page with form and closest store info
    return render(
        request,
        "grocery_store_app/stores.html",
        {
            "stores": store_objects,
            "form": form,
            "closest_store": closest_store,
            "distance_km": distance_km,
        },
    )


# Client Management
def authView(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("index")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomUserCreationForm()

    return render(request, "registration/signup.html", {"form": form})


def profile(request):
    return render(request, "grocery_store_app/profile.html", {"user": request.user})
