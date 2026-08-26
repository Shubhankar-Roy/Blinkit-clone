# 🛒 Blinkit Clone - 10-Minute Grocery Delivery Web Application

Welcome! This project is a production-ready **Blinkit Clone (Quick-Commerce 10-Minute Grocery Delivery Web App)** built with **Django 5.x**, **HTML5 Templates**, and **Tailwind CSS**.

---

## 🏗️ Core Architecture & Features

1. **Authentication & User Profile (`blinkitapps.accounts`)**:
   - Custom `User` with phone number and `Address` management (Home, Work, Other) with default address selector.
   - **Guest Cart Merging**: Unauthenticated users can browse and add items to a temporary session cart; upon login, carts are automatically merged into their database profile.

2. **Location & Dark Store Engine (`blinkitapps.darkstore`)**:
   - `DarkStore` & `DarkStoreInventory` models supporting multi-hub inventory.
   - `location_processor` providing location, active hub, and ETA across all templates.
   - Pincode and routing simulator at `/dashboard/darkstore/simulator/`.

3. **Product Catalog & Search Engine (`blinkitapps.products`)**:
   - `Category`, `SubCategory`, and `Product` models with unit indicators, dynamic discount percentages, and badges (*Trending*, *Bestseller*).
   - Multi-field search with category filters, low/high price sorting, discount sorting, and popularity sorting.

4. **Stock & Inventory Engine**:
   - Dark store stock quantity ceilings and zero-stock blocking in cart views and templates.
   - Automatic `OUT OF STOCK` badges on unavailable items.

5. **Cart & Dynamic Promotions Engine (`blinkitapps.cart`)**:
   - Slide-over cart drawer and full-page cart with dynamic bill recalculations.
   - Free delivery above ₹199 (₹25 standard fee), ₹4 handling fee, and 1-click delivery partner tipping (₹10, ₹20, ₹30, ₹50).

6. **Coupons & Offers Engine (`blinkitapps.promotions`)**:
   - `Coupon` model supporting Flat (₹) and Percentage (%) discounts with max caps, validity windows, and minimum cart thresholds.
   - Dedicated Admin Coupon Campaign Manager at `/dashboard/coupons/`.

7. **Payments & Checkout (`blinkitapps.orders`)**:
   - Cash on Delivery (COD) and Razorpay Gateway integration with callback verification.
   - Order price snapshotting and automatic warehouse stock decrements upon placement.

8. **Order Lifecycle & Real-Time Rider GPS Radar**:
   - **4-Stage Pipeline**: `PLACED` ➔ `PACKING` ➔ `OUT_FOR_DELIVERY` ➔ `DELIVERED`.
   - **Leaflet.js Live GPS Radar Map** (`/orders/track/<order_number>/`): Dynamic map with animated `🏬 DarkStore Hub`, `🛵 Moving Delivery Scooter` (smooth 3s GPS interpolation via `rider_location_api`), and `🏠 Destination Address`.
   - 1-click **Cancel Order** with automatic inventory restock and **Re-Order** shortcuts.
   - Printable **GST Tax Invoice** (`/orders/invoice/<order_number>/`).

9. **Dedicated Custom Admin & Merchant Portal (`/dashboard/`)**:
   - Master Operations Overview, Live Dispatch Queue, Merchant Product Catalog, 1-Click Stock Availability Switches, and Dark Store Fleet Manager.
   - Role-guarded with `@admin_or_staff_required`.

---

## 🚀 Quick Start (How to Run)

### 1. Create & Activate Virtual Environment
```bash
python -m venv venv
.\venv\Scripts\Activate.ps1   # On Windows PowerShell
# source venv/bin/activate    # On macOS/Linux
```

### 2. Install Required Dependencies
```bash
pip install -r requirements.txt
```

### 3. Apply Migrations
```bash
python manage.py migrate
```

### 4. Seed Comprehensive Demo Catalog & Dark Stores
```bash
python manage.py seed_blinkit
```

### 5. Start Development Server
```bash
python manage.py runserver
```

Open your browser at [http://127.0.0.1:8000/](http://127.0.0.1:8000/) to browse the store, or [http://127.0.0.1:8000/dashboard/](http://127.0.0.1:8000/dashboard/) for the Store Manager Dashboard!
