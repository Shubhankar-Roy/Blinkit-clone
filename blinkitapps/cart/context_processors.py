from .models import Cart


def cart_processor(request):
    """
    Context processor providing current cart state, item count,
    subtotal, delivery fee, coupons, tipping, and grand total across all templates.
    """
    cart = None
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
    else:
        session_id = request.session.session_key
        if session_id:
            cart = Cart.objects.filter(session_id=session_id).first()

    return {
        'cart': cart,
        'cart_item_count': cart.item_count if cart else 0,
        'cart_total_price': cart.grand_total if cart else 0,
        'cart_items_subtotal': cart.items_subtotal if cart else 0,
        'cart_total_savings': cart.total_savings if cart else 0,
        'cart_coupon': cart.coupon if cart else None,
        'coupon_discount': cart.coupon_discount if cart else 0,
        'tip_amount': cart.tip_amount if cart else 0,
    }
