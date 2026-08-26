from django.contrib import admin
from .models import DarkStore, DarkStoreInventory


class DarkStoreInventoryInline(admin.TabularInline):
    model = DarkStoreInventory
    extra = 0
    fields = ('product', 'stock_quantity', 'is_available', 'low_stock_threshold')
    autocomplete_fields = ('product',)
    show_change_link = True


@admin.register(DarkStore)
class DarkStoreAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'code', 'city', 'avg_delivery_mins',
        'is_active', 'pincode_count_display', 'total_stock_display', 'updated_at'
    )
    list_editable = ('is_active', 'avg_delivery_mins')
    list_filter = ('is_active', 'city', 'avg_delivery_mins')
    search_fields = ('name', 'code', 'address', 'serviceable_pincodes', 'city')
    inlines = [DarkStoreInventoryInline]
    actions = ['activate_stores', 'deactivate_stores']

    def pincode_count_display(self, obj):
        return f"{obj.pincode_count} Pincodes"
    pincode_count_display.short_description = "Coverage"

    def total_stock_display(self, obj):
        return f"{obj.total_stock_units} Units ({obj.total_inventory_items} SKUs)"
    total_stock_display.short_description = "Live Stock"

    def activate_stores(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f"{count} Dark Store(s) marked as ACTIVE.")
    activate_stores.short_description = "Mark selected stores as ACTIVE"

    def deactivate_stores(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f"{count} Dark Store(s) marked as INACTIVE (Closed).")
    deactivate_stores.short_description = "Mark selected stores as INACTIVE"


@admin.register(DarkStoreInventory)
class DarkStoreInventoryAdmin(admin.ModelAdmin):
    list_display = (
        'dark_store', 'product', 'stock_quantity',
        'is_available', 'is_low_stock_display', 'last_restocked_at'
    )
    list_editable = ('stock_quantity', 'is_available')
    list_filter = ('dark_store', 'is_available', 'product__category')
    search_fields = ('product__name', 'dark_store__name', 'dark_store__code')
    autocomplete_fields = ('product',)
    actions = ['mark_available', 'mark_unavailable', 'replenish_50_units']

    def is_low_stock_display(self, obj):
        if obj.is_out_of_stock:
            return "❌ Out of Stock"
        if obj.is_low_stock:
            return "⚠️ Low Stock"
        return "✅ Healthy"
    is_low_stock_display.short_description = "Stock Health"

    def mark_available(self, request, queryset):
        count = queryset.update(is_available=True)
        self.message_user(request, f"{count} item(s) marked as AVAILABLE.")
    mark_available.short_description = "Mark selected items as AVAILABLE"

    def mark_unavailable(self, request, queryset):
        count = queryset.update(is_available=False)
        self.message_user(request, f"{count} item(s) marked as UNAVAILABLE.")
    mark_unavailable.short_description = "Mark selected items as UNAVAILABLE"

    def replenish_50_units(self, request, queryset):
        count = queryset.update(stock_quantity=50, is_available=True)
        self.message_user(request, f"{count} item(s) replenished to 50 units.")
    replenish_50_units.short_description = "Replenish stock to 50 units"
