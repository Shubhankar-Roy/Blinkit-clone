from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product_name', 'unit_quantity', 'price', 'quantity', 'subtotal')
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_number', 'user', 'phone', 'dark_store',
        'grand_total', 'payment_method', 'payment_status', 'status', 'created_at'
    )
    list_editable = ('status', 'payment_status')
    list_filter = ('status', 'payment_method', 'payment_status', 'dark_store', 'created_at')
    search_fields = ('order_number', 'phone', 'pincode', 'delivery_address')
    readonly_fields = ('order_number', 'created_at', 'updated_at', 'items_total', 'grand_total')
    inlines = [OrderItemInline]
