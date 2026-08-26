from django.core.management.base import BaseCommand
from blinkitapps.products.models import Category, SubCategory, Product
from blinkitapps.darkstore.models import DarkStore, DarkStoreInventory


class Command(BaseCommand):
    help = 'Seeds a full-featured Blinkit product catalog across multiple categories'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE("Populating comprehensive Blinkit product catalog..."))

        catalog_data = [
            {
                'category': 'Dairy, Bread & Eggs',
                'icon_url': 'https://cdn-icons-png.flaticon.com/512/3081/3081986.png',
                'is_popular': True,
                'display_order': 1,
                'subcategories': [
                    {
                        'name': 'Milk',
                        'products': [
                            {
                                'name': 'Amul Taaza Homogenised Toned Milk',
                                'unit_quantity': '500 ml',
                                'mrp': 28.00,
                                'selling_price': 27.00,
                                'image_url': 'https://images.unsplash.com/photo-1550583724-b2692b85b150?w=500&auto=format&fit=crop&q=60',
                                'description': 'Fresh pasteurised toned milk with 3.0% fat, rich in calcium and protein for everyday energy.',
                                'is_trending': True,
                                'is_bestseller': True,
                                'eta_minutes': 8,
                            },
                            {
                                'name': 'Nandini GoodLife UHT Toned Milk',
                                'unit_quantity': '1 L',
                                'mrp': 60.00,
                                'selling_price': 56.00,
                                'image_url': 'https://images.unsplash.com/photo-1563636619-e9143da7973b?w=500&auto=format&fit=crop&q=60',
                                'description': 'Long shelf life UHT treated milk, zero preservatives, 100% wholesome pure milk.',
                                'is_trending': False,
                                'is_bestseller': True,
                                'eta_minutes': 9,
                            },
                            {
                                'name': 'Amul Gold Full Cream Fresh Milk',
                                'unit_quantity': '500 ml',
                                'mrp': 34.00,
                                'selling_price': 33.00,
                                'image_url': 'https://images.unsplash.com/photo-1550583724-b2692b85b150?w=500&auto=format&fit=crop&q=60',
                                'description': 'Thick creamy milk ideal for desserts, tea, coffee, and homemade curd.',
                                'is_trending': True,
                                'is_bestseller': False,
                                'eta_minutes': 8,
                            }
                        ]
                    },
                    {
                        'name': 'Bread & Pav',
                        'products': [
                            {
                                'name': 'Modern Classic White Bread',
                                'unit_quantity': '400 g',
                                'mrp': 45.00,
                                'selling_price': 40.00,
                                'image_url': 'https://images.unsplash.com/photo-1509440159596-0249088772ff?w=500&auto=format&fit=crop&q=60',
                                'description': 'Soft and pillowy everyday sandwich bread, fortified with essential vitamins.',
                                'is_trending': False,
                                'is_bestseller': True,
                                'eta_minutes': 8,
                            },
                            {
                                'name': 'English Oven 100% Whole Wheat Brown Bread',
                                'unit_quantity': '400 g',
                                'mrp': 55.00,
                                'selling_price': 50.00,
                                'image_url': 'https://images.unsplash.com/photo-1549931319-a545dcf3bc73?w=500&auto=format&fit=crop&q=60',
                                'description': 'High fibre 100% whole wheat brown bread for health-conscious daily breakfast.',
                                'is_trending': True,
                                'is_bestseller': True,
                                'eta_minutes': 9,
                            }
                        ]
                    },
                    {
                        'name': 'Eggs & Paneer',
                        'products': [
                            {
                                'name': 'Farm Fresh White Eggs (Pack of 6)',
                                'unit_quantity': '6 pcs',
                                'mrp': 55.00,
                                'selling_price': 48.00,
                                'image_url': 'https://images.unsplash.com/photo-1582722872445-44dc5f7e3c8f?w=500&auto=format&fit=crop&q=60',
                                'description': 'Antibiotic-free clean fresh graded farm eggs packed with high-quality natural protein.',
                                'is_trending': True,
                                'is_bestseller': True,
                                'eta_minutes': 8,
                            },
                            {
                                'name': 'Amul Fresh Malai Paneer',
                                'unit_quantity': '200 g',
                                'mrp': 95.00,
                                'selling_price': 89.00,
                                'image_url': 'https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=500&auto=format&fit=crop&q=60',
                                'description': 'Soft and creamy traditional cottage cheese block, perfect for curries and snacks.',
                                'is_trending': True,
                                'is_bestseller': True,
                                'eta_minutes': 8,
                            }
                        ]
                    }
                ]
            },
            {
                'category': 'Fruits & Vegetables',
                'icon_url': 'https://cdn-icons-png.flaticon.com/512/1625/1625048.png',
                'is_popular': True,
                'display_order': 2,
                'subcategories': [
                    {
                        'name': 'Fresh Fruits',
                        'products': [
                            {
                                'name': 'Fresh Organic Bananas (Robusta)',
                                'unit_quantity': '500 g (3-4 pcs)',
                                'mrp': 35.00,
                                'selling_price': 29.00,
                                'image_url': 'https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?w=500&auto=format&fit=crop&q=60',
                                'description': 'Naturally ripened sweet bananas packed with potassium.',
                                'is_trending': True,
                                'is_bestseller': True,
                                'eta_minutes': 8,
                            },
                            {
                                'name': 'Shimla Royal Delicious Apples',
                                'unit_quantity': '4 pcs (approx 500g)',
                                'mrp': 160.00,
                                'selling_price': 135.00,
                                'image_url': 'https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?w=500&auto=format&fit=crop&q=60',
                                'description': 'Crisp, sweet and juicy red apples handpicked from Himachal orchards.',
                                'is_trending': False,
                                'is_bestseller': True,
                                'eta_minutes': 10,
                            }
                        ]
                    },
                    {
                        'name': 'Daily Vegetables',
                        'products': [
                            {
                                'name': 'Fresh Farm Red Hybrid Tomatoes',
                                'unit_quantity': '500 g',
                                'mrp': 30.00,
                                'selling_price': 22.00,
                                'image_url': 'https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=500&auto=format&fit=crop&q=60',
                                'description': 'Firm and tangy fresh tomatoes, farm picked every morning.',
                                'is_trending': True,
                                'is_bestseller': True,
                                'eta_minutes': 8,
                            },
                            {
                                'name': 'Fresh Farm Potatoes (Aloo)',
                                'unit_quantity': '1 kg',
                                'mrp': 45.00,
                                'selling_price': 34.00,
                                'image_url': 'https://images.unsplash.com/photo-1518977676601-b53f82aba655?w=500&auto=format&fit=crop&q=60',
                                'description': 'Standard cooking potatoes, clean and dirt-free.',
                                'is_trending': False,
                                'is_bestseller': True,
                                'eta_minutes': 8,
                            },
                            {
                                'name': 'Fresh Red Onions (Pyaaz)',
                                'unit_quantity': '1 kg',
                                'mrp': 50.00,
                                'selling_price': 39.00,
                                'image_url': 'https://images.unsplash.com/photo-1618512496248-a07fe83aa8cb?w=500&auto=format&fit=crop&q=60',
                                'description': 'Pungent and crisp red onions sourced directly from Nashik farms.',
                                'is_trending': True,
                                'is_bestseller': True,
                                'eta_minutes': 8,
                            }
                        ]
                    }
                ]
            },
            {
                'category': 'Snacks & Munchies',
                'icon_url': 'https://cdn-icons-png.flaticon.com/512/2553/2553691.png',
                'is_popular': True,
                'display_order': 3,
                'subcategories': [
                    {
                        'name': 'Chips & Crisps',
                        'products': [
                            {
                                'name': 'Lay\'s India\'s Magic Masala Potato Chips',
                                'unit_quantity': '50 g',
                                'mrp': 20.00,
                                'selling_price': 20.00,
                                'image_url': 'https://images.unsplash.com/photo-1566478989037-eec170784d0b?w=500&auto=format&fit=crop&q=60',
                                'description': 'Spicy ridges of crispy golden potato chips tossed in authentic Indian spices.',
                                'is_trending': True,
                                'is_bestseller': True,
                                'eta_minutes': 8,
                            },
                            {
                                'name': 'Kurkure Masala Munch Crunchy Snack',
                                'unit_quantity': '75 g',
                                'mrp': 20.00,
                                'selling_price': 20.00,
                                'image_url': 'https://images.unsplash.com/photo-1621447504864-d8686e12698c?w=500&auto=format&fit=crop&q=60',
                                'description': 'Irresistibly spicy, crunchy corn puff twists that deliver a burst of flavor.',
                                'is_trending': True,
                                'is_bestseller': True,
                                'eta_minutes': 8,
                            },
                            {
                                'name': 'Doritos Cheese Supreme Nachos',
                                'unit_quantity': '60 g',
                                'mrp': 35.00,
                                'selling_price': 30.00,
                                'image_url': 'https://images.unsplash.com/photo-1513456852971-30c0b8199d4d?w=500&auto=format&fit=crop&q=60',
                                'description': 'Crunchy corn tortilla triangle chips infused with intense savory cheese flavor.',
                                'is_trending': False,
                                'is_bestseller': False,
                                'eta_minutes': 10,
                            }
                        ]
                    },
                    {
                        'name': 'Biscuits & Cookies',
                        'products': [
                            {
                                'name': 'Oreo Original Vanilla Creme Sandwich Biscuits',
                                'unit_quantity': '120 g',
                                'mrp': 40.00,
                                'selling_price': 35.00,
                                'image_url': 'https://images.unsplash.com/photo-1558961363-fa8fdf82db35?w=500&auto=format&fit=crop&q=60',
                                'description': 'Rich dark cocoa biscuits sandwiched with smooth sweet vanilla cream.',
                                'is_trending': True,
                                'is_bestseller': True,
                                'eta_minutes': 8,
                            },
                            {
                                'name': 'Britannia Good Day Cashew Cookies',
                                'unit_quantity': '200 g',
                                'mrp': 50.00,
                                'selling_price': 42.00,
                                'image_url': 'https://images.unsplash.com/photo-1499636136210-6f4ee915583e?w=500&auto=format&fit=crop&q=60',
                                'description': 'Buttery crisp cookies loaded with real crunchy cashew nuts in every bite.',
                                'is_trending': False,
                                'is_bestseller': True,
                                'eta_minutes': 9,
                            }
                        ]
                    }
                ]
            },
            {
                'category': 'Cold Drinks & Juices',
                'icon_url': 'https://cdn-icons-png.flaticon.com/512/2405/2405479.png',
                'is_popular': True,
                'display_order': 4,
                'subcategories': [
                    {
                        'name': 'Soft Drinks',
                        'products': [
                            {
                                'name': 'Coca-Cola Original Soft Drink (Can)',
                                'unit_quantity': '300 ml',
                                'mrp': 40.00,
                                'selling_price': 38.00,
                                'image_url': 'https://images.unsplash.com/photo-1554866585-cd94860890b7?w=500&auto=format&fit=crop&q=60',
                                'description': 'Iconic chilled sparkling cola refreshment that uplifts every moment.',
                                'is_trending': True,
                                'is_bestseller': True,
                                'eta_minutes': 8,
                            },
                            {
                                'name': 'Sprite Lemon-Lime Sparkling Drink (Bottle)',
                                'unit_quantity': '750 ml',
                                'mrp': 45.00,
                                'selling_price': 40.00,
                                'image_url': 'https://images.unsplash.com/photo-1622483767028-3f66f32aef97?w=500&auto=format&fit=crop&q=60',
                                'description': 'Clear, crisp and refreshing sparkling lemon-lime drink with zero caffeine.',
                                'is_trending': False,
                                'is_bestseller': True,
                                'eta_minutes': 8,
                            }
                        ]
                    },
                    {
                        'name': 'Juices & Energy',
                        'products': [
                            {
                                'name': 'Real Fruit Power Mixed Fruit Juice',
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
                                'name': 'Red Bull Energy Drink',
                                'unit_quantity': '250 ml',
                                'mrp': 125.00,
                                'selling_price': 120.00,
                                'image_url': 'https://images.unsplash.com/photo-1527661591475-527312dd65f5?w=500&auto=format&fit=crop&q=60',
                                'description': 'Vitalizes body and mind with high-grade caffeine, taurine, and B-group vitamins.',
                                'is_trending': True,
                                'is_bestseller': False,
                                'eta_minutes': 8,
                            }
                        ]
                    }
                ]
            },
            {
                'category': 'Instant & Frozen Food',
                'icon_url': 'https://cdn-icons-png.flaticon.com/512/1046/1046751.png',
                'is_popular': True,
                'display_order': 5,
                'subcategories': [
                    {
                        'name': 'Noodles & Pasta',
                        'products': [
                            {
                                'name': 'Maggi 2-Minute Masala Instant Noodles',
                                'unit_quantity': '70 g (Pack of 4)',
                                'mrp': 60.00,
                                'selling_price': 54.00,
                                'image_url': 'https://images.unsplash.com/photo-1612927601601-6638404737ce?w=500&auto=format&fit=crop&q=60',
                                'description': 'India\'s favorite comfort snack with authentic aromatic blend of 20 spices and herbs.',
                                'is_trending': True,
                                'is_bestseller': True,
                                'eta_minutes': 8,
                            }
                        ]
                    }
                ]
            }
        ]

        total_prods = 0
        all_created_products = []

        for cat_info in catalog_data:
            cat, _ = Category.objects.update_or_create(
                name=cat_info['category'],
                defaults={
                    'icon_url': cat_info['icon_url'],
                    'is_popular': cat_info['is_popular'],
                    'display_order': cat_info['display_order'],
                }
            )

            for sub_info in cat_info.get('subcategories', []):
                sub, _ = SubCategory.objects.update_or_create(
                    category=cat,
                    name=sub_info['name']
                )

                for prod_info in sub_info.get('products', []):
                    prod, _ = Product.objects.update_or_create(
                        name=prod_info['name'],
                        defaults={
                            'category': cat,
                            'subcategory': sub,
                            'unit_quantity': prod_info['unit_quantity'],
                            'mrp': prod_info['mrp'],
                            'selling_price': prod_info['selling_price'],
                            'image_url': prod_info['image_url'],
                            'description': prod_info['description'],
                            'is_active': True,
                            'is_out_of_stock': False,
                            'is_trending': prod_info.get('is_trending', False),
                            'is_bestseller': prod_info.get('is_bestseller', False),
                            'eta_minutes': prod_info.get('eta_minutes', 8),
                        }
                    )
                    all_created_products.append(prod)
                    total_prods += 1

        self.stdout.write(self.style.SUCCESS(f"Populated {total_prods} products across categories."))

        # Link all products into DarkStoreInventory for all dark stores
        dark_stores = DarkStore.objects.all()
        for store in dark_stores:
            for idx, prod in enumerate(all_created_products):
                # Set realistic inventory quantities
                qty = 40 + ((idx * 11) % 45)
                # Let one item be out of stock in DS-BLR-02 for demonstration
                if store.code == 'DS-BLR-02' and idx == 4:
                    qty = 0

                DarkStoreInventory.objects.update_or_create(
                    dark_store=store,
                    product=prod,
                    defaults={
                        'stock_quantity': qty,
                        'is_available': True if qty > 0 else False,
                        'low_stock_threshold': 10,
                    }
                )

        self.stdout.write(self.style.SUCCESS(f"Synchronized inventories across {dark_stores.count()} dark stores!"))
