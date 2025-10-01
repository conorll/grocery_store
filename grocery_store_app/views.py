from django.shortcuts import render, redirect, get_object_or_404

from .models import Product
from .models import Cart , CartEntry
from .models import Store
from .models import PerStoreProduct 
from .models import Address 
from .models import Payment 
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

def product(request, id):
    product_object = get_object_or_404(Product, id=id)

    per_store_products = PerStoreProduct.objects.filter(
            product_id=id
        )
    
    
    store_objects = Store.objects.all()

    store_quantities = {}

    for per_store_product in per_store_products:
        store_quantities[per_store_product.store_id] = per_store_product.quantity

    stores = []

    for store in store_objects:
        stores.append({
            "id": store.id,
            "name": store.name,
            "quantity": store_quantities.get(store.id, -1),
        })
    
    selected_store = None

    selected_store_id = request.session.get("selected_store_id")
    if (selected_store_id):
        store = Store.objects.filter(id=selected_store_id).first()
        selected_store = {
            "id": store.id,
            "name": store.name,
            "quantity": store_quantities.get(store.id, -1),
        }
    
    return render(
        request, "grocery_store_app/product.html", 
        {
            "product": product_object,
            "stores": stores,
            "selected_store": selected_store
         }
    )

@login_required
def checkout_address(request):

    cart, _ = Cart.objects.get_or_create(user=request.user)
    entries = cart.cart_entries.select_related()

    if len(entries) == 0:
        return redirect("index")

    if request.method == "POST":
        first_name = request.POST.get("first-name")
        last_name = request.POST.get("last-name")
        form_address = request.POST.get("address")
        form_address2 = request.POST.get("address2")
        suburb = request.POST.get("suburb")
        postcode = request.POST.get("postcode")

        try:
            address = Address.objects.get(user=request.user)
            address.delete()
        except:
            print("")
        address = Address.objects.create(user=request.user, first_name = first_name, last_name = last_name, address = form_address, address2 = form_address2, suburb=suburb, postcode=postcode)

        return redirect("checkout_payment")

    return render(
        request, "grocery_store_app/checkout_address.html"
    )

@login_required
def checkout_payment(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    entries = cart.cart_entries.select_related()

    if len(entries) == 0:
        return redirect("index")

    try:
        address = Address.objects.get(user=request.user)
    except:
        return redirect("index")


    if request.method == "POST":
        card_number = request.POST.get("card-number")
        expiration_month = request.POST.get("expiration-month")
        expiration_year = request.POST.get("expiration-year")
        cvc = request.POST.get("cvc")

        try:
            payment = Payment.objects.get(user=request.user)
            payment.delete()
        except:
            print("")
        payment = Payment.objects.create(user=request.user, card_number=card_number, expiration_month=expiration_month, expiration_year=expiration_year, cvc=cvc)

        for entry in entries:
            entry.per_store_product.quantity -= entry.quantity
            entry.per_store_product.save()

        cart.cart_entries.all().delete()

        return redirect("confirm")

    return render(
        request, "grocery_store_app/checkout_payment.html"
    )

def confirm(request):
    return render(
        request, "grocery_store_app/confirm.html"
    )

@login_required
def cart(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)

    if request.method == "POST":
        product_id = int(request.POST.get("id"))
        store_id = int(request.session.get("selected_store_id"))
        quantity = int(request.POST.get("quantity"))

        per_store_product = get_object_or_404(PerStoreProduct, product_id=product_id, store_id=store_id)

        if quantity == 0:
            try:
                entry = CartEntry.objects.get(
                    cart=cart,
                    per_store_product=per_store_product,
                )
                entry.delete()
                return redirect("cart")
            except:
                return redirect("cart")

        entry, created = CartEntry.objects.get_or_create(
            cart=cart,
            per_store_product=per_store_product,
            defaults={"quantity": quantity}
        )

        if not created:
            entry.quantity = quantity
            entry.save()
        return redirect("cart")
    
    entries = cart.cart_entries.select_related("per_store_product")
    
    entry_list = []
    cart_total = 0

    for entry in entries:
        item_total = entry.per_store_product.product.price * entry.quantity
        cart_total += item_total
        entry_list.append({
            "per_store_product": entry.per_store_product,
            "quantity": entry.quantity,
            "item_total": item_total,
        })

    return render(request, "grocery_store_app/cart.html", {
        "cart": entry_list,
        "cart_total": cart_total
    })


def product_select_store(request, id):

    if request.method == "POST":
        store_id = request.POST.get("store")
        if store_id:
            request.session["selected_store_id"] = int(store_id)

        cart, _ = Cart.objects.get_or_create(user=request.user)

        cart.cart_entries.all().delete()

        return redirect("product", id=id)


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


# Client Management - User Registration
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

# User Profile View
@login_required
def profile(request):
    return render(request, "grocery_store_app/profile.html", {"user": request.user})
