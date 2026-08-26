from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from blinkitapps.promotions.models import Coupon


class Command(BaseCommand):
    help = 'Seeds initial promo coupons for Blinkit clone'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE("Seeding promotional coupons and offers..."))

        now = timezone.now()
        future_date = now + timedelta(days=90)

        coupons_data = [
            {
                'code': 'WELCOME50',
                'description': 'Flat ₹50 OFF on orders above ₹199',
                'discount_type': 'FLAT',
                'discount_value': Decimal('50.00'),
                'min_order_amount': Decimal('199.00'),
                'valid_from': now,
                'valid_until': future_date,
                'is_active': True,
                'usage_limit': 10000,
            },
            {
                'code': 'BLINKIT20',
                'description': '20% OFF up to ₹100 on orders above ₹149',
                'discount_type': 'PERCENTAGE',
                'discount_value': Decimal('20.00'),
                'min_order_amount': Decimal('149.00'),
                'max_discount_amount': Decimal('100.00'),
                'valid_from': now,
                'valid_until': future_date,
                'is_active': True,
                'usage_limit': 10000,
            },
            {
                'code': 'SUPER100',
                'description': 'Flat ₹100 OFF on mega grocery orders above ₹499',
                'discount_type': 'FLAT',
                'discount_value': Decimal('100.00'),
                'min_order_amount': Decimal('499.00'),
                'valid_from': now,
                'valid_until': future_date,
                'is_active': True,
                'usage_limit': 5000,
            },
            {
                'code': 'FESTIVE25',
                'description': 'Festive Special: 25% OFF up to ₹150 on orders above ₹299',
                'discount_type': 'PERCENTAGE',
                'discount_value': Decimal('25.00'),
                'min_order_amount': Decimal('299.00'),
                'max_discount_amount': Decimal('150.00'),
                'valid_from': now,
                'valid_until': future_date,
                'is_active': True,
                'usage_limit': 5000,
            },
        ]

        for c_data in coupons_data:
            c, created = Coupon.objects.update_or_create(
                code=c_data['code'],
                defaults=c_data
            )
            action = "Created" if created else "Updated"
            self.stdout.write(f"  - {action} Coupon: {c.code}")

        self.stdout.write(self.style.SUCCESS("Successfully seeded promotional coupons!"))
