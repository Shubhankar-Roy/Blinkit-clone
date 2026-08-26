from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, Count, Q
from decimal import Decimal

from blinkitapps.darkstore.models import DarkStore, DarkStoreInventory
from .models import Order, OrderItem


def admin_or_staff_required(view_func):
    """
    Decorator restricting access to staff or superuser administrators.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, "Please log in with Administrator credentials to access the Order Manager.")
            return redirect(f"/accounts/login/?next={request.path}")
        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, "Access Denied: Administrator privileges required.")
            return redirect('/accounts/login/?next=/dashboard/darkstore/')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


@admin_or_staff_required
def admin_orders_list(request):
    """
    Real-time Live Order Dispatch Queue and Order Management Dashboard.
    """
    status_filter = request.GET.get('status', 'ALL')
    store_filter = request.GET.get('store', 'ALL')
    payment_filter = request.GET.get('payment', 'ALL')
    search_query = request.GET.get('q', '').strip()

    orders = Order.objects.select_related('user', 'dark_store').prefetch_related('items').order_by('-created_at')

    if status_filter != 'ALL':
        orders = orders.filter(status=status_filter)
    if store_filter != 'ALL':
        orders = orders.filter(dark_store_id=store_filter)
    if payment_filter != 'ALL':
        orders = orders.filter(payment_status=payment_filter)
    if search_query:
        orders = orders.filter(
            Q(order_number__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(delivery_address__icontains=search_query) |
            Q(user__username__icontains=search_query)
        )

    # Metrics
    all_orders = Order.objects.all()
    total_orders_count = all_orders.count()
    placed_count = all_orders.filter(status='PLACED').count()
    packing_count = all_orders.filter(status='PACKING').count()
    out_for_delivery_count = all_orders.filter(status='OUT_FOR_DELIVERY').count()
    delivered_count = all_orders.filter(status='DELIVERED').count()
    total_revenue = all_orders.filter(payment_status='SUCCESS').aggregate(total=Sum('grand_total'))['total'] or Decimal('0.00')

    dark_stores = DarkStore.objects.filter(is_active=True)

    return render(request, 'admin_custom/orders/order_list.html', {
        'orders': orders,
        'total_orders_count': total_orders_count,
        'placed_count': placed_count,
        'packing_count': packing_count,
        'out_for_delivery_count': out_for_delivery_count,
        'delivered_count': delivered_count,
        'total_revenue': total_revenue,
        'dark_stores': dark_stores,
        'status_filter': status_filter,
        'store_filter': store_filter,
        'payment_filter': payment_filter,
        'search_query': search_query,
        'active_tab': 'orders_dispatch',
    })


@admin_or_staff_required
def admin_order_detail(request, order_number):
    """
    Detailed Order Inspector with customer information, assigned dark store, and item list.
    """
    order = get_object_or_404(Order.objects.select_related('user', 'dark_store').prefetch_related('items', 'items__product'), order_number=order_number)
    
    return render(request, 'admin_custom/orders/order_detail.html', {
        'order': order,
        'items': order.items.all(),
        'active_tab': 'orders_dispatch',
    })


@admin_or_staff_required
def admin_order_update_status(request, order_number):
    """
    Advances or updates an order's lifecycle stage:
    PLACED -> PACKING -> OUT_FOR_DELIVERY -> DELIVERED (or CANCELLED).
    If cancelled, returns items to Dark Store inventory.
    """
    if request.method == "POST":
        order = get_object_or_404(Order, order_number=order_number)
        new_status = request.POST.get('status')

        valid_statuses = dict(Order.STATUS_CHOICES).keys()
        if new_status in valid_statuses:
            old_status = order.status

            # If cancelling an active order, replenish warehouse stock
            if new_status == 'CANCELLED' and old_status != 'CANCELLED':
                if order.dark_store:
                    for item in order.items.all():
                        if item.product:
                            inv = DarkStoreInventory.objects.filter(dark_store=order.dark_store, product=item.product).first()
                            if inv:
                                inv.stock_quantity += item.quantity
                                inv.is_available = True
                                inv.save()

            order.status = new_status
            if new_status == 'DELIVERED' and order.payment_method == 'COD':
                order.payment_status = 'SUCCESS'

            order.save()
            messages.success(request, f"Order #{order.order_number} status updated to '{order.get_status_display()}'.")
        else:
            messages.error(request, "Invalid status choice selected.")

    return redirect(request.META.get('HTTP_REFERER', 'orders_admin:list'))
