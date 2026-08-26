from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from .models import Coupon
from blinkitapps.cart.models import Cart


def _get_cart(request):
    if request.user.is_authenticated:
        return Cart.objects.filter(user=request.user).first()
    elif request.session.session_key:
        return Cart.objects.filter(session_id=request.session.session_key).first()
    return None


def apply_coupon_view(request):
    """
    Validates and applies promo coupon code to current cart.
    """
    if request.method == "POST":
        code = request.POST.get('code', '').strip().upper()
        cart = _get_cart(request)

        if not cart or cart.item_count == 0:
            messages.warning(request, "Your cart is empty. Add items before applying a coupon.")
            return redirect(request.META.get('HTTP_REFERER', 'cart:detail'))

        if not code:
            messages.warning(request, "Please enter a coupon code.")
            return redirect(request.META.get('HTTP_REFERER', 'cart:detail'))

        try:
            coupon = Coupon.objects.get(code__iexact=code)
        except Coupon.DoesNotExist:
            messages.error(request, f"Coupon code '{code}' is invalid or does not exist.")
            return redirect(request.META.get('HTTP_REFERER', 'cart:detail'))

        is_valid, msg = coupon.is_valid_for_cart(cart.items_subtotal)
        if not is_valid:
            messages.error(request, f"Cannot apply '{code}': {msg}")
            return redirect(request.META.get('HTTP_REFERER', 'cart:detail'))

        cart.coupon = coupon
        cart.save()
        discount = cart.coupon_discount
        messages.success(request, f"Coupon '{coupon.code}' applied! You saved ₹{discount:.0f} on this order.")

        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
            return JsonResponse({
                'status': 'success',
                'code': coupon.code,
                'discount': float(discount),
                'grand_total': float(cart.grand_total),
                'message': f"Coupon '{coupon.code}' applied!",
            })

    return redirect(request.META.get('HTTP_REFERER', 'cart:detail'))


def remove_coupon_view(request):
    """
    Removes applied coupon code from cart.
    """
    if request.method == "POST":
        cart = _get_cart(request)
        if cart and cart.coupon:
            removed_code = cart.coupon.code
            cart.coupon = None
            cart.save()
            messages.info(request, f"Coupon '{removed_code}' removed from your cart.")

    return redirect(request.META.get('HTTP_REFERER', 'cart:detail'))


def available_coupons_api(request):
    """
    Returns list of active eligible coupons.
    """
    now = timezone.now()
    coupons = Coupon.objects.filter(is_active=True, valid_from__lte=now, valid_until__gte=now)
    cart = _get_cart(request)
    cart_subtotal = cart.items_subtotal if cart else 0

    coupons_list = []
    for c in coupons:
        is_eligible = cart_subtotal >= c.min_order_amount
        coupons_list.append({
            'code': c.code,
            'description': c.description,
            'discount_type': c.discount_type,
            'discount_value': float(c.discount_value),
            'min_order_amount': float(c.min_order_amount),
            'is_eligible': is_eligible,
        })

    return JsonResponse({'status': 'success', 'coupons': coupons_list})
