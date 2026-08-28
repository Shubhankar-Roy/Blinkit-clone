from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import uuid

from blinkitapps.accounts.models import Address
from blinkitapps.cart.models import Cart, CartItem
from blinkitapps.darkstore.models import DarkStore, DarkStoreInventory
from blinkitapps.promotions.models import Coupon
from blinkitapps.payment.models import Payment
from .models import Order, OrderItem
import razorpay


def _get_user_cart(request):
    if request.user.is_authenticated:
        return Cart.objects.filter(user=request.user).first()
    elif request.session.session_key:
        return Cart.objects.filter(session_id=request.session.session_key).first()
    return None


def _get_assigned_darkstore(request):
    pincode = request.session.get('pincode', '560034')
    active_stores = DarkStore.objects.filter(is_active=True)
    for store in active_stores:
        if store.is_pincode_serviceable(pincode):
            return store
    return active_stores.first()


@login_required(login_url='/accounts/login/')
def checkout_view(request):
    """
    Checkout controller handling address selection, stock validation,
    payment method selection (COD & Razorpay), and order generation.
    """
    cart = _get_user_cart(request)
    if not cart or cart.item_count == 0:
        messages.warning(request, "Your cart is empty. Please add items before checkout.")
        return redirect('products:home')

    dark_store = _get_assigned_darkstore(request)
    user_addresses = Address.objects.filter(user=request.user)

    # Pre-validate stock for all items
    if dark_store:
        inventories = DarkStoreInventory.objects.filter(dark_store=dark_store, product__in=[item.product for item in cart.items.all()])
        inv_map = {inv.product_id: inv for inv in inventories}
        for item in cart.items.all():
            inv = inv_map.get(item.product_id)
            available = inv.stock_quantity if (inv and inv.is_available) else 0
            if item.product.is_out_of_stock or not item.product.is_active or available == 0:
                messages.error(request, f"'{item.product.name}' is currently out of stock at {dark_store.name}. Please remove it to proceed.")
                return redirect('cart:detail')
            elif item.quantity > available:
                messages.warning(request, f"Only {available} units of '{item.product.name}' available in stock.")
                return redirect('cart:detail')

    if request.method == "POST":
        address_id = request.POST.get('address_id')
        new_street = request.POST.get('street_address', '').strip()
        new_city = request.POST.get('city', 'Bengaluru').strip()
        new_pincode = request.POST.get('pincode', request.session.get('pincode', '560034')).strip()
        new_landmark = request.POST.get('landmark', '').strip()
        phone = request.POST.get('phone', request.user.phone_number or '').strip()
        payment_method = request.POST.get('payment_method', 'COD')

        # Resolve delivery address
        if address_id and address_id != 'new':
            address_obj = Address.objects.filter(id=address_id, user=request.user).first()
            if address_obj:
                delivery_address_text = f"{address_obj.street_address}, {address_obj.city} - {address_obj.pincode}"
                if address_obj.landmark:
                    delivery_address_text += f" (Landmark: {address_obj.landmark})"
                delivery_pincode = address_obj.pincode
            else:
                messages.error(request, "Selected address could not be found.")
                return redirect('orders:checkout')
        else:
            if not new_street:
                messages.error(request, "Please provide a valid delivery address.")
                return redirect('orders:checkout')
            delivery_address_text = f"{new_street}, {new_city} - {new_pincode}"
            if new_landmark:
                delivery_address_text += f" (Landmark: {new_landmark})"
            delivery_pincode = new_pincode

            # Optionally save to address book
            if request.POST.get('save_address') == 'on':
                Address.objects.create(
                    user=request.user,
                    address_type=request.POST.get('address_type', 'Home'),
                    house_flat_no='Location',
                    area_street=new_street,
                    city=new_city,
                    pincode=new_pincode,
                    landmark=new_landmark,
                    is_default=(user_addresses.count() == 0)
                )

        if not phone:
            phone = request.user.phone_number or '9876543210'

        # Snapshot order record
        order = Order.objects.create(
            user=request.user,
            dark_store=dark_store,
            delivery_address=delivery_address_text,
            pincode=delivery_pincode,
            phone=phone,
            items_total=cart.items_subtotal,
            coupon_discount=cart.coupon_discount,
            delivery_fee=cart.delivery_fee,
            handling_fee=cart.handling_fee,
            tip_amount=cart.tip_amount,
            grand_total=cart.grand_total,
            payment_method=payment_method,
            payment_status='SUCCESS' if payment_method == 'COD' else 'PENDING',
            eta_minutes=dark_store.avg_delivery_mins if dark_store else 10,
            status='PLACED',
            darkstore_lat=12.9352,
            darkstore_lng=77.6245,
            dest_lat=12.9390,
            dest_lng=77.6290,
        )

        # Snapshot order items & decrement store inventory
        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                product_name=item.product.name,
                unit_quantity=item.product.unit_quantity,
                price=item.product.selling_price,
                quantity=item.quantity,
                subtotal=item.subtotal
            )

            # Decrement dark store inventory
            if dark_store:
                inv = DarkStoreInventory.objects.filter(dark_store=dark_store, product=item.product).first()
                if inv:
                    inv.stock_quantity = max(0, inv.stock_quantity - item.quantity)
                    if inv.stock_quantity == 0:
                        inv.is_available = False
                    inv.save()

        # Update coupon redemption count
        if cart.coupon:
            cart.coupon.times_used += 1
            cart.coupon.save()

        # Clear active cart
        cart.items.all().delete()
        cart.coupon = None
        cart.tip_amount = Decimal('0.00')
        cart.save()

        # Route according to payment method
        if payment_method == 'RAZORPAY':
            razorpay_key = getattr(settings, 'RAZOR_KEY_ID', getattr(settings, 'RAZORPAY_KEY_ID', 'rzp_test_TUqVvgf1HYHy0o'))
            razorpay_secret = getattr(settings, 'RAZOR_KEY_SECRET', getattr(settings, 'RAZORPAY_KEY_SECRET', 'kmQ1hgcEvRaL6k6ZZ4Dw8MG3'))
            amount_in_paise = int(order.grand_total * 100)

            try:
                client = razorpay.Client(auth=(razorpay_key, razorpay_secret))
                rzp_order = client.order.create(
                    dict(
                        amount=amount_in_paise,
                        currency='INR',
                        receipt=str(order.order_number),
                        payment_capture='0',
                        notes={'order_number': order.order_number}
                    )
                )
                razorpay_order_id = rzp_order['id']
            except Exception:
                razorpay_order_id = f"order_{uuid.uuid4().hex[:14]}"

            order.razorpay_order_id = razorpay_order_id
            order.save(update_fields=['razorpay_order_id'])

            Payment.objects.create(
                razorpay_order_id=razorpay_order_id,
                amount=amount_in_paise,
                status='Created'
            )

            return render(request, 'payments/razorpay_pay.html', {
                'order': order,
                'razorpay_order_id': razorpay_order_id,
                'razorpay_merchant_key': razorpay_key,
                'razorpay_key_id': razorpay_key,
                'amount_in_paise': amount_in_paise,
                'currency': 'INR',
                'callback_url': '/paymenthandler/',
                'user_name': request.user.display_name if request.user.is_authenticated else 'Customer',
                'user_email': request.user.email if request.user.is_authenticated and request.user.email else 'customer@blinkitclone.local',
                'user_phone': phone,
            })

        messages.success(request, f"Order #{order.order_number} placed successfully! Arriving in {order.eta_minutes} mins.")
        return redirect('orders:track', order_number=order.order_number)

    return render(request, 'orders/checkout.html', {
        'cart': cart,
        'dark_store': dark_store,
        'user_addresses': user_addresses,
        'default_address': user_addresses.filter(is_default=True).first() or user_addresses.first(),
    })


@csrf_exempt
def razorpay_payment_verify(request):
    """
    Simulates or verifies Razorpay payment completion callback.
    """
    if request.method == "POST":
        order_number = request.POST.get('order_number')
        payment_id = request.POST.get('razorpay_payment_id', f"pay_{uuid.uuid4().hex[:14]}")
        payment_status = request.POST.get('payment_status', 'SUCCESS')

        order = get_object_or_404(Order, order_number=order_number)

        if payment_status == 'SUCCESS':
            order.payment_status = 'SUCCESS'
            order.razorpay_payment_id = payment_id
            order.save()
            messages.success(request, f"Payment received! Order #{order.order_number} is being packed.")
            return redirect('orders:track', order_number=order.order_number)
        else:
            order.payment_status = 'FAILED'
            order.save()
            messages.error(request, "Payment failed or cancelled. Please retry payment.")
            return redirect('orders:checkout')

    return redirect('products:home')


def order_tracking_view(request, order_number):
    """
    Live visual order tracking screen with multi-step progress bar,
    Dark Store dispatch details, rider information, real-time Leaflet.js map, and itemized invoice.
    """
    order = get_object_or_404(Order.objects.prefetch_related('items', 'items__product'), order_number=order_number)
    
    return render(request, 'orders/order_tracking.html', {
        'order': order,
        'items': order.items.all(),
    })


def order_status_api(request, order_number):
    """
    JSON API for live polling of order status changes.
    """
    order = get_object_or_404(Order, order_number=order_number)
    return JsonResponse({
        'status': 'success',
        'order_number': order.order_number,
        'order_status': order.status,
        'status_display': order.get_status_display(),
        'tracking_step': order.tracking_step,
        'eta_minutes': order.eta_minutes,
        'payment_status': order.payment_status,
    })


def rider_location_api(request, order_number):
    """
    Phase 7: Real-Time Delivery Rider GPS Tracking & Coordinate Interpolation API.
    Smoothly moves rider coordinates along the route from Dark Store to Customer address.
    """
    order = get_object_or_404(Order, order_number=order_number)
    now = timezone.now()
    elapsed_seconds = (now - order.created_at).total_seconds()
    
    # 120-second simulation cycle
    progress = min(1.0, max(0.0, elapsed_seconds / 120.0))
    
    # Interpolate current rider latitude and longitude
    if progress < 0.30:
        curr_lat, curr_lng = order.darkstore_lat, order.darkstore_lng
    elif progress >= 0.98:
        curr_lat, curr_lng = order.dest_lat, order.dest_lng
    else:
        ratio = (progress - 0.30) / 0.68
        curr_lat = order.darkstore_lat + (order.dest_lat - order.darkstore_lat) * ratio
        curr_lng = order.darkstore_lng + (order.dest_lng - order.darkstore_lng) * ratio

    return JsonResponse({
        'status': 'success',
        'order_number': order.order_number,
        'order_status': order.status,
        'status_display': order.get_status_display(),
        'eta_minutes': max(0, int((1.0 - progress) * (order.eta_minutes or 10))),
        'rider_coords': [round(curr_lat, 6), round(curr_lng, 6)],
        'darkstore_coords': [order.darkstore_lat, order.darkstore_lng],
        'dest_coords': [order.dest_lat, order.dest_lng],
        'rider': {
            'name': order.rider_name,
            'phone': order.rider_phone,
            'rating': float(order.rider_rating),
            'vehicle': order.vehicle_number
        }
    })


def order_invoice_view(request, order_number):
    """
    Renders official printable GST Tax Invoice for the customer order.
    """
    order = get_object_or_404(Order.objects.prefetch_related('items', 'items__product'), order_number=order_number)
    
    # Access check: user must own order or be admin/staff
    if request.user.is_authenticated and (order.user == request.user or request.user.is_staff):
        pass
    elif not request.user.is_authenticated and not order.user:
        pass
    else:
        messages.error(request, "Access denied.")
        return redirect('orders:history')

    return render(request, 'orders/order_invoice.html', {
        'order': order,
        'items': order.items.all(),
    })


@login_required(login_url='/accounts/login/')
def cancel_order_view(request, order_number):
    """
    Allows user or admin to cancel an order if it is in PLACED stage,
    restoring inventory back to the Dark Store.
    """
    order = get_object_or_404(Order, order_number=order_number)
    if order.user != request.user and not request.user.is_staff:
        messages.error(request, "Access denied.")
        return redirect('orders:history')

    if order.status == 'PLACED':
        order.status = 'CANCELLED'
        order.save()

        # Restock inventory
        if order.dark_store:
            for item in order.items.all():
                if item.product:
                    inv = DarkStoreInventory.objects.filter(dark_store=order.dark_store, product=item.product).first()
                    if inv:
                        inv.stock_quantity += item.quantity
                        inv.is_available = True
                        inv.save()

        messages.info(request, f"Order #{order.order_number} has been cancelled successfully.")
    else:
        messages.warning(request, "Cannot cancel: order has already been packed and dispatched for delivery.")

    return redirect('orders:track', order_number=order.order_number)


@login_required(login_url='/accounts/login/')
def order_history_view(request):
    """
    Displays historical orders placed by the customer.
    """
    orders = Order.objects.filter(user=request.user).prefetch_related('items').order_by('-created_at')
    
    return render(request, 'orders/order_history.html', {
        'orders': orders,
    })


@login_required(login_url='/accounts/login/')
def reorder_view(request, order_number):
    """
    1-click Re-order: Adds all available items from a past order to customer's active cart.
    """
    past_order = get_object_or_404(Order, order_number=order_number, user=request.user)
    cart = _get_user_cart(request)
    if not cart:
        cart = Cart.objects.create(user=request.user)

    items_added = 0
    for order_item in past_order.items.all():
        if order_item.product and order_item.product.is_active and not order_item.product.is_out_of_stock:
            cart_item, created = CartItem.objects.get_or_create(cart=cart, product=order_item.product)
            if not created:
                cart_item.quantity += order_item.quantity
            else:
                cart_item.quantity = order_item.quantity
            cart_item.save()
            items_added += 1

    if items_added > 0:
        messages.success(request, f"Added items from Order #{past_order.order_number} to your cart.")
        return redirect('cart:detail')
    else:
        messages.warning(request, "Could not reorder items: products are currently unavailable.")
        return redirect('orders:history')
