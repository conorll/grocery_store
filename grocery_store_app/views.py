from django.shortcuts import render, redirect, get_object_or_404

from .models import Product
from .models import Cart , CartEntry
from .models import Store
from .models import PerStoreProduct 
from .models import Address 
from .models import Payment
from .models.order import Order
from .forms import PostcodeForm, CustomUserCreationForm
from .utils import geocode_postcode, haversine
from .services import create_order_from_cart
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import login
from django.db.models import Q
from django.core.paginator import Paginator
from urllib.parse import urlencode
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

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

        # After saving the payment, create the order and order items:
        order = create_order_from_cart(request.user)

        if not order:
            messages.error(request, "Something went wrong creating your order. Please try again.")
            return redirect("cart")

        return redirect("confirm")

    return render(
        request, "grocery_store_app/checkout_payment.html"
    )

def confirm(request):
    return render(
        request, "grocery_store_app/confirm.html"
    )

def update_cart(cart, per_store_product, quantity):
    if quantity < 0:
        raise Exception(f"Purchase quantity cannot be negative")

    if quantity > per_store_product.quantity:
        raise Exception(f"Purchase quantity must be less than or equal to the available quantity: {per_store_product.quantity}")

    if quantity == 0:
        try:
            entry = CartEntry.objects.get(
                cart=cart,
                per_store_product=per_store_product,
            )
            entry.delete()
            return
        except:
            return

    entry, created = CartEntry.objects.get_or_create(
        cart=cart,
        per_store_product=per_store_product,
        defaults={"quantity": quantity}
    )

    if not created:
        entry.quantity = quantity
        entry.save()

@login_required
def add_cart(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)

    if request.method == "POST":
        product_id = int(request.POST.get("id"))
        store_id = int(request.session.get("selected_store_id"))

        quantity = int(request.POST.get("quantity"))

        per_store_product = get_object_or_404(PerStoreProduct, product_id=product_id, store_id=store_id)

        entry, _ = CartEntry.objects.get_or_create(
            cart=cart,
            per_store_product=per_store_product,
            defaults={"quantity": 0}
        )

        try:
            update_cart(cart, per_store_product, entry.quantity + quantity)
        except Exception as e:
            messages.error(request, str(e))
            return redirect("product", id=product_id)

    return redirect("cart")


@login_required
def cart(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)

    if request.method == "POST":
        product_id = int(request.POST.get("id"))
        store_id = int(request.session.get("selected_store_id"))

        quantity = int(request.POST.get("quantity"))

        per_store_product = get_object_or_404(PerStoreProduct, product_id=product_id, store_id=store_id)

        try:
            update_cart(cart, per_store_product, quantity)
        except Exception as e:
            messages.error(request, str(e))

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

@login_required
def product_select_store(request, id):

    if request.method == "POST":
        store_id = request.POST.get("store")
        if store_id:
            request.session["selected_store_id"] = int(store_id)

        cart, _ = Cart.objects.get_or_create(user=request.user)

        cart.cart_entries.all().delete()

        return redirect("product", id=id)
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
    store_objects = Store.objects.exclude(latitude__isnull=True, longitude__isnull=True).select_related("hours")
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

# Profile View
@login_required
def profile(request):
    user = request.user
    active_orders = user.orders.filter(status='active')
    past_orders = user.orders.filter(status='completed').order_by('-created_at')[:5]

    return render(request, "grocery_store_app/profile.html", {
        "user": user,
        "active_orders": active_orders,
        "past_orders": past_orders,
    })

# Edit Profile View
@login_required
def edit_profile(request):
    if request.method == "POST":
        user = request.user
        
        # Update basic user information
        user.username = request.POST.get("username", user.username)
        user.email = request.POST.get("email", user.email)
        user.first_name = request.POST.get("first_name", user.first_name)
        user.last_name = request.POST.get("last_name", user.last_name)
        
        # Handle password change
        current_password = request.POST.get("current_password")
        new_password1 = request.POST.get("new_password1")
        new_password2 = request.POST.get("new_password2")
        
        errors = []
        
        # Validate email uniqueness
        from django.contrib.auth.models import User
        if User.objects.filter(email=user.email).exclude(id=user.id).exists():
            errors.append("This email address is already in use.")
        
        # Validate username uniqueness
        if User.objects.filter(username=user.username).exclude(id=user.id).exists():
            errors.append("This username is already in use.")
        
        # Validate password change if provided
        if current_password or new_password1 or new_password2:
            if not current_password:
                errors.append("Current password is required to change password.")
            elif not user.check_password(current_password):
                errors.append("Current password is incorrect.")
            elif new_password1 != new_password2:
                errors.append("New passwords do not match.")
            elif len(new_password1) < 8:
                errors.append("New password must be at least 8 characters long.")
        
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            # Save user changes
            user.save()
            
            # Change password if provided
            if new_password1:
                user.set_password(new_password1)
                user.save()
                # Keep user logged in after password change
                from django.contrib.auth import update_session_auth_hash
                update_session_auth_hash(request, user)
            
            messages.success(request, "Your profile has been updated successfully!")
            return redirect("profile")
    
    return render(request, "grocery_store_app/edit_profile.html", {"user": request.user})

# Order Detail View
@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    items = order.items.all()  # using related_name='items'
    
    def rounded(value):
        return value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    subtotal = sum(item.subtotal() for item in items)
    subtotal = rounded(subtotal)
    gst = rounded(subtotal * Decimal('0.10'))
    total = rounded(subtotal + gst)

    return render(request, 'grocery_store_app/order_detail.html', {
        'order': order,
        'items': items,
        'subtotal': subtotal,
        'gst': gst,
        'total': total
    })
