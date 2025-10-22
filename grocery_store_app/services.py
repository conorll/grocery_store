from .models import Order, OrderItem, Payment, Address, CartEntry, Cart
from decimal import Decimal

def create_order_from_cart(user):
    try:
        cart = Cart.objects.get(user=user)
        entries = cart.cart_entries.select_related("per_store_product", "per_store_product__product")
    except Cart.DoesNotExist:
        return None

    if not entries.exists():
        return None

    # Get user's address and payment
    try:
        address = Address.objects.get(user=user)
        payment = Payment.objects.get(user=user)
    except (Address.DoesNotExist, Payment.DoesNotExist):
        return None
    
    # Calculate total
    total = Decimal(0)
    for entry in entries:
        total += entry.quantity * entry.per_store_product.product.price

    # Create the order
    order = Order.objects.create(
        user=user,
        address=address,
        payment=payment,
        status='active',
        total=total,
    )

    # Create order items from cart entries
    for entry in entries:
        per_store_product = entry.per_store_product
        product = per_store_product.product

        # Reduce stock
        per_store_product.quantity -= entry.quantity
        per_store_product.save()

        # Create order item
        OrderItem.objects.create(
            order=order,
            product=product,
            per_store_product=per_store_product,
            quantity=entry.quantity,
            price=product.price  # assuming static price at time of order
        )

    # Clear the cart
    entries.delete()

    return order