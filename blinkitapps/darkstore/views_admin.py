from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum, Q, Count, Avg
from decimal import Decimal

from blinkitapps.accounts.models import User
from blinkitapps.products.models import Product, Category
from .models import DarkStore, DarkStoreInventory


def admin_or_staff_required(view_func):
    """
    Decorator ensuring that only authenticated Staff or Superuser accounts
    can access the Dark Store Admin Dashboard.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, "Please log in with Administrator credentials to access the Dark Store Dashboard.")
            return redirect(f"/accounts/login/?next={request.path}")
        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, "Access Denied: You need Administrator or Staff privileges to access the Dark Store Engine.")
            return redirect('/accounts/login/?next=/dashboard/darkstore/')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


@admin_or_staff_required
def admin_darkstore_dashboard(request):
    """
    Main Executive Dashboard for Dark Store & Location Engine operations.
    """
    stores = DarkStore.objects.all()
    total_stores = stores.count()
    active_stores = stores.filter(is_active=True).count()
    inactive_stores = stores.filter(is_active=False).count()

    # Calculate all unique pincodes covered across network
    all_pincodes_set = set()
    for store in stores:
        for p in store.pincode_list:
            all_pincodes_set.add(p)
    total_pincodes_covered = len(all_pincodes_set)

    # Aggregated inventory metrics
    total_stock_units = DarkStoreInventory.objects.aggregate(total=Sum('stock_quantity'))['total'] or 0
    total_low_stock = DarkStoreInventory.objects.filter(stock_quantity__gt=0, stock_quantity__lte=10, is_available=True).count()
    total_out_of_stock = DarkStoreInventory.objects.filter(Q(stock_quantity=0) | Q(is_available=False)).count()
    avg_network_eta = stores.filter(is_active=True).aggregate(avg=Avg('avg_delivery_mins'))['avg'] or 10

    # High-priority dark stores with health metrics
    store_cards = []
    for store in stores:
        total_items = store.inventories.count()
        low_count = store.low_stock_count
        oos_count = store.out_of_stock_count
        healthy_count = store.in_stock_count
        health_percent = int((healthy_count / total_items * 100)) if total_items > 0 else 0

        store_cards.append({
            'store': store,
            'total_items': total_items,
            'low_count': low_count,
            'oos_count': oos_count,
            'healthy_count': healthy_count,
            'health_percent': health_percent,
        })

    # Recent low stock alerts across all stores
    critical_inventories = DarkStoreInventory.objects.filter(
        Q(stock_quantity__lte=10) | Q(is_available=False)
    ).select_related('dark_store', 'product')[:10]

    return render(request, 'admin_custom/darkstore/dashboard.html', {
        'total_stores': total_stores,
        'active_stores': active_stores,
        'inactive_stores': inactive_stores,
        'total_pincodes_covered': total_pincodes_covered,
        'total_stock_units': total_stock_units,
        'total_low_stock': total_low_stock,
        'total_out_of_stock': total_out_of_stock,
        'avg_network_eta': round(avg_network_eta, 1),
        'store_cards': store_cards,
        'critical_inventories': critical_inventories,
        'active_tab': 'darkstore_dashboard',
    })


@admin_or_staff_required
def admin_darkstore_list(request):
    """
    Comprehensive Dark Store fleet list with filters, quick search, and status toggles.
    """
    query = request.GET.get('q', '').strip()
    city_filter = request.GET.get('city', '').strip()
    status_filter = request.GET.get('status', '').strip()

    stores_qs = DarkStore.objects.all()

    if query:
        stores_qs = stores_qs.filter(
            Q(name__icontains=query) |
            Q(code__icontains=query) |
            Q(address__icontains=query) |
            Q(serviceable_pincodes__icontains=query)
        )

    if city_filter:
        stores_qs = stores_qs.filter(city__iexact=city_filter)

    if status_filter == 'active':
        stores_qs = stores_qs.filter(is_active=True)
    elif status_filter == 'inactive':
        stores_qs = stores_qs.filter(is_active=False)

    cities = DarkStore.objects.values_list('city', flat=True).distinct()

    return render(request, 'admin_custom/darkstore/store_list.html', {
        'stores': stores_qs,
        'query': query,
        'city_filter': city_filter,
        'status_filter': status_filter,
        'cities': cities,
        'active_tab': 'darkstore_list',
    })


@admin_or_staff_required
def admin_darkstore_create(request):
    """
    Create a new Dark Store hub with automatic product inventory linking option.
    """
    if request.method == "POST":
        name = request.POST.get('name', '').strip()
        code = request.POST.get('code', '').strip().upper()
        address = request.POST.get('address', '').strip()
        city = request.POST.get('city', 'Bengaluru').strip()
        state = request.POST.get('state', 'Karnataka').strip()
        serviceable_pincodes = request.POST.get('serviceable_pincodes', '').strip()
        avg_delivery_mins = int(request.POST.get('avg_delivery_mins', 10))
        is_active = request.POST.get('is_active') == 'on'
        latitude = float(request.POST.get('latitude', 12.9352) or 12.9352)
        longitude = float(request.POST.get('longitude', 77.6245) or 77.6245)
        contact_phone = request.POST.get('contact_phone', '').strip()
        manager_name = request.POST.get('manager_name', '').strip()
        auto_seed_inventory = request.POST.get('auto_seed_inventory') == 'on'

        if not name or not code or not serviceable_pincodes:
            messages.error(request, "Store Name, Code, and Serviceable Pincodes are required fields.")
            return render(request, 'admin_custom/darkstore/store_form.html', {
                'form_action': 'create',
                'active_tab': 'darkstore_create',
            })

        if DarkStore.objects.filter(code=code).exists():
            messages.error(request, f"A Dark Store with Code '{code}' already exists.")
            return render(request, 'admin_custom/darkstore/store_form.html', {
                'form_action': 'create',
                'active_tab': 'darkstore_create',
            })

        store = DarkStore.objects.create(
            name=name,
            code=code,
            address=address,
            city=city,
            state=state,
            serviceable_pincodes=serviceable_pincodes,
            avg_delivery_mins=avg_delivery_mins,
            is_active=is_active,
            latitude=latitude,
            longitude=longitude,
            contact_phone=contact_phone,
            manager_name=manager_name,
        )

        # Auto-initialize store inventory with all active catalog products
        if auto_seed_inventory:
            products = Product.objects.all()
            for product in products:
                DarkStoreInventory.objects.get_or_create(
                    dark_store=store,
                    product=product,
                    defaults={'stock_quantity': 50, 'is_available': True}
                )
            messages.success(request, f"Dark Store '{store.name}' created with {products.count()} initial product inventories!")
        else:
            messages.success(request, f"Dark Store '{store.name}' created successfully.")

        return redirect('darkstore_admin:list')

    return render(request, 'admin_custom/darkstore/store_form.html', {
        'form_action': 'create',
        'active_tab': 'darkstore_create',
    })


@admin_or_staff_required
def admin_darkstore_edit(request, store_id):
    """
    Edit parameters of an existing Dark Store.
    """
    store = get_object_or_404(DarkStore, id=store_id)

    if request.method == "POST":
        store.name = request.POST.get('name', '').strip()
        new_code = request.POST.get('code', '').strip().upper()
        if new_code != store.code and DarkStore.objects.filter(code=new_code).exclude(id=store.id).exists():
            messages.error(request, f"Another Dark Store with Code '{new_code}' already exists.")
            return render(request, 'admin_custom/darkstore/store_form.html', {
                'store': store,
                'form_action': 'edit',
                'active_tab': 'darkstore_list',
            })
        store.code = new_code
        store.address = request.POST.get('address', '').strip()
        store.city = request.POST.get('city', 'Bengaluru').strip()
        store.state = request.POST.get('state', 'Karnataka').strip()
        store.serviceable_pincodes = request.POST.get('serviceable_pincodes', '').strip()
        store.avg_delivery_mins = int(request.POST.get('avg_delivery_mins', 10))
        store.is_active = request.POST.get('is_active') == 'on'
        store.latitude = float(request.POST.get('latitude', 12.9352) or 12.9352)
        store.longitude = float(request.POST.get('longitude', 77.6245) or 77.6245)
        store.contact_phone = request.POST.get('contact_phone', '').strip()
        store.manager_name = request.POST.get('manager_name', '').strip()

        store.save()
        messages.success(request, f"Dark Store '{store.name}' updated successfully.")
        return redirect('darkstore_admin:list')

    return render(request, 'admin_custom/darkstore/store_form.html', {
        'store': store,
        'form_action': 'edit',
        'active_tab': 'darkstore_list',
    })


@admin_or_staff_required
def admin_darkstore_toggle_status(request, store_id):
    """
    1-click toggle to open / close a Dark Store hub.
    """
    store = get_object_or_404(DarkStore, id=store_id)
    store.is_active = not store.is_active
    store.save()
    status_label = "OPEN (Active)" if store.is_active else "CLOSED (Inactive)"
    messages.success(request, f"Dark Store '{store.name}' is now {status_label}.")
    return redirect(request.META.get('HTTP_REFERER', 'darkstore_admin:list'))


@admin_or_staff_required
def admin_darkstore_inventory(request, store_id):
    """
    Dedicated store-level inventory matrix allowing direct stock quantity adjustments,
    store-level out-of-stock overrides, and category filtering.
    """
    store = get_object_or_404(DarkStore, id=store_id)
    all_stores = DarkStore.objects.all()

    category_id = request.GET.get('category', '').strip()
    status_filter = request.GET.get('stock_status', '').strip()
    query = request.GET.get('q', '').strip()

    # Ensure all products in catalog have an inventory entry for this store
    all_products = Product.objects.all()
    existing_product_ids = store.inventories.values_list('product_id', flat=True)
    missing_products = all_products.exclude(id__in=existing_product_ids)
    if missing_products.exists():
        for prod in missing_products:
            DarkStoreInventory.objects.create(
                dark_store=store,
                product=prod,
                stock_quantity=50,
                is_available=True
            )

    inventories = store.inventories.select_related('product', 'product__category').all()

    if query:
        inventories = inventories.filter(
            Q(product__name__icontains=query) |
            Q(product__description__icontains=query)
        )

    if category_id and category_id.isdigit():
        inventories = inventories.filter(product__category_id=int(category_id))

    if status_filter == 'in_stock':
        inventories = inventories.filter(stock_quantity__gt=10, is_available=True)
    elif status_filter == 'low_stock':
        inventories = inventories.filter(stock_quantity__gt=0, stock_quantity__lte=10, is_available=True)
    elif status_filter == 'out_of_stock':
        inventories = inventories.filter(Q(stock_quantity=0) | Q(is_available=False))

    categories = Category.objects.all()

    return render(request, 'admin_custom/darkstore/inventory_matrix.html', {
        'store': store,
        'all_stores': all_stores,
        'inventories': inventories,
        'categories': categories,
        'selected_category': int(category_id) if category_id.isdigit() else '',
        'selected_status': status_filter,
        'query': query,
        'active_tab': 'darkstore_inventory',
    })


@admin_or_staff_required
def admin_darkstore_stock_update(request, inventory_id):
    """
    Inline action to adjust stock quantity (+/- / set value) or toggle availability.
    """
    inventory = get_object_or_404(DarkStoreInventory, id=inventory_id)

    if request.method == "POST":
        action = request.POST.get('action') # 'increment', 'decrement', 'set', 'toggle_availability'
        delta = int(request.POST.get('delta', 1))
        exact_value = request.POST.get('quantity')

        if action == 'increment':
            inventory.stock_quantity += delta
            inventory.is_available = True
        elif action == 'decrement':
            inventory.stock_quantity = max(0, inventory.stock_quantity - delta)
            if inventory.stock_quantity == 0:
                inventory.is_available = False
        elif action == 'set' and exact_value is not None:
            try:
                qty = max(0, int(exact_value))
                inventory.stock_quantity = qty
                if qty == 0:
                    inventory.is_available = False
                else:
                    inventory.is_available = True
            except ValueError:
                pass
        elif action == 'toggle_availability':
            inventory.is_available = not inventory.is_available

        inventory.save()

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'stock_quantity': inventory.stock_quantity,
                'is_available': inventory.is_available,
                'is_low_stock': inventory.is_low_stock,
                'is_out_of_stock': inventory.is_out_of_stock,
            })

        messages.success(request, f"Updated stock for '{inventory.product.name}' to {inventory.stock_quantity} units.")

    return redirect(request.META.get('HTTP_REFERER', 'darkstore_admin:dashboard'))


@admin_or_staff_required
def admin_darkstore_bulk_restock(request, store_id):
    """
    1-click replenishment of all low-stock or out-of-stock items in this dark store.
    """
    store = get_object_or_404(DarkStore, id=store_id)
    if request.method == "POST":
        target = request.POST.get('target', 'all_low') # 'all_low', 'all_oos', 'everything'
        replenish_qty = int(request.POST.get('quantity', 50))

        if target == 'all_low':
            updated = store.inventories.filter(stock_quantity__lte=10).update(
                stock_quantity=replenish_qty,
                is_available=True
            )
        elif target == 'all_oos':
            updated = store.inventories.filter(Q(stock_quantity=0) | Q(is_available=False)).update(
                stock_quantity=replenish_qty,
                is_available=True
            )
        else:
            updated = store.inventories.all().update(
                stock_quantity=replenish_qty,
                is_available=True
            )

        messages.success(request, f"Successfully replenished {updated} products to {replenish_qty} units in {store.name}!")

    return redirect(request.META.get('HTTP_REFERER', 'darkstore_admin:inventory', store_id=store.id))


@admin_or_staff_required
def admin_darkstore_simulator(request):
    """
    Interactive Pincode & Routing Simulation Engine:
    Test any Indian pincode, view assigned Dark Store, delivery ETA,
    and 1-click add missing pincodes to coverage hubs.
    """
    test_pincode = request.GET.get('pincode', '').strip()
    active_stores = DarkStore.objects.filter(is_active=True)
    all_stores = DarkStore.objects.all()

    matched_store = None
    if test_pincode:
        for store in active_stores:
            if store.is_pincode_serviceable(test_pincode):
                matched_store = store
                break

    # Stats for simulator
    total_covered_pincodes = sum(s.pincode_count for s in all_stores)

    return render(request, 'admin_custom/darkstore/simulator.html', {
        'test_pincode': test_pincode,
        'matched_store': matched_store,
        'active_stores': active_stores,
        'all_stores': all_stores,
        'total_covered_pincodes': total_covered_pincodes,
        'active_tab': 'darkstore_simulator',
    })


@admin_or_staff_required
def admin_darkstore_quick_assign_pincode(request):
    """
    1-click assign a tested pincode from simulator directly to a selected Dark Store.
    """
    if request.method == "POST":
        pincode = request.POST.get('pincode', '').strip()
        store_id = request.POST.get('store_id')

        if pincode and store_id:
            store = get_object_or_404(DarkStore, id=store_id)
            existing_pincodes = [p.strip() for p in store.serviceable_pincodes.split(',') if p.strip()]

            if pincode not in existing_pincodes:
                existing_pincodes.append(pincode)
                store.serviceable_pincodes = ", ".join(existing_pincodes)
                store.save()
                messages.success(request, f"Pincode {pincode} successfully added to '{store.name}' coverage area!")
            else:
                messages.info(request, f"Pincode {pincode} is already covered by '{store.name}'.")

    return redirect(f"/dashboard/darkstore/simulator/?pincode={request.POST.get('pincode', '')}")
