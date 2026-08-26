from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from .models import Coupon


def admin_or_staff_required(view_func):
    """
    Decorator restricting access to staff or superuser administrators.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, "Please log in with Administrator credentials to access the Coupon Manager.")
            return redirect(f"/accounts/login/?next={request.path}")
        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, "Access Denied: Administrator privileges required.")
            return redirect('/accounts/login/?next=/dashboard/darkstore/')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


@admin_or_staff_required
def admin_coupons_list(request):
    """
    Overview list of all promotional coupons with usage statistics and status toggles.
    """
    coupons = Coupon.objects.all().order_by('-created_at')
    now = timezone.now()

    total_coupons = coupons.count()
    active_coupons = coupons.filter(is_active=True, valid_until__gte=now).count()
    expired_coupons = coupons.filter(valid_until__lt=now).count()
    total_redemptions = sum(c.times_used for c in coupons)

    return render(request, 'admin_custom/promotions/coupon_list.html', {
        'coupons': coupons,
        'total_coupons': total_coupons,
        'active_coupons': active_coupons,
        'expired_coupons': expired_coupons,
        'total_redemptions': total_redemptions,
        'active_tab': 'promotions_coupons',
    })


@admin_or_staff_required
def admin_coupon_create(request):
    """
    Create a new promotional coupon code.
    """
    if request.method == "POST":
        code = request.POST.get('code', '').strip().upper()
        description = request.POST.get('description', '').strip()
        discount_type = request.POST.get('discount_type', 'FLAT')
        discount_value = Decimal(str(request.POST.get('discount_value', 0)))
        min_order_amount = Decimal(str(request.POST.get('min_order_amount', 0)))
        
        max_cap_str = request.POST.get('max_discount_amount', '').strip()
        max_discount_amount = Decimal(max_cap_str) if max_cap_str else None

        valid_days = int(request.POST.get('valid_days', 30))
        valid_from = timezone.now()
        valid_until = valid_from + timedelta(days=valid_days)
        usage_limit = int(request.POST.get('usage_limit', 1000))
        is_active = request.POST.get('is_active') == 'on'

        if not code or not description or discount_value <= 0:
            messages.error(request, "Code, Description, and Discount Value are required.")
            return render(request, 'admin_custom/promotions/coupon_form.html', {
                'form_action': 'create',
                'active_tab': 'promotions_coupons',
            })

        if Coupon.objects.filter(code=code).exists():
            messages.error(request, f"A coupon with code '{code}' already exists.")
            return render(request, 'admin_custom/promotions/coupon_form.html', {
                'form_action': 'create',
                'active_tab': 'promotions_coupons',
            })

        coupon = Coupon.objects.create(
            code=code,
            description=description,
            discount_type=discount_type,
            discount_value=discount_value,
            min_order_amount=min_order_amount,
            max_discount_amount=max_discount_amount,
            valid_from=valid_from,
            valid_until=valid_until,
            usage_limit=usage_limit,
            is_active=is_active,
        )

        messages.success(request, f"Coupon '{coupon.code}' created successfully!")
        return redirect('promotions_admin:list')

    return render(request, 'admin_custom/promotions/coupon_form.html', {
        'form_action': 'create',
        'active_tab': 'promotions_coupons',
    })


@admin_or_staff_required
def admin_coupon_edit(request, coupon_id):
    """
    Edit an existing promotional coupon code.
    """
    coupon = get_object_or_404(Coupon, id=coupon_id)

    if request.method == "POST":
        new_code = request.POST.get('code', '').strip().upper()
        if new_code != coupon.code and Coupon.objects.filter(code=new_code).exclude(id=coupon.id).exists():
            messages.error(request, f"A coupon with code '{new_code}' already exists.")
            return render(request, 'admin_custom/promotions/coupon_form.html', {
                'coupon': coupon,
                'form_action': 'edit',
                'active_tab': 'promotions_coupons',
            })

        coupon.code = new_code
        coupon.description = request.POST.get('description', '').strip()
        coupon.discount_type = request.POST.get('discount_type', 'FLAT')
        coupon.discount_value = Decimal(str(request.POST.get('discount_value', 0)))
        coupon.min_order_amount = Decimal(str(request.POST.get('min_order_amount', 0)))

        max_cap_str = request.POST.get('max_discount_amount', '').strip()
        coupon.max_discount_amount = Decimal(max_cap_str) if max_cap_str else None

        valid_days = int(request.POST.get('valid_days', 30))
        coupon.valid_until = coupon.valid_from + timedelta(days=valid_days)
        coupon.usage_limit = int(request.POST.get('usage_limit', 1000))
        coupon.is_active = request.POST.get('is_active') == 'on'

        coupon.save()
        messages.success(request, f"Coupon '{coupon.code}' updated successfully.")
        return redirect('promotions_admin:list')

    return render(request, 'admin_custom/promotions/coupon_form.html', {
        'coupon': coupon,
        'form_action': 'edit',
        'active_tab': 'promotions_coupons',
    })


@admin_or_staff_required
def admin_coupon_toggle(request, coupon_id):
    """
    1-click active/inactive toggle for a coupon code.
    """
    coupon = get_object_or_404(Coupon, id=coupon_id)
    coupon.is_active = not coupon.is_active
    coupon.save()
    status_str = "ACTIVE" if coupon.is_active else "INACTIVE"
    messages.success(request, f"Coupon '{coupon.code}' is now {status_str}.")
    return redirect(request.META.get('HTTP_REFERER', 'promotions_admin:list'))


@admin_or_staff_required
def admin_coupon_delete(request, coupon_id):
    """
    Deletes a coupon code.
    """
    if request.method == "POST":
        coupon = get_object_or_404(Coupon, id=coupon_id)
        code = coupon.code
        coupon.delete()
        messages.success(request, f"Coupon '{code}' has been deleted.")
    return redirect('promotions_admin:list')
