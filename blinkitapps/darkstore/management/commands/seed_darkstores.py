from django.core.management.base import BaseCommand
from blinkitapps.darkstore.models import DarkStore, DarkStoreInventory
from blinkitapps.products.models import Product, Category, SubCategory


class Command(BaseCommand):
    help = 'Seeds initial Dark Stores and connects product inventories with realistic stock'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE("Seeding Dark Stores & Location Coverage Engine..."))

        # Seed realistic products if none or few exist
        if Product.objects.count() < 4:
            dairy_cat, _ = Category.objects.get_or_create(
                name="Dairy, Bread & Eggs",
                defaults={'icon_url': 'https://cdn-icons-png.flaticon.com/512/3081/3081986.png', 'is_popular': True, 'display_order': 1}
            )
            fruits_cat, _ = Category.objects.get_or_create(
                name="Fruits & Vegetables",
                defaults={'icon_url': 'https://cdn-icons-png.flaticon.com/512/1625/1625048.png', 'is_popular': True, 'display_order': 2}
            )
            snacks_cat, _ = Category.objects.get_or_create(
                name="Snacks & Munchies",
                defaults={'icon_url': 'https://cdn-icons-png.flaticon.com/512/2553/2553691.png', 'is_popular': True, 'display_order': 3}
            )
            beverages_cat, _ = Category.objects.get_or_create(
                name="Cold Drinks & Juices",
                defaults={'icon_url': 'https://cdn-icons-png.flaticon.com/512/2405/2405479.png', 'is_popular': True, 'display_order': 4}
            )

            milk_sub, _ = SubCategory.objects.get_or_create(category=dairy_cat, name="Milk")
            bread_sub, _ = SubCategory.objects.get_or_create(category=dairy_cat, name="Bread & Pav")
            chips_sub, _ = SubCategory.objects.get_or_create(category=snacks_cat, name="Chips & Crisps")
            juice_sub, _ = SubCategory.objects.get_or_create(category=beverages_cat, name="Fresh Juices")

            sample_products = [
                {
                    'name': 'Amul Taaza Homogenised Toned Milk',
                    'category': dairy_cat,
                    'subcategory': milk_sub,
                    'unit_quantity': '500 ml',
                    'mrp': 28.00,
                    'selling_price': 27.00,
                    'image_url': 'https://images.unsplash.com/photo-1550583724-b2692b85b150?w=500&auto=format&fit=crop&q=60',
                    'description': 'Pure fresh toned milk rich in calcium and protein.',
                    'is_trending': True,
                    'is_bestseller': True,
                    'eta_minutes': 8,
                },
                {
                    'name': 'Modern Classic White Bread',
                    'category': dairy_cat,
                    'subcategory': bread_sub,
                    'unit_quantity': '400 g',
                    'mrp': 45.00,
                    'selling_price': 40.00,
                    'image_url': 'https://images.unsplash.com/photo-1509440159596-0249088772ff?w=500&auto=format&fit=crop&q=60',
                    'description': 'Soft and fresh everyday white sliced bread.',
                    'is_trending': False,
                    'is_bestseller': True,
                    'eta_minutes': 8,
                },
                {
                    'name': 'Lay\'s India\'s Magic Masala Potato Chips',
                    'category': snacks_cat,
                    'subcategory': chips_sub,
                    'unit_quantity': '50 g',
                    'mrp': 20.00,
                    'selling_price': 20.00,
                    'image_url': 'https://images.unsplash.com/photo-1566478989037-eec170784d0b?w=500&auto=format&fit=crop&q=60',
                    'description': 'Crispy golden potato chips with spicy Indian magic masala.',
                    'is_trending': True,
                    'is_bestseller': True,
                    'eta_minutes': 10,
                },
                {
                    'name': 'Real Fruit Power Mixed Fruit Juice',
                    'category': beverages_cat,
                    'subcategory': juice_sub,
                    'unit_quantity': '1 L',
                    'mrp': 130.00,
                    'selling_price': 115.00,
                    'image_url': 'https://images.unsplash.com/photo-1613478223719-2ab802602423?w=500&auto=format&fit=crop&q=60',
                    'description': 'Loaded with delicious wholesome goodness of 9 handpicked fruits.',
                    'is_trending': True,
                    'is_bestseller': False,
                    'eta_minutes': 9,
                },
                {
                    'name': 'Fresh Organic Bananas (Robusta)',
                    'category': fruits_cat,
                    'subcategory': None,
                    'unit_quantity': '500 g (3-4 pcs)',
                    'mrp': 35.00,
                    'selling_price': 29.00,
                    'image_url': 'https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?w=500&auto=format&fit=crop&q=60',
                    'description': 'Naturally ripened fresh Robusta bananas sourced directly from farms.',
                    'is_trending': True,
                    'is_bestseller': True,
                    'eta_minutes': 8,
                },
            ]

            for p_data in sample_products:
                Product.objects.get_or_create(
                    name=p_data['name'],
                    defaults=p_data
                )
            self.stdout.write(self.style.SUCCESS(f"Populated baseline product catalog."))

        # Define Dark Store Hubs
        dark_stores_data = [
            {
                'name': 'Koramangala Dark Hub #01',
                'code': 'DS-BLR-01',
                'address': '80 Feet Road, 4th Block, Koramangala, Bengaluru',
                'city': 'Bengaluru',
                'state': 'Karnataka',
                'serviceable_pincodes': '560034, 560095, 560047, 560030',
                'avg_delivery_mins': 8,
                'is_active': True,
                'latitude': 12.9352,
                'longitude': 77.6245,
                'contact_phone': '+91 9880123456',
                'manager_name': 'Ramesh Kumar',
            },
            {
                'name': 'Indiranagar Express Hub #02',
                'code': 'DS-BLR-02',
                'address': '100 Feet Road, HAL 2nd Stage, Indiranagar, Bengaluru',
                'city': 'Bengaluru',
                'state': 'Karnataka',
                'serviceable_pincodes': '560038, 560008, 560075, 560001',
                'avg_delivery_mins': 9,
                'is_active': True,
                'latitude': 12.9719,
                'longitude': 77.6412,
                'contact_phone': '+91 9880123457',
                'manager_name': 'Priya Sharma',
            },
            {
                'name': 'HSR Layout Mega Store #03',
                'code': 'DS-BLR-03',
                'address': '27th Main Road, Sector 1, HSR Layout, Bengaluru',
                'city': 'Bengaluru',
                'state': 'Karnataka',
                'serviceable_pincodes': '560102, 560068, 560103, 560100',
                'avg_delivery_mins': 10,
                'is_active': True,
                'latitude': 12.9121,
                'longitude': 77.6446,
                'contact_phone': '+91 9880123458',
                'manager_name': 'Anand Verma',
            },
            {
                'name': 'Whitefield Tech Hub #04',
                'code': 'DS-BLR-04',
                'address': 'ITPL Main Road, Pattandur Agrahara, Whitefield, Bengaluru',
                'city': 'Bengaluru',
                'state': 'Karnataka',
                'serviceable_pincodes': '560066, 560087, 560067, 560048',
                'avg_delivery_mins': 12,
                'is_active': True,
                'latitude': 12.9698,
                'longitude': 77.7500,
                'contact_phone': '+91 9880123459',
                'manager_name': 'Vikram Singh',
            },
            {
                'name': 'Jayanagar Central Hub #05',
                'code': 'DS-BLR-05',
                'address': '11th Main Road, 4th T Block, Jayanagar, Bengaluru',
                'city': 'Bengaluru',
                'state': 'Karnataka',
                'serviceable_pincodes': '560011, 560041, 560070, 560076',
                'avg_delivery_mins': 10,
                'is_active': True,
                'latitude': 12.9250,
                'longitude': 77.5938,
                'contact_phone': '+91 9880123460',
                'manager_name': 'Deepak Hegde',
            },
        ]

        products = list(Product.objects.all())

        for store_data in dark_stores_data:
            store, created = DarkStore.objects.update_or_create(
                code=store_data['code'],
                defaults=store_data
            )
            action_text = "Created" if created else "Updated"
            self.stdout.write(f"  - {action_text} Dark Store: {store.name} ({store.code})")

            # Link all products to this dark store inventory
            for idx, prod in enumerate(products):
                # Add realistic variation in stock
                base_qty = 45 + ((idx * 7) % 35)
                # Let 1 item have low stock for demonstration
                if idx == 2 and store.code == 'DS-BLR-01':
                    base_qty = 4
                
                DarkStoreInventory.objects.update_or_create(
                    dark_store=store,
                    product=prod,
                    defaults={
                        'stock_quantity': base_qty,
                        'is_available': True,
                        'low_stock_threshold': 10,
                    }
                )

        self.stdout.write(self.style.SUCCESS("Successfully seeded Dark Stores and Inventory Engine!"))
