from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.db.models import Q
from .models import Category, SubCategory, Product
from blinkitapps.cart.models import Cart, CartItem
from blinkitapps.darkstore.models import DarkStore, DarkStoreInventory

POPULAR_SEARCH_KEYWORDS = [
    'Milk', 'Bread', 'Eggs', 'Butter', 'Curd', 'Paneer',
    'Chips', 'Bananas', 'Tomatoes', 'Biscuits', 'Cold Drinks', 'Ice Cream'
]


def _get_cart_items_map(request):
    """
    Returns a dictionary of {product_id: quantity} for current user/session cart.
    """
    cart = None
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
    else:
        session_id = request.session.session_key
        if session_id:
            cart = Cart.objects.filter(session_id=session_id).first()

    if cart:
        return {item.product_id: item.quantity for item in cart.items.all()}
    return {}


def _get_current_darkstore(request):
    """
    Retrieves the Dark Store serving the current session's pincode.
    """
    pincode = request.session.get('pincode', '560034')
    active_stores = DarkStore.objects.filter(is_active=True)
    
    for store in active_stores:
        if store.is_pincode_serviceable(pincode):
            return store
            
    return active_stores.first()


def _annotate_products(products, request):
    """
    Attaches in-cart quantities and store-level stock availability
    to product objects for accurate UI rendering.
    """
    cart_map = _get_cart_items_map(request)
    dark_store = _get_current_darkstore(request)
    
    # Build inventory lookup map if dark store is present
    inventory_map = {}
    if dark_store:
        inventories = DarkStoreInventory.objects.filter(dark_store=dark_store)
        inventory_map = {inv.product_id: inv for inv in inventories}

    product_list = list(products)
    for p in product_list:
        p.in_cart_qty = cart_map.get(p.id, 0)
        
        if dark_store:
            inv = inventory_map.get(p.id)
            if inv:
                p.store_stock = inv.stock_quantity
                # Product is out of stock if globally disabled, store inventory disabled, or store stock is 0
                p.is_out_of_stock = p.is_out_of_stock or inv.is_out_of_stock
            else:
                p.store_stock = 0
                p.is_out_of_stock = True
        else:
            p.store_stock = 50

    return product_list


def home_view(request):
    """
    Homepage view with Popular Categories, Trending Items, Bestsellers,
    and Featured Essentials.
    """
    categories = Category.objects.filter(is_popular=True)
    
    trending_qs = Product.objects.filter(is_active=True, is_trending=True)[:8]
    bestseller_qs = Product.objects.filter(is_active=True, is_bestseller=True)[:8]
    all_products_qs = Product.objects.filter(is_active=True)[:18]

    trending_products = _annotate_products(trending_qs, request)
    bestseller_products = _annotate_products(bestseller_qs, request)
    all_products = _annotate_products(all_products_qs, request)

    return render(request, 'products/home.html', {
        'categories': categories,
        'trending_products': trending_products,
        'bestseller_products': bestseller_products,
        'all_products': all_products,
        'search_keywords': POPULAR_SEARCH_KEYWORDS,
    })


def all_categories_view(request):
    """
    Redirects to first category or home.
    """
    first_cat = Category.objects.first()
    if first_cat:
        return redirect('products:category_list', id=first_cat.id)
    return redirect('products:home')


def category_view(request, id):
    """
    Category listing page with nested subcategories, sorting, and stock status.
    """
    category = get_object_or_404(Category, id=id)
    subcategories = category.subcategories.all() if hasattr(category, 'subcategories') else category.subcategory_set.all()
    all_categories = Category.objects.all()

    sub_id = request.GET.get('sub', '').strip()
    sort_by = request.GET.get('sort', '').strip()

    products_qs = Product.objects.filter(category=category, is_active=True)

    if sub_id and sub_id.isdigit():
        products_qs = products_qs.filter(subcategory_id=int(sub_id))

    # Apply sorting
    if sort_by == 'price_low':
        products_qs = products_qs.order_by('selling_price')
    elif sort_by == 'price_high':
        products_qs = products_qs.order_by('-selling_price')
    elif sort_by == 'discount':
        products_qs = products_qs.order_by('-discount_percentage')
    elif sort_by == 'popular':
        products_qs = products_qs.order_by('-is_bestseller', '-is_trending')
    else:
        products_qs = products_qs.order_by('name')

    products = _annotate_products(products_qs, request)

    return render(request, 'products/category_list.html', {
        'category': category,
        'all_categories': all_categories,
        'subcategories': subcategories,
        'products': products,
        'selected_sub': int(sub_id) if sub_id.isdigit() else '',
        'selected_sort': sort_by,
        'total_count': len(products),
    })


def product_detail_view(request, id):
    """
    Product detail page with images, description, stock status, and related products.
    """
    product = get_object_or_404(Product, id=id, is_active=True)
    
    # Annotate product with cart & stock
    annotated_single = _annotate_products([product], request)
    current_product = annotated_single[0]

    related_qs = Product.objects.filter(category=product.category, is_active=True).exclude(id=product.id)[:6]
    related_products = _annotate_products(related_qs, request)

    return render(request, 'products/product_detail.html', {
        'product': current_product,
        'related_products': related_products,
    })


def search_view(request):
    """
    Comprehensive search engine with multi-faceted matching across product name,
    category, subcategory, and description, with category filtering and sorting.
    """
    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '').strip()
    sort_by = request.GET.get('sort', '').strip()

    products_qs = Product.objects.none()
    
    if query:
        search_filter = (
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query) |
            Q(subcategory__name__icontains=query)
        )
        products_qs = Product.objects.filter(search_filter, is_active=True).distinct()

        # Category refinement
        if category_id and category_id.isdigit():
            products_qs = products_qs.filter(category_id=int(category_id))

        # Sorting
        if sort_by == 'price_low':
            products_qs = products_qs.order_by('selling_price')
        elif sort_by == 'price_high':
            products_qs = products_qs.order_by('-selling_price')
        elif sort_by == 'discount':
            products_qs = products_qs.order_by('-discount_percentage')
        elif sort_by == 'popular':
            products_qs = products_qs.order_by('-is_bestseller', '-is_trending')

    products = _annotate_products(products_qs, request)
    categories = Category.objects.all()

    return render(request, 'products/search_results.html', {
        'query': query,
        'products': products,
        'count': len(products),
        'categories': categories,
        'selected_category': int(category_id) if category_id.isdigit() else '',
        'selected_sort': sort_by,
        'popular_keywords': POPULAR_SEARCH_KEYWORDS,
    })