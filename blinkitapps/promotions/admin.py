from django.contrib import admin
from .models import Coupon


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = (
        'code', 'description', 'discount_type', 'discount_value',
        'min_order_amount', 'max_discount_amount', 'valid_until',
        'is_active', 'times_used', 'usage_limit'
    )
    list_editable = ('is_active', 'discount_value', 'min_order_amount')
    list_filter = ('discount_type', 'is_active', 'valid_until')
    search_fields = ('code', 'description')
