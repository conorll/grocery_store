from django.shortcuts import render, redirect, get_object_or_404
from grocery_store_app.models import Category
from .models import Product
from .models import Cart, CartEntry
from .models import Store
from .models import PerStoreProduct
from .models import Address
from .models import Payment
from .models.order import Order
from .models import CustomUser
from .forms import PostcodeForm, CustomUserCreationForm, CustomStaffCreationForm
from .utils import geocode_postcode, haversine, apply_product_filters
from django.http import HttpResponse, JsonResponse
from .services import create_order_from_cart
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login
from django.db.models import Q
from django.core.paginator import Paginator
from urllib.parse import urlencode
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from django.utils import timezone

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

    per_store_products = PerStoreProduct.objects.filter(product_id=id)

    store_objects = Store.objects.all()

    store_quantities = {}

    for per_store_product in per_store_products:
        store_quantities[per_store_product.store_id] = per_store_product.quantity

    stores = []

    for store in store_objects:
        stores.append(
            {
                "id": store.id,
                "name": store.name,
                "quantity": store_quantities.get(store.id, -1),
            }
        )

    selected_store = None

    selected_store_id = request.session.get("selected_store_id")
    if selected_store_id:
        store = Store.objects.filter(id=selected_store_id).first()
        selected_store = {
            "id": store.id,
            "name": store.name,
            "quantity": store_quantities.get(store.id, -1),
        }

    return render(
        request,
        "grocery_store_app/product.html",
        {"product": product_object, "stores": stores, "selected_store": selected_store},
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
        address = Address.objects.create(
            user=request.user,
            first_name=first_name,
            last_name=last_name,
            address=form_address,
            address2=form_address2,
            suburb=suburb,
            postcode=postcode,
        )

        return redirect("checkout_payment")

    return render(request, "grocery_store_app/checkout_address.html")


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
        payment = Payment.objects.create(
            user=request.user,
            card_number=card_number,
            expiration_month=expiration_month,
            expiration_year=expiration_year,
            cvc=cvc,
        )

        # After saving the payment, create the order and order items:
        order = create_order_from_cart(request.user)

        if not order:
            messages.error(
                request, "Something went wrong creating your order. Please try again."
            )
            return redirect("cart")

        return redirect("confirm")

    return render(request, "grocery_store_app/checkout_payment.html")


def confirm(request):
    return render(request, "grocery_store_app/confirm.html")


def update_cart(cart, per_store_product, quantity):
    if quantity < 0:
        raise Exception(f"Purchase quantity cannot be negative")

    if quantity > per_store_product.quantity:
        raise Exception(
            f"Purchase quantity must be less than or equal to the available quantity: {per_store_product.quantity}"
        )

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
        cart=cart, per_store_product=per_store_product, defaults={"quantity": quantity}
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

        per_store_product = get_object_or_404(
            PerStoreProduct, product_id=product_id, store_id=store_id
        )

        entry, _ = CartEntry.objects.get_or_create(
            cart=cart, per_store_product=per_store_product, defaults={"quantity": 0}
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

        per_store_product = get_object_or_404(
            PerStoreProduct, product_id=product_id, store_id=store_id
        )

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
        entry_list.append(
            {
                "per_store_product": entry.per_store_product,
                "quantity": entry.quantity,
                "item_total": item_total,
            }
        )

    return render(
        request,
        "grocery_store_app/cart.html",
        {"cart": entry_list, "cart_total": cart_total},
    )


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


# Product listing with multi-filtering, sorting, pagination, persistence, perf timing
def products(request):
    # Clear / restore saved filters
    if request.GET.get("clear") == "1":
        request.session.pop("products_filters", None)
        return redirect("products")
    if request.method == "GET" and not request.GET:
        saved = request.session.get("products_filters")
        if saved:
            request.GET = request.GET.copy()
            for k, v in saved.items():
                request.GET[k] = v

    t0 = timezone.now()

    # Base queryset (avoid N+1 on category)
    qs = Product.objects.select_related("category").all()

    # Work on a mutable copy and NORMALIZE price names
    params = request.GET.copy()
    if "min_price" in params and "price_min" not in params:
        params["price_min"] = params["min_price"]
    if "max_price" in params and "price_max" not in params:
        params["price_max"] = params["max_price"]

    # Apply filters using the NORMALIZED params
    # (If your helper accepts selected_store_id, pass it too)
    try:
        selected_store_id = request.session.get("selected_store_id")
        qs = apply_product_filters(qs, params, selected_store_id=selected_store_id)
    except TypeError:
        qs = apply_product_filters(qs, params)

    # Sorting (add newest/oldest)
    sort = (params.get("sort") or "").strip()
    sort_map = {
        "price_asc": "price",
        "price_desc": "-price",
        "name_asc": "name",
        "name_desc": "-name",
        "newest": "-id",
        "oldest": "id",
        "id": "id",  # default
    }
    sort_key = sort if sort in sort_map else "id"
    qs = qs.order_by(sort_map[sort_key])

    # Pagination
    per_page_raw = params.get("per_page") or "12"
    try:
        per_page_int = max(1, min(60, int(per_page_raw)))
    except ValueError:
        per_page_int = 12
    paginator = Paginator(qs, per_page_int)
    page_obj = paginator.get_page(params.get("page"))

    # Build querystring (exclude 'page')
    params_for_links = params.dict()
    params_for_links.pop("page", None)
    querystring = urlencode(params_for_links)

    # Persist current filters
    request.session["products_filters"] = {k: v for k, v in params.items()}

    elapsed_ms = int((timezone.now() - t0).total_seconds() * 1000)

    return render(
        request,
        "grocery_store_app/products.html",
        {
            "products": page_obj,
            "page_obj": page_obj,
            "paginator": paginator,
            # UI state (use normalized params so fields reflect what user typed)
            "query": (params.get("q") or ""),
            "min_price": params.get("min_price") or params.get("price_min") or "",
            "max_price": params.get("max_price") or params.get("price_max") or "",
            "sort": sort_key,
            "per_page": per_page_int,
            "querystring": querystring,
            "per_page_options": [12, 24, 36, 48, 60],
            # Extras for filters & chips
            "categories": Category.objects.all(),
            "selected_category": params.get("category") or "",
            "in_stock": params.get("in_stock") == "1",
            "elapsed_ms": elapsed_ms,
        },
    )


# ---------- JSON API (reuses the same filter helper) ----------
def products_api(request):
    qs = Product.objects.select_related("category").all()

    # Normalize here too, so API accepts both min_price/max_price and price_min/price_max
    params = request.GET.copy()
    if "min_price" in params and "price_min" not in params:
        params["price_min"] = params["min_price"]
    if "max_price" in params and "price_max" not in params:
        params["price_max"] = params["max_price"]

    try:
        selected_store_id = request.session.get("selected_store_id")
        qs = apply_product_filters(qs, params, selected_store_id=selected_store_id)
    except TypeError:
        qs = apply_product_filters(qs, params)

    qs = qs.order_by("name")
    data = list(qs.values("id", "name", "price", "category__name"))
    return JsonResponse({"count": len(data), "results": data}, status=200)


# ---------- JSON API (reuses the same filter helper for reusability) ----------
def products_api(request):
    qs = Product.objects.select_related("category").all()
    qs = apply_product_filters(qs, request.GET).order_by("name")
    data = list(
        qs.values(
            "id",
            "name",
            "price",
            "category__name",
        )
    )
    return JsonResponse({"count": len(data), "results": data}, status=200)


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


# Profile View
@login_required
def profile(request):
    user = request.user
    active_orders = user.orders.filter(status="active")
    past_orders = user.orders.filter(status="completed").order_by("-created_at")[:5]

    return render(
        request,
        "grocery_store_app/profile.html",
        {
            "user": user,
            "active_orders": active_orders,
            "past_orders": past_orders,
        },
    )


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
            elif new_password1 and len(new_password1) < 8:
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

    return render(
        request, "grocery_store_app/edit_profile.html", {"user": request.user}
    )


# Order Detail View
@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    # Handle order cancellation
    if request.method == "POST" and request.POST.get("action") == "cancel_order":
        if order.status == "Active":
            order.status = "Cancelled"
            order.save()
            messages.success(
                request, f"Order #{order.id} has been cancelled successfully."
            )
        else:
            messages.error(request, "Only active orders can be cancelled.")
        return redirect("order_detail", order_id=order.id)

    items = order.items.all()  # using related_name='items'

    def rounded(value):
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    subtotal = sum(item.subtotal() for item in items)
    subtotal = rounded(subtotal)
    gst = rounded(subtotal * Decimal("0.10"))
    total = rounded(subtotal + gst)

    return render(
        request,
        "grocery_store_app/order_detail.html",
        {
            "order": order,
            "items": items,
            "subtotal": subtotal,
            "gst": gst,
            "total": total,
        },
    )


# Payment Management Views
@login_required
def add_payment_method(request):
    if request.method == "POST":
        card_number = request.POST.get("card_number")
        expiration_month = request.POST.get("expiration_month")
        expiration_year = request.POST.get("expiration_year")
        cvc = request.POST.get("cvc")

        errors = []

        # Basic validation
        if not card_number or len(card_number) != 16 or not card_number.isdigit():
            errors.append("Card number must be 16 digits.")

        if (
            not expiration_month
            or int(expiration_month) < 1
            or int(expiration_month) > 12
        ):
            errors.append("Please select a valid expiration month.")

        if not expiration_year or int(expiration_year) < 2024:
            errors.append("Please select a valid expiration year.")

        if not cvc or len(cvc) != 3 or not cvc.isdigit():
            errors.append("CVC must be 3 digits.")

        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            # Remove existing payment method if exists
            Payment.objects.filter(user=request.user).delete()

            # Create new payment method
            Payment.objects.create(
                user=request.user,
                card_number=int(card_number),
                expiration_month=int(expiration_month),
                expiration_year=int(expiration_year),
                cvc=int(cvc),
            )

            messages.success(request, "Payment method added successfully!")
            return redirect("profile")

    return render(request, "grocery_store_app/add_payment.html")


@login_required
def edit_payment_method(request):
    try:
        payment = Payment.objects.get(user=request.user)
    except Payment.DoesNotExist:
        messages.error(request, "No payment method found.")
        return redirect("profile")

    if request.method == "POST":
        card_number = request.POST.get("card_number")
        expiration_month = request.POST.get("expiration_month")
        expiration_year = request.POST.get("expiration_year")
        cvc = request.POST.get("cvc")

        errors = []

        # Basic validation
        if not card_number or len(card_number) != 16 or not card_number.isdigit():
            errors.append("Card number must be 16 digits.")

        if (
            not expiration_month
            or int(expiration_month) < 1
            or int(expiration_month) > 12
        ):
            errors.append("Please select a valid expiration month.")

        if not expiration_year or int(expiration_year) < 2024:
            errors.append("Please select a valid expiration year.")

        if not cvc or len(cvc) != 3 or not cvc.isdigit():
            errors.append("CVC must be 3 digits.")

        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            # Update payment method
            payment.card_number = int(card_number)
            payment.expiration_month = int(expiration_month)
            payment.expiration_year = int(expiration_year)
            payment.cvc = int(cvc)
            payment.save()

            messages.success(request, "Payment method updated successfully!")
            return redirect("profile")

    return render(request, "grocery_store_app/edit_payment.html", {"payment": payment})


@login_required
def remove_payment_method(request):
    if request.method == "POST":
        Payment.objects.filter(user=request.user).delete()
        messages.success(request, "Payment method removed successfully!")

    return redirect("profile")


# Admin Dashboard Views
@login_required
def admin_dashboard(request):
    # Check if user has admin privileges
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect("profile")

    # Get all users for management and dropdown
    users = CustomUser.objects.all().order_by("-date_joined")
    all_users_for_dropdown = CustomUser.objects.all().order_by("username")

    # Get all orders for status management
    orders = Order.objects.all().order_by("-created_at")

    # Handle user selection for order filtering
    selected_user = None
    user_orders = []
    selected_user_id = request.GET.get("user_id")

    if selected_user_id:
        try:
            selected_user = CustomUser.objects.get(id=selected_user_id)
            user_orders = Order.objects.filter(user=selected_user).order_by(
                "-created_at"
            )
        except CustomUser.DoesNotExist:
            messages.error(request, "Selected user not found.")

    # Handle user management actions
    if request.method == "POST":
        action = request.POST.get("action")

        if action == "create_admin":
            username = request.POST.get("username")
            email = request.POST.get("email")
            password = request.POST.get("password")
            is_staff = request.POST.get("is_staff") == "on"
            is_superuser = request.POST.get("is_superuser") == "on"

            if username and email and password:
                if CustomUser.objects.filter(username=username).exists():
                    messages.error(request, "Username already exists.")
                elif CustomUser.objects.filter(email=email).exists():
                    messages.error(request, "Email already exists.")
                else:
                    user = CustomUser.objects.create_user(
                        username=username,
                        email=email,
                        password=password,
                        is_staff=is_staff,
                        is_superuser=is_superuser,
                    )

                    # Determine account type for message
                    if is_superuser:
                        account_type = "Super Administrator"
                    elif is_staff:
                        account_type = "Staff"
                    else:
                        account_type = "User"

                    messages.success(
                        request,
                        f"{account_type} account '{username}' created successfully!",
                    )
            else:
                messages.error(request, "All fields are required for account creation.")

        elif action == "toggle_user_status":
            user_id = request.POST.get("user_id")
            try:
                user = CustomUser.objects.get(id=user_id)
                user.is_active = not user.is_active
                user.save()
                status = "activated" if user.is_active else "deactivated"
                messages.success(request, f"User '{user.username}' has been {status}.")
            except CustomUser.DoesNotExist:
                messages.error(request, "User not found.")

        elif action == "make_staff":
            user_id = request.POST.get("user_id")
            try:
                user = CustomUser.objects.get(id=user_id)
                user.is_staff = not user.is_staff
                user.save()
                status = "granted" if user.is_staff else "revoked"
                messages.success(
                    request, f"Staff privileges {status} for '{user.username}'."
                )
            except CustomUser.DoesNotExist:
                messages.error(request, "User not found.")

        elif action == "update_order_status":
            order_id = request.POST.get("order_id")
            new_status = request.POST.get("new_status")
            try:
                order = Order.objects.get(id=order_id)
                order.status = new_status
                order.save()
                messages.success(
                    request, f"Order #{order.id} status updated to '{new_status}'."
                )

                # Redirect back to the same user selection if one was selected
                if selected_user_id:
                    return redirect(f"{request.path}?user_id={selected_user_id}")

            except Order.DoesNotExist:
                messages.error(request, "Order not found.")

        return redirect("admin_dashboard")

    context = {
        "users": users,
        "orders": orders,
        "all_users_for_dropdown": all_users_for_dropdown,
        "selected_user": selected_user,
        "user_orders": user_orders,
        "total_users": users.count(),
        "active_users": users.filter(is_active=True).count(),
        "total_orders": orders.count(),
        "pending_orders": orders.filter(status="active").count(),
    }

    return render(request, "grocery_store_app/admin_dashboard.html", context)
