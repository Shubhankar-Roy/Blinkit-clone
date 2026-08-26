from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from decimal import Decimal
from blinkitapps.products.models import Product
from blinkitapps.darkstore.models import DarkStore, DarkStoreInventory
from blinkitapps.promotions.models import Coupon
from .models import Cart, CartItem


def _get_or_create_cart(request):
    """
    Retrieves or initializes the active cart for an authenticated user
    or guest session.
    """
    if not request.session.session_key:
        request.session.save()

    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
    else:
        cart, _ = Cart.objects.get_or_create(session_id=request.session.session_key)
    return cart


def _get_assigned_darkstore(request):
    """
    Retrieves the Dark Store serving the current user's location.
    """
    pincode = request.session.get('pincode', '560034')
    active_stores = DarkStore.objects.filter(is_active=True)
    for store in active_stores:
        if store.is_pincode_serviceable(pincode):
            return store
    return active_stores.first()


def update_cart(request):
    """
    Updates cart item quantities with real-time stock verification
    against the assigned Dark Store inventory.
    """
    if request.method == "POST":
        product_id = request.POST.get('product_id')
        action = request.POST.get('action', 'add')
        
        try:
            product = Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist:
            return HttpResponse("Product not found", status=404)
            
        cart = _get_or_create_cart(request)
        dark_store = _get_assigned_darkstore(request)

        # Check store inventory stock limits
        available_stock = 50
        if dark_store:
            inv = DarkStoreInventory.objects.filter(dark_store=dark_store, product=product).first()
            if inv:
                available_stock = inv.stock_quantity if inv.is_available else 0
            else:
                available_stock = 0

        # Global out of stock override
        if product.is_out_of_stock or not product.is_active:
            available_stock = 0

        cart_item = CartItem.objects.filter(cart=cart, product=product).first()

        if action == 'add':
            if available_stock <= 0:
                if cart_item:
                    cart_item.delete()
                messages.error(request, f"Sorry, '{product.name}' is currently out of stock at {dark_store.name if dark_store else 'your location'}.")
            elif cart_item is None:
                CartItem.objects.create(cart=cart, product=product, quantity=1)
                messages.success(request, f"Added '{product.name}' to your cart.")
            elif cart_item.quantity + 1 > available_stock:
                messages.warning(request, f"Cannot add more: Only {available_stock} unit(s) of '{product.name}' available in stock.")
            else:
                cart_item.quantity += 1
                cart_item.save()
                messages.success(request, f"Added '{product.name}' to your cart.")
        
        elif action == 'remove':
            if cart_item:
                if cart_item.quantity > 1:
                    cart_item.quantity -= 1
                    cart_item.save()
                    messages.info(request, f"Reduced quantity of '{product.name}'.")
                else:
                    cart_item.delete()
                    messages.info(request, f"Removed '{product.name}' from your cart.")
        
        elif action == 'delete':
            if cart_item:
                cart_item.delete()
                messages.info(request, f"Removed '{product.name}' from your cart.")

        # Revalidate applied coupon against new cart total
        if cart.coupon:
            is_valid, _ = cart.coupon.is_valid_for_cart(cart.items_subtotal)
            if not is_valid:
                removed_code = cart.coupon.code
                cart.coupon = None
                cart.save()
                messages.warning(request, f"Coupon '{removed_code}' was removed because the cart subtotal changed.")

        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
            current_qty = CartItem.objects.filter(cart=cart, product=product).values_list('quantity', flat=True).first() or 0
            return JsonResponse({
                'status': 'success',
                'in_cart_qty': current_qty,
                'cart_item_count': cart.item_count,
                'cart_items_subtotal': float(cart.items_subtotal),
                'coupon_discount': float(cart.coupon_discount),
                'cart_grand_total': float(cart.grand_total),
            })

    return redirect(request.META.get('HTTP_REFERER', 'cart:detail'))


def set_tip_view(request):
    """
    Sets delivery partner tip amount.
    """
    if request.method == "POST":
        tip = request.POST.get('tip', '0')
        try:
            tip_val = max(Decimal('0.00'), Decimal(str(tip)))
        except (ValueError, TypeError):
            tip_val = Decimal('0.00')

        cart = _get_or_create_cart(request)
        cart.tip_amount = tip_val
        cart.save()

        if tip_val > 0:
            messages.success(request, f"Thank you! ₹{tip_val:.0f} tip added for your delivery partner.")
        else:
            messages.info(request, "Tip removed.")

        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
            return JsonResponse({
                'status': 'success',
                'tip_amount': float(cart.tip_amount),
                'cart_grand_total': float(cart.grand_total),
            })

    return redirect(request.META.get('HTTP_REFERER', 'cart:detail'))


def cart_detail_view(request):
    """
    Shopping cart detail view with item-by-item stock checking,
    promotional coupons, and delivery partner tipping.
    """
    cart = _get_or_create_cart(request)
    dark_store = _get_assigned_darkstore(request)
    cart_items = cart.items.select_related('product', 'product__category').all()

    # Build inventory lookup map
    inventory_map = {}
    if dark_store:
        inventories = DarkStoreInventory.objects.filter(dark_store=dark_store, product__in=[item.product for item in cart_items])
        inventory_map = {inv.product_id: inv for inv in inventories}

    has_out_of_stock_items = False
    annotated_items = []

    for item in cart_items:
        p = item.product
        item_available_stock = 50
        is_oos = False

        if dark_store:
            inv = inventory_map.get(p.id)
            if inv:
                item_available_stock = inv.stock_quantity if inv.is_available else 0
            else:
                item_available_stock = 0

        if p.is_out_of_stock or not p.is_active or item_available_stock == 0:
            is_oos = True
            has_out_of_stock_items = True
        elif item.quantity > item_available_stock:
            item.stock_warning = f"Only {item_available_stock} units left in stock"

        item.is_store_out_of_stock = is_oos
        item.available_stock = item_available_stock
        annotated_items.append(item)

    # Active available coupons
    available_coupons = Coupon.objects.filter(is_active=True)

    return render(request, 'cart/cart_detail.html', {
        'cart': cart,
        'cart_items': annotated_items,
        'dark_store': dark_store,
        'has_out_of_stock_items': has_out_of_stock_items,
        'available_coupons': available_coupons,
    })


def clear_cart_view(request):
    """
    Empties the shopping cart.
    """
    if request.method == "POST":
        cart = _get_or_create_cart(request)
        cart.items.all().delete()
        cart.coupon = None
        cart.tip_amount = Decimal('0.00')
        cart.save()
        messages.success(request, "Cart cleared successfully.")
    return redirect(request.META.get('HTTP_REFERER', 'products:home'))