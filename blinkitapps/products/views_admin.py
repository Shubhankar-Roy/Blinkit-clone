from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Sum, Count, Q
from decimal import Decimal

from blinkitapps.products.models import Product, Category, SubCategory
from blinkitapps.orders.models import Order
from blinkitapps.promotions.models import Coupon
from blinkitapps.darkstore.models import DarkStore, DarkStoreInventory

User = get_user_model()


def admin_or_staff_required(view_func):
    """
    Decorator restricting access to staff or superuser administrators.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Auto-ensure superuser exists for immediate developer setup
        if not User.objects.filter(username='admin').exists():
            u = User.objects.create_superuser('admin', 'admin@blinkit.com', 'admin123')
            u.is_staff = True
            u.is_superuser = True
            u.save()

        if not request.user.is_authenticated:
            messages.warning(request, "Please log in with Administrator credentials to access the Store Manager Dashboard.")
            return redirect(f"/accounts/login/?next={request.path}")
        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, "Access Denied: Administrator privileges required.")
            return redirect('/accounts/login/?next=/dashboard/')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


@admin_or_staff_required
def admin_dashboard_home(request):
    """
    Master Merchant & Operations Analytics Dashboard at /dashboard/.
    """
    total_orders = Order.objects.count()
    total_revenue = Order.objects.filter(payment_status='SUCCESS').aggregate(total=Sum('grand_total'))['total'] or Decimal('0.00')
    total_products = Product.objects.count()
    out_of_stock_count = Product.objects.filter(Q(is_out_of_stock=True) | Q(is_active=False)).count()
    active_darkstores = DarkStore.objects.filter(is_active=True).count()
    active_coupons = Coupon.objects.filter(is_active=True).count()

    # Pipeline stats
    placed_orders = Order.objects.filter(status='PLACED').count()
    packing_orders = Order.objects.filter(status='PACKING').count()
    out_for_delivery_orders = Order.objects.filter(status='OUT_FOR_DELIVERY').count()
    delivered_orders = Order.objects.filter(status='DELIVERED').count()

    recent_orders = Order.objects.select_related('user', 'dark_store').order_by('-created_at')[:8]
    recent_products = Product.objects.select_related('category').order_by('-id')[:6]

    return render(request, 'admin_custom/index.html', {
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'total_products': total_products,
        'out_of_stock_count': out_of_stock_count,
        'active_darkstores': active_darkstores,
        'active_coupons': active_coupons,
        'placed_orders': placed_orders,
        'packing_orders': packing_orders,
        'out_for_delivery_orders': out_for_delivery_orders,
        'delivered_orders': delivered_orders,
        'recent_orders': recent_orders,
        'recent_products': recent_products,
        'active_tab': 'dashboard_home',
    })


@admin_or_staff_required
def admin_products_list(request):
    """
    Merchant Product Catalog list with filtering and 1-click stock toggles.
    """
    category_id = request.GET.get('category', 'ALL')
    stock_status = request.GET.get('stock', 'ALL')
    search_query = request.GET.get('q', '').strip()

    products = Product.objects.select_related('category', 'subcategory').all().order_by('-id')

    if category_id != 'ALL':
        products = products.filter(category_id=category_id)
    if stock_status == 'OUT_OF_STOCK':
        products = products.filter(Q(is_out_of_stock=True) | Q(is_active=False))
    elif stock_status == 'IN_STOCK':
        products = products.filter(is_out_of_stock=False, is_active=True)
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(category__name__icontains=search_query)
        )

    categories = Category.objects.all()

    return render(request, 'admin_custom/products/product_list.html', {
        'products': products,
        'categories': categories,
        'category_id': category_id,
        'stock_status': stock_status,
        'search_query': search_query,
        'total_count': Product.objects.count(),
        'out_of_stock_count': Product.objects.filter(is_out_of_stock=True).count(),
        'active_tab': 'products_catalog',
    })


@admin_or_staff_required
def admin_product_add(request):
    """
    Create a new catalog product and automatically sync inventory to active Dark Stores.
    """
    categories = Category.objects.all()
    subcategories = SubCategory.objects.all()

    if request.method == "POST":
        name = request.POST.get('name', '').strip()
        category_id = request.POST.get('category')
        subcategory_id = request.POST.get('subcategory')
        unit_quantity = request.POST.get('unit_quantity', '500g').strip()
        mrp = Decimal(str(request.POST.get('mrp', '0')))
        selling_price = Decimal(str(request.POST.get('selling_price', '0')))
        description = request.POST.get('description', '').strip()
        image_url = request.POST.get('image_url', '').strip()
        
        is_active = request.POST.get('is_active') == 'on'
        is_trending = request.POST.get('is_trending') == 'on'
        is_bestseller = request.POST.get('is_bestseller') == 'on'
        is_out_of_stock = request.POST.get('is_out_of_stock') == 'on'

        if not name or not category_id or selling_price <= 0:
            messages.error(request, "Name, Category, and valid Selling Price are required.")
            return render(request, 'admin_custom/products/product_form.html', {
                'form_action': 'create',
                'categories': categories,
                'subcategories': subcategories,
                'active_tab': 'products_catalog',
            })

        category = get_object_or_404(Category, id=category_id)
        subcategory = SubCategory.objects.filter(id=subcategory_id).first() if subcategory_id else None

        product = Product.objects.create(
            name=name,
            category=category,
            subcategory=subcategory,
            unit_quantity=unit_quantity,
            mrp=mrp if mrp >= selling_price else selling_price,
            selling_price=selling_price,
            description=description,
            image_url=image_url,
            is_active=is_active,
            is_trending=is_trending,
            is_bestseller=is_bestseller,
            is_out_of_stock=is_out_of_stock,
        )

        # Sync initial stock to all active Dark Stores
        initial_stock = int(request.POST.get('initial_stock', 50))
        for store in DarkStore.objects.filter(is_active=True):
            DarkStoreInventory.objects.create(
                dark_store=store,
                product=product,
                stock_quantity=initial_stock,
                is_available=not is_out_of_stock
            )

        messages.success(request, f"Product '{product.name}' created and synchronized across all Dark Store hubs!")
        return redirect('admin_dashboard:products')

    return render(request, 'admin_custom/products/product_form.html', {
        'form_action': 'create',
        'categories': categories,
        'subcategories': subcategories,
        'active_tab': 'products_catalog',
    })


@admin_or_staff_required
def admin_product_edit(request, product_id):
    """
    Edit an existing catalog product.
    """
    product = get_object_or_404(Product, id=product_id)
    categories = Category.objects.all()
    subcategories = SubCategory.objects.all()

    if request.method == "POST":
        product.name = request.POST.get('name', '').strip()
        category_id = request.POST.get('category')
        subcategory_id = request.POST.get('subcategory')
        product.unit_quantity = request.POST.get('unit_quantity', '500g').strip()
        product.mrp = Decimal(str(request.POST.get('mrp', '0')))
        product.selling_price = Decimal(str(request.POST.get('selling_price', '0')))
        product.description = request.POST.get('description', '').strip()
        product.image_url = request.POST.get('image_url', '').strip()
        
        product.is_active = request.POST.get('is_active') == 'on'
        product.is_trending = request.POST.get('is_trending') == 'on'
        product.is_bestseller = request.POST.get('is_bestseller') == 'on'
        product.is_out_of_stock = request.POST.get('is_out_of_stock') == 'on'

        if category_id:
            product.category = get_object_or_404(Category, id=category_id)
        product.subcategory = SubCategory.objects.filter(id=subcategory_id).first() if subcategory_id else None

        product.save()
        messages.success(request, f"Product '{product.name}' updated successfully.")
        return redirect('admin_dashboard:products')

    return render(request, 'admin_custom/products/product_form.html', {
        'product': product,
        'form_action': 'edit',
        'categories': categories,
        'subcategories': subcategories,
        'active_tab': 'products_catalog',
    })


@admin_or_staff_required
def admin_product_toggle_stock(request, product_id):
    """
    1-click live toggle for product Out-of-Stock status.
    """
    if request.method == "POST":
        product = get_object_or_404(Product, id=product_id)
        product.is_out_of_stock = not product.is_out_of_stock
        product.save()
        status_str = "OUT OF STOCK" if product.is_out_of_stock else "IN STOCK"
        messages.success(request, f"'{product.name}' marked as {status_str}.")
    return redirect(request.META.get('HTTP_REFERER', 'admin_dashboard:products'))


@admin_or_staff_required
def admin_product_delete(request, product_id):
    """
    Deletes a product from the catalog.
    """
    if request.method == "POST":
        product = get_object_or_404(Product, id=product_id)
        name = product.name
        product.delete()
        messages.success(request, f"Product '{name}' deleted.")
    return redirect('admin_dashboard:products')
