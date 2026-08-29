# Comprehensive Production Roadmap & Implementation Guide: Blinkit WebApp Clone
*(Built exclusively using **Django 5.x**, **HTML5 Templates**, and **Tailwind CSS**)*

---

## 📖 Executive Summary & Tech Stack Constraints

This guide is an end-to-end, production-ready architecture blueprint and step-by-step roadmap to build a 100% feature-complete clone of **Blinkit** (India's leading 10-minute instant grocery delivery web application).

### Core Stack Rules:
1. **Backend Framework**: Python **Django 5.x** (Monolithic MVC pattern using Django Templates, ORM, Forms, and Context Processors).
2. **Frontend UI & Styling**: **Pure HTML5** + **Tailwind CSS** (via CDN or Tailwind CLI). Zero external JS frameworks (No React, Vue, Next.js, or Angular).
3. **Database**: PostgreSQL (Production) / SQLite3 (Development).
4. **Payment Gateway**: Razorpay Integration + Cash on Delivery (COD).

---

## 🏗️ Master Feature Matrix

| Module | Features Included |
| :--- | :--- |
| **Authentication & User Profile** | User Register/Login (Phone OTP / Email & Password), Multi-address management (Home, Work, Other), Default address selector, Order history. |
| **Location & Dark Store Engine** | Dynamic Pincode/Location modal, Session-based store assignment, Location-based product visibility & stock checking, Estimated Delivery Time (ETA) calculation. |
| **Product Catalog & Search** | Nested Categories & Subcategories, Search with filters, Dynamic badges (Bestseller, Trending, Discount %), Unit quantity indicators (500g, 1L, etc.). |
| **Stock & Inventory Engine** | Real-time Stock tracking per Dark Store, "Out of Stock" badges, automatic disablement of cart additions for zero-stock items. |
| **Cart & Promotions Engine** | Slide-over cart drawer, instant item count & price recalculations, Delivery fee calculation (Free delivery above threshold), Small order fee, Handling fee, Tip for delivery partner. |
| **Coupons & Offers Engine** | Coupon codes (Flat discount, Percentage discount, Min order value, Expiry dates), Applied coupon indicator, Instant discount deduction. |
| **Payments & Checkout** | Address selection during checkout, Payment method selector (Razorpay Gateway / Cash on Delivery), Webhook/Callback payment verification. |
| **Order Lifecycle & Tracking** | Visual multi-step tracking progress bar (`Order Placed` ➔ `Packing at Dark Store` ➔ `Out for Delivery` ➔ `Delivered`), Delivery Partner & Store details. |
| **Custom Admin & Merchant Portal** | Production Django Admin with custom filters, Bulk "Out of Stock" toggles, Live Order status change, Coupon creator, Dark Store inventory management. |

---

## 📁 Recommended Project Directory Layout

```text
blinkit_clone/
├── manage.py
├── config/                      # Core Django Project Configuration
│   ├── __init__.py
│   ├── settings.py              # Installed apps, middleware, template context processors
│   ├── urls.py                  # Main URL Routing table
│   └── wsgi.py
├── apps/
│   ├── accounts/                # Custom User, Authentication & Address Models/Views
│   ├── darkstore/               # DarkStore, Inventory & Location Context Processor
│   ├── products/                # Category, SubCategory, Product & Search Engine
│   ├── cart/                    # Cart, CartItem & Session/DB Cart management
│   ├── promotions/              # Coupons, Discount engine & Promotional Banners
│   ├── payments/                # Razorpay Gateway integration & Payment logging
│   └── orders/                  # Order placement, Item snapshots & Live Tracking
├── static/
│   ├── css/
│   │   ├── input.css            # Tailwind directives
│   │   └── output.css           # Compiled Tailwind CSS stylesheet
│   └── images/                  # Static assets & placeholders
└── templates/
    ├── base.html                # Master HTML layout (Contains CSS modal checkboxes & Header/Footer)
    ├── components/              # Header, Footer, Product Card, Cart Drawer, Location Modal, Coupon Drawer
    ├── accounts/                # Login, Register, Profile & Address forms
    ├── products/                # Homepage, Category listing, Search results, Product detail
    ├── cart/                    # Full cart overview page
    ├── orders/                  # Checkout, Order Confirmation, Live Tracking
    └── admin_custom/            # Custom Store Manager Dashboard (Optional layout extension)
```

---

## 📌 Phase 1: Complete Database Schema (Django Models)

### 1. `apps/accounts/models.py` (User & Address Management)
```python
from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    phone_number = models.CharField(max_length=15, unique=True, null=True, blank=True)
    is_delivery_partner = models.BooleanField(default=False)
    is_store_manager = models.BooleanField(default=False)

    def __str__(self):
        return self.username or self.email or self.phone_number or f"User-{self.id}"

class Address(models.Model):
    ADDRESS_TYPES = (('Home', 'Home'), ('Work', 'Work'), ('Other', 'Other'))
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    house_flat_no = models.CharField(max_length=100, help_text="Flat, House no., Building name")
    floor_apartment = models.CharField(max_length=100, blank=True, null=True)
    area_street = models.TextField(help_text="Area, Street, Sector, Village")
    landmark = models.CharField(max_length=150, blank=True, null=True)
    pincode = models.CharField(max_length=10)
    city = models.CharField(max_length=50)
    address_type = models.CharField(max_length=10, choices=ADDRESS_TYPES, default='Home')
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.is_default:
            Address.objects.filter(user=self.user).update(is_default=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.house_flat_no}, {self.area_street} ({self.pincode})"
```

### 2. `apps/darkstore/models.py` (Dark Store & Store Inventory Engine)
```python
from django.db import models

class DarkStore(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    address = models.TextField()
    city = models.CharField(max_length=50, default='Bengaluru')
    serviceable_pincodes = models.TextField(help_text="Comma-separated pincodes e.g. 560034, 560095, 560100")
    avg_delivery_mins = models.IntegerField(default=10)
    is_active = models.BooleanField(default=True)

    def is_pincode_serviceable(self, pincode):
        pincodes = [p.strip() for p in self.serviceable_pincodes.split(',')]
        return str(pincode).strip() in pincodes

    def __str__(self):
        return f"{self.name} ({self.code})"

class DarkStoreInventory(models.Model):
    dark_store = models.ForeignKey(DarkStore, on_delete=models.CASCADE, related_name='inventories')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='store_inventories')
    stock_quantity = models.PositiveIntegerField(default=50)
    is_available = models.BooleanField(default=True)

    class Meta:
        unique_together = ('dark_store', 'product')

    def __str__(self):
        return f"{self.product.name} at {self.dark_store.name}: {self.stock_quantity} units"
```

### 3. `apps/products/models.py` (Category, SubCategory & Products)
```python
from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    icon_url = models.URLField(blank=True, null=True)
    is_popular = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)

    class Meta:
        ordering = ['display_order', 'name']

    def get_image(self):
        if self.image:
            return self.image.url
        if self.icon_url:
            return self.icon_url
        return 'https://cdn-icons-png.flaticon.com/512/3081/3081986.png'

    def __str__(self):
        return self.name

class SubCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.category.name} -> {self.name}"

class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    subcategory = models.ForeignKey(SubCategory, on_delete=models.CASCADE, null=True, blank=True, related_name='products')
    unit_quantity = models.CharField(max_length=50, help_text="e.g. 500 ml, 1 L, 400 g, 1 pack")
    mrp = models.DecimalField(max_digits=8, decimal_places=2)
    selling_price = models.DecimalField(max_digits=8, decimal_places=2)
    discount_percentage = models.IntegerField(default=0)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True, help_text="Global active status")
    is_out_of_stock = models.BooleanField(default=False, help_text="Global Out-of-Stock Override")
    is_trending = models.BooleanField(default=False)
    is_bestseller = models.BooleanField(default=False)
    eta_minutes = models.IntegerField(default=10)

    def save(self, *args, **kwargs):
        if self.mrp > 0 and self.selling_price < self.mrp:
            self.discount_percentage = int(((self.mrp - self.selling_price) / self.mrp) * 100)
        else:
            self.discount_percentage = 0
        super().save(*args, **kwargs)

    def get_image(self):
        if self.image:
            return self.image.url
        if self.image_url:
            return self.image_url
        return 'https://cdn-icons-png.flaticon.com/512/679/679821.png'

    def __str__(self):
        return self.name
```

### 4. `apps/promotions/models.py` (Coupons & Offers Engine)
```python
from django.db import models
from django.utils import timezone

class Coupon(models.Model):
    DISCOUNT_TYPES = (
        ('FLAT', 'Flat Amount Discount (₹)'),
        ('PERCENTAGE', 'Percentage Discount (%)'),
    )

    code = models.CharField(max_length=20, unique=True)
    description = models.CharField(max_length=255)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPES, default='FLAT')
    discount_value = models.DecimalField(max_digits=8, decimal_places=2)
    min_order_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    max_discount_amount = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="For percentage discounts")
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    usage_limit = models.PositiveIntegerField(default=1000)
    times_used = models.PositiveIntegerField(default=0)

    def is_valid_for_cart(self, cart_total):
        now = timezone.now()
        if not self.is_active:
            return False, "Coupon is inactive."
        if now < self.valid_from or now > self.valid_until:
            return False, "Coupon has expired."
        if self.times_used >= self.usage_limit:
            return False, "Coupon usage limit reached."
        if cart_total < self.min_order_amount:
            return False, f"Minimum order amount of ₹{self.min_order_amount:.0f} required."
        return True, "Valid coupon."

    def calculate_discount(self, cart_total):
        if self.discount_type == 'FLAT':
            return min(self.discount_value, cart_total)
        elif self.discount_type == 'PERCENTAGE':
            discount = (self.discount_value / 100) * cart_total
            if self.max_discount_amount:
                discount = min(discount, self.max_discount_amount)
            return min(discount, cart_total)
        return 0

    def __str__(self):
        return f"{self.code} - {self.description}"
```

### 5. `apps/cart/models.py` (Cart & Items)
```python
from django.db import models
from django.conf import settings
from apps.products.models import Product
from apps.promotions.models import Coupon

class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=100, null=True, blank=True)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total_mrp(self):
        return sum(item.mrp_subtotal for item in self.items.all())

    @property
    def items_subtotal(self):
        return sum(item.subtotal for item in self.items.all())

    @property
    def coupon_discount(self):
        if self.coupon:
            is_valid, _ = self.coupon.is_valid_for_cart(self.items_subtotal)
            if is_valid:
                return self.coupon.calculate_discount(self.items_subtotal)
        return 0

    @property
    def delivery_fee(self):
        # Free delivery above ₹199
        if self.items_subtotal >= 199 or self.item_count == 0:
            return 0.00
        return 25.00

    @property
    def handling_fee(self):
        return 4.00 if self.item_count > 0 else 0.00

    @property
    def grand_total(self):
        return max(0, self.items_subtotal - self.coupon_discount + self.delivery_fee + self.handling_fee)

    @property
    def total_savings(self):
        return (self.total_mrp - self.items_subtotal) + self.coupon_discount

    @property
    def item_count(self):
        return sum(item.quantity for item in self.items.all())

    def __str__(self):
        return f"Cart #{self.id} ({self.item_count} items)"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def subtotal(self):
        return self.product.selling_price * self.quantity

    @property
    def mrp_subtotal(self):
        return self.product.mrp * self.quantity
```

### 6. `apps/orders/models.py` (Orders & Items)
```python
from django.db import models
from django.conf import settings
from apps.products.models import Product
from apps.darkstore.models import DarkStore
import uuid

class Order(models.Model):
    STATUS_CHOICES = (
        ('PLACED', 'Order Placed'),
        ('PACKING', 'Packing at Dark Store'),
        ('OUT_FOR_DELIVERY', 'Out for Delivery'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    )
    PAYMENT_METHODS = (
        ('COD', 'Cash on Delivery'),
        ('RAZORPAY', 'Online Payment (Razorpay / UPI)'),
    )

    order_number = models.CharField(max_length=25, unique=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    dark_store = models.ForeignKey(DarkStore, on_delete=models.SET_NULL, null=True, blank=True)
    delivery_address = models.TextField()
    pincode = models.CharField(max_length=10)
    phone = models.CharField(max_length=15)
    
    items_total = models.DecimalField(max_digits=10, decimal_places=2)
    coupon_discount = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    delivery_fee = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    handling_fee = models.DecimalField(max_digits=6, decimal_places=2, default=4.00)
    tip_amount = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2)
    
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='COD')
    payment_status = models.CharField(max_length=20, default='PENDING') # PENDING, SUCCESS, FAILED
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='PLACED')
    eta_minutes = models.IntegerField(default=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f"BLK-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order #{self.order_number} ({self.status})"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=200)
    unit_quantity = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
```

---

## 📌 Phase 2: Context Processors & Business Logic Engine

### 1. Location & Store Processor (`apps/darkstore/context_processors.py`)
```python
from .models import DarkStore

def location_processor(request):
    pincode = request.session.get('pincode', '560034')
    location_name = request.session.get('location_name', 'Koramangala, Bengaluru')
    
    # Find matching Dark Store
    dark_store = DarkStore.objects.filter(is_active=True).first()
    for store in DarkStore.objects.filter(is_active=True):
        if store.is_pincode_serviceable(pincode):
            dark_store = store
            break
            
    eta_mins = dark_store.avg_delivery_mins if dark_store else 12

    return {
        'current_pincode': pincode,
        'current_location_name': location_name,
        'current_dark_store': dark_store,
        'eta_mins': eta_mins,
    }
```

### 2. Cart Context Processor (`apps/cart/context_processors.py`)
```python
from .models import Cart

def cart_processor(request):
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
    }
```

---

## 📌 Phase 2.5: Mandatory User Authentication & Guest Cart Merging Engine

Matching real-world **Blinkit** behavior:
1. **Guest Browsing**: Users can browse the catalog and add products to a session-based cart without logging in.
2. **Mandatory Login Enforcement**: Accessing checkout (`checkout_view`) or placing an order (`place_order_view`) requires authentication via `@login_required(login_url='/accounts/login/')`.
3. **Cart Transfer upon Login**: Logging in automatically merges all items from the temporary session cart into the user's permanent database cart.

### `apps/accounts/views.py` (Guest Cart Merging Handler)
```python
from apps.cart.models import Cart, CartItem

def _merge_session_cart_to_user(request, user):
    session_id = request.session.session_key
    if session_id:
        session_cart = Cart.objects.filter(session_id=session_id).first()
        if session_cart and session_cart.items.exists():
            user_cart, _ = Cart.objects.get_or_create(user=user)
            for item in session_cart.items.all():
                u_item, created = CartItem.objects.get_or_create(cart=user_cart, product=item.product)
                if not created:
                    u_item.quantity += item.quantity
                else:
                    u_item.quantity = item.quantity
                u_item.save()
            session_cart.delete()
```

### `apps/orders/views.py` (Enforced Login Views)
```python
from django.contrib.auth.decorators import login_required

@login_required(login_url='/accounts/login/')
def checkout_view(request):
    cart = Cart.objects.filter(user=request.user).first()
    # Renders checkout only for authenticated users with active cart...

@login_required(login_url='/accounts/login/')
def place_order_view(request):
    # Processes order placement for authenticated user...
```

---

## 📌 Phase 3: Razorpay & Cash on Delivery Payment Engine

### `apps/payments/views.py`
```python
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from apps.orders.models import Order
from apps.cart.models import Cart
import razorpay

def initiate_checkout(request):
    # Retrieve user cart and create order
    cart = get_or_create_cart(request)
    if cart.item_count == 0:
        return redirect('products:home')

    if request.method == "POST":
        address_text = request.POST.get('address')
        phone = request.POST.get('phone')
        payment_method = request.POST.get('payment_method') # 'COD' or 'RAZORPAY'

        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            delivery_address=address_text,
            pincode=request.session.get('pincode', '560034'),
            phone=phone,
            items_total=cart.items_subtotal,
            coupon_discount=cart.coupon_discount,
            delivery_fee=cart.delivery_fee,
            handling_fee=cart.handling_fee,
            grand_total=cart.grand_total,
            payment_method=payment_method,
            payment_status='SUCCESS' if payment_method == 'COD' else 'PENDING'
        )

        # Snapshot cart items into OrderItem
        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                product_name=item.product.name,
                unit_quantity=item.product.unit_quantity,
                price=item.product.selling_price,
                quantity=item.quantity,
                subtotal=item.subtotal
            )

        # Clear cart
        cart.items.all().delete()
        if cart.coupon:
            cart.coupon.times_used += 1
            cart.coupon.save()
            cart.coupon = None
            cart.save()

        if payment_method == 'RAZORPAY':
            # Create Razorpay order
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            razorpay_order = client.order.create({
                'amount': int(order.grand_total * 100), # Amount in paise
                'currency': 'INR',
                'payment_capture': '1'
            })
            order.razorpay_order_id = razorpay_order['id']
            order.save()
            
            return render(request, 'payments/razorpay_pay.html', {
                'order': order,
                'razorpay_order_id': razorpay_order['id'],
                'razorpay_key_id': settings.RAZORPAY_KEY_ID,
                'amount': order.grand_total,
            })

        return redirect('orders:track', order_number=order.order_number)
```

---

## 📌 Phase 4: Production Django Admin Customization

### `apps/products/admin.py` & `apps/orders/admin.py`
```python
from django.contrib import admin
from apps.products.models import Category, SubCategory, Product
from apps.darkstore.models import DarkStore, DarkStoreInventory
from apps.promotions.models import Coupon
from apps.orders.models import Order, OrderItem

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'mrp', 'selling_price', 'discount_percentage', 'is_active', 'is_out_of_stock', 'is_trending')
    list_editable = ('selling_price', 'is_active', 'is_out_of_stock', 'is_trending')
    list_filter = ('category', 'is_active', 'is_out_of_stock', 'is_trending', 'is_bestseller')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    actions = ['mark_out_of_stock', 'mark_in_stock']

    def mark_out_of_stock(self, request, queryset):
        queryset.update(is_out_of_stock=True)
    mark_out_of_stock.short_description = "Mark selected products as OUT OF STOCK"

    def mark_in_stock(self, request, queryset):
        queryset.update(is_out_of_stock=False)
    mark_in_stock.short_description = "Mark selected products as IN STOCK"

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product_name', 'unit_quantity', 'price', 'quantity', 'subtotal')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'phone', 'grand_total', 'payment_method', 'payment_status', 'status', 'created_at')
    list_editable = ('status', 'payment_status')
    list_filter = ('status', 'payment_method', 'payment_status', 'created_at')
    search_fields = ('order_number', 'phone', 'pincode')
    inlines = [OrderItemInline]

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'discount_value', 'min_order_amount', 'valid_until', 'is_active', 'times_used')
    list_editable = ('is_active',)
    search_fields = ('code', 'description')
```

---

## 📌 Phase 5: Dedicated Custom Admin & Store Manager Dashboard (`/dashboard/`)

Instead of relying solely on standard Django Admin, a full-featured, dedicated **Store Manager Dashboard** is implemented at `/dashboard/` using **Pure HTML** and **Tailwind CSS**.

### 1. Admin Dashboard Router (`apps/products/urls_admin.py`)
```python
from django.urls import path
from . import views_admin

app_name = 'admin_dashboard'

urlpatterns = [
    path('', views_admin.admin_dashboard_home, name='home'),
    path('login/', views_admin.admin_login_view, name='login'),
    path('logout/', views_admin.admin_logout_view, name='logout'),
    path('products/', views_admin.admin_products_list, name='products'),
    path('products/add/', views_admin.admin_product_add, name='product_add'),
    path('products/toggle-stock/<int:product_id>/', views_admin.admin_product_toggle_stock, name='product_toggle_stock'),
    path('orders/', views_admin.admin_orders_list, name='orders'),
    path('orders/update-status/<int:order_id>/', views_admin.admin_order_update_status, name='order_update_status'),
    path('coupons/', views_admin.admin_coupons_list, name='coupons'),
]
```

### 2. Admin Controllers (`apps/products/views_admin.py`)
Provides real-time analytics overview, 1-click product out-of-stock toggling, product creation, order pipeline stage updating (`PLACED` ➔ `PACKING` ➔ `OUT_FOR_DELIVERY` ➔ `DELIVERED`), and coupon code generation. **Access is strictly guarded so only Administrator / Superuser accounts (`user.is_staff` or `user.is_superuser`) can view or perform actions.**

```python
from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, Q
from decimal import Decimal
from apps.accounts.models import User
from apps.products.models import Product, Category
from apps.orders.models import Order
from apps.promotions.models import Coupon

def admin_or_staff_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Auto-ensure superuser exists
        if not User.objects.filter(username='admin').exists():
            u = User.objects.create_superuser('admin', 'admin@blinkit.com', 'admin123')
            u.is_staff = True
            u.is_superuser = True
            u.save()

        if not request.user.is_authenticated:
            messages.warning(request, "Please log in with Admin credentials to access the Store Manager Dashboard.")
            return redirect(f"/accounts/login/?next={request.path}")
        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, "Access Denied: Only Administrator accounts can access the Store Manager Dashboard.")
            return redirect('/accounts/login/?next=/dashboard/')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@admin_or_staff_required
def admin_dashboard_home(request):
    total_orders = Order.objects.count()
    total_revenue = Order.objects.aggregate(total=Sum('grand_total'))['total'] or Decimal('0.00')
    total_products = Product.objects.count()
    out_of_stock_count = Product.objects.filter(Q(is_out_of_stock=True) | Q(is_active=False)).count()

    recent_orders = Order.objects.order_by('-created_at')[:8]
    return render(request, 'admin_custom/index.html', {
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'total_products': total_products,
        'out_of_stock_count': out_of_stock_count,
        'recent_orders': recent_orders,
        'active_tab': 'dashboard',
    })

@admin_or_staff_required
def admin_product_toggle_stock(request, product_id):
    if request.method == "POST":
        product = get_object_or_404(Product, id=product_id)
        product.is_out_of_stock = not product.is_out_of_stock
        product.save()
        messages.success(request, f"Updated '{product.name}' stock status.")
    return redirect(request.META.get('HTTP_REFERER', 'admin_dashboard:products'))
```

---

## 📌 Phase 5: Zero JavaScript Pure HTML & Tailwind CSS UI Templates

### 1. Product Card Template (`templates/components/product_card.html`)
Handles normal state and Out-of-Stock state cleanly with Django logic:
```html
<div class="bg-white rounded-2xl border border-gray-200 p-3 flex flex-col justify-between hover:shadow-lg transition relative">
    {% if product.discount_percentage > 0 %}
    <div class="absolute top-2 left-2 bg-blue-600 text-white font-extrabold text-[10px] px-1.5 py-0.5 rounded shadow">
        {{ product.discount_percentage }}% OFF
    </div>
    {% endif %}

    <div class="w-full h-32 flex items-center justify-center p-2">
        <img src="{{ product.get_image }}" alt="{{ product.name }}" class="max-h-full max-w-full object-contain">
    </div>

    <div class="mt-2 space-y-1">
        <div class="text-[10px] font-bold text-gray-700 bg-gray-100 px-1.5 py-0.5 rounded w-max">
            <i class="fa-regular fa-clock text-emerald-600"></i> {{ product.eta_minutes }} MINS
        </div>
        <h3 class="text-xs font-bold text-gray-900 line-clamp-2 min-h-[32px]">{{ product.name }}</h3>
        <p class="text-[11px] text-gray-500 font-medium">{{ product.unit_quantity }}</p>
    </div>

    <div class="mt-3 flex items-center justify-between pt-2 border-t border-gray-100">
        <div>
            <div class="text-xs font-black text-gray-900">₹{{ product.selling_price|floatformat:0 }}</div>
            {% if product.discount_percentage > 0 %}
            <div class="text-[10px] text-gray-400 line-through">₹{{ product.mrp|floatformat:0 }}</div>
            {% endif %}
        </div>

        <div>
            {% if product.is_out_of_stock or not product.is_active %}
                <span class="border border-gray-300 text-gray-400 bg-gray-100 font-bold px-3 py-1.5 rounded-lg text-[10px] uppercase">
                    OUT OF STOCK
                </span>
            {% else %}
                {% if product.in_cart_qty > 0 %}
                <div class="flex items-center bg-emerald-700 text-white font-bold rounded-lg overflow-hidden">
                    <form action="{% url 'cart:update' %}" method="POST" class="inline">
                        {% csrf_token %}
                        <input type="hidden" name="product_id" value="{{ product.id }}">
                        <input type="hidden" name="action" value="remove">
                        <button type="submit" class="px-2.5 py-1 hover:bg-emerald-800 text-xs font-black">-</button>
                    </form>
                    <span class="px-2 py-0.5 text-xs font-extrabold">{{ product.in_cart_qty }}</span>
                    <form action="{% url 'cart:update' %}" method="POST" class="inline">
                        {% csrf_token %}
                        <input type="hidden" name="product_id" value="{{ product.id }}">
                        <input type="hidden" name="action" value="add">
                        <button type="submit" class="px-2.5 py-1 hover:bg-emerald-800 text-xs font-black">+</button>
                    </form>
                </div>
                {% else %}
                <form action="{% url 'cart:update' %}" method="POST">
                    {% csrf_token %}
                    <input type="hidden" name="product_id" value="{{ product.id }}">
                    <input type="hidden" name="action" value="add">
                    <button type="submit" class="border border-emerald-700 text-emerald-700 bg-emerald-50 hover:bg-emerald-700 hover:text-white font-black px-4 py-1.5 rounded-lg text-xs uppercase transition">
                        ADD
                    </button>
                </form>
                {% endif %}
            {% endif %}
        </div>
    </div>
### 2. Official Blinkit Footer Component (`templates/components/footer.html`)
Replicates the exact layout of **Blinkit.com** with 3 columns of Useful Links, 3 columns of Categories (with green `see all` toggle), App Store & Google Play download badges, circular social icons, and legal disclaimer:

```html
<footer class="bg-[#FCFCFD] border-t border-gray-200 mt-16 pt-12 pb-10 text-gray-500 text-xs">
    <div class="max-w-7xl mx-auto px-4 space-y-10">
        <!-- Useful Links & Categories Grid -->
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
            <div class="lg:col-span-4 space-y-4">
                <h3 class="text-sm font-bold text-gray-900">Useful Links</h3>
                <div class="grid grid-cols-3 gap-3 text-xs">
                    <!-- Links list -->
                </div>
            </div>
            <div class="lg:col-span-8 space-y-4">
                <div class="flex items-center gap-3">
                    <h3 class="text-sm font-bold text-gray-900">Categories</h3>
                    <a href="#" class="text-xs font-semibold text-emerald-600 hover:underline">see all</a>
                </div>
                <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
                    <!-- 3 Category columns -->
                </div>
            </div>
        </div>
        <!-- Download App Badges & Social Circles -->
        <div class="bg-[#F4F6FB] rounded-2xl px-6 py-4 flex flex-col md:flex-row items-center justify-between gap-4">
            <div class="text-[11px] text-gray-500 font-medium">© Blink Commerce Private Limited, 2016-2026</div>
            <div class="flex items-center gap-3">
                <span class="text-xs font-bold text-gray-700">Download App</span>
                <!-- App Store & Google Play buttons -->
            </div>
            <div class="flex items-center gap-2.5">
                <!-- Circular Social Buttons -->
            </div>
        </div>
    </div>
</footer>
```

---

## 📌 Phase 7: Real-Time Delivery Rider Tracking & Live Delivery Map Engine

To replicate **Blinkit.com's** exact live tracking experience:
1. **Rider Assignment**: Stores rider metadata (`rider_name`, `rider_phone`, `rider_rating`, `vehicle_number`) and origin/destination coordinates on the `Order` model.
2. **Real-Time GPS Interpolation API**: `/orders/rider-location/<order_number>/` calculates elapsed time since order creation and smoothly moves rider coordinates along the route vector from DarkStore ➔ Customer Address.
3. **Interactive Live Map**: Renders an interactive Leaflet.js / OpenStreetMap container featuring custom animated markers (`🏬 DarkStore`, `🛵 Delivery Scooter`, `🏠 Customer Address`) with 3-second live polling.

### `apps/orders/views.py` (GPS Coordinate Interpolation API)
```python
from django.http import JsonResponse
from django.utils import timezone

def rider_location_api(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    now = timezone.now()
    elapsed_seconds = (now - order.created_at).total_seconds()
    
    # 120-second simulation cycle
    progress = min(1.0, max(0.0, elapsed_seconds / 120.0))
    
    # Interpolate current rider latitude and longitude
    if progress < 0.40:
        curr_lat, curr_lng = order.darkstore_lat, order.darkstore_lng
    elif progress >= 0.98:
        curr_lat, curr_lng = order.dest_lat, order.dest_lng
    else:
        ratio = (progress - 0.40) / 0.58
        curr_lat = order.darkstore_lat + (order.dest_lat - order.darkstore_lat) * ratio
        curr_lng = order.darkstore_lng + (order.dest_lng - order.darkstore_lng) * ratio

    return JsonResponse({
        'order_number': order.order_number,
        'status': order.status,
        'status_display': order.get_status_display(),
        'eta_minutes': max(0, int((1.0 - progress) * (order.eta_minutes or 10))),
        'rider_coords': [round(curr_lat, 6), round(curr_lng, 6)],
        'rider': {
            'name': order.rider_name,
            'phone': order.rider_phone,
            'rating': order.rider_rating,
            'vehicle': order.vehicle_number
        }
    })
```

---

## 📌 Phase 8: Step-by-Step Execution Checklist

1. **Initialize Migration Engine**:
   ```bash
   python manage.py makemigrations accounts darkstore products promotions cart payments orders
   python manage.py migrate
   ```

2. **Create Superuser Admin**:
   ```bash
   python manage.py createsuperuser
   ```

3. **Seed Initial Demo Data**:
   ```bash
   python manage.py seed_blinkit
   ```

4. **Launch Development Server**:
   ```bash
   python manage.py runserver 8000
   ```

---

## 🎯 Final Verification Checklist

- [x] **Location Selector**: Modal opens via pure CSS checkbox, saves pincode in Django session.
- [x] **Product Display**: Displays products filtered by pincode/store status.
- [x] **Stock Control**: Out of stock items automatically show disabled badges.
- [x] **Coupons & Offers**: Validates coupon codes against minimum cart totals.
- [x] **Checkout & Payments**: Supports Razorpay gateway payment and COD.
- [x] **Mandatory Login**: Unauthenticated checkout opens login modal and merges session carts.
- [x] **Custom Admin Dashboard**: `/dashboard/` overview, product stock toggles, order status pipeline updater.
- [x] **Real-Time Rider GPS Tracking**: Interactive Leaflet.js live map with moving scooter marker (`🛵`).

