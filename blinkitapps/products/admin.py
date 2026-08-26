from django.contrib import admin
from .models import Category, SubCategory, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_popular', 'display_order')
    list_editable = ('display_order', 'is_popular')
    search_fields = ('name',)


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    list_filter = ('category',)
    search_fields = ('name', 'category__name')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'category', 'unit_quantity', 'mrp', 'selling_price',
        'discount_percentage', 'is_active', 'is_out_of_stock', 'is_trending', 'is_bestseller'
    )
    list_editable = ('selling_price', 'is_active', 'is_out_of_stock', 'is_trending', 'is_bestseller')
    list_filter = ('category', 'is_active', 'is_out_of_stock', 'is_trending', 'is_bestseller')
    search_fields = ('name', 'description')
    actions = ['mark_out_of_stock', 'mark_in_stock']

    def mark_out_of_stock(self, request, queryset):
        count = queryset.update(is_out_of_stock=True)
        self.message_user(request, f"{count} product(s) marked as OUT OF STOCK.")
    mark_out_of_stock.short_description = "Mark selected products as OUT OF STOCK"

    def mark_in_stock(self, request, queryset):
        count = queryset.update(is_out_of_stock=False)
        self.message_user(request, f"{count} product(s) marked as IN STOCK.")
    mark_in_stock.short_description = "Mark selected products as IN STOCK"
