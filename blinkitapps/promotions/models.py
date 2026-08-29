from django.db import models
from django.utils import timezone
from decimal import Decimal


class Coupon(models.Model):
    DISCOUNT_TYPES = (
        ('FLAT', 'Flat Amount Discount (₹)'),
        ('PERCENTAGE', 'Percentage Discount (%)'),
    )

    code = models.CharField(max_length=20, unique=True, help_text="Promo coupon code e.g. WELCOME50")
    description = models.CharField(max_length=255, help_text="Promotional summary e.g. Flat ₹50 OFF on orders above ₹199")
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPES, default='FLAT')
    discount_value = models.DecimalField(max_digits=8, decimal_places=2, help_text="Flat amount in ₹ or percentage value")
    min_order_amount = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'), help_text="Minimum items subtotal required")
    max_discount_amount = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
        help_text="Maximum discount cap for percentage discounts (in ₹)"
    )
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    usage_limit = models.PositiveIntegerField(default=1000, help_text="Maximum times this coupon can be redeemed")
    times_used = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def is_valid_for_cart(self, cart_total):
        """
        Validates coupon against active dates, usage count, and minimum cart value.
        """
        now = timezone.now()
        if not self.is_active:
            return False, "This coupon is currently inactive."
        if now < self.valid_from:
            return False, "This coupon offer is not active yet."
        if now > self.valid_until:
            return False, "This coupon has expired."
        if self.times_used >= self.usage_limit:
            return False, "Coupon usage limit has been reached."
        if Decimal(str(cart_total)) < self.min_order_amount:
            return False, f"Minimum items subtotal of ₹{self.min_order_amount:.0f} required for this coupon."
        return True, "Valid coupon applied!"

    def calculate_discount(self, cart_total):
        """
        Calculates discount value based on flat amount or percentage.
        """
        total = Decimal(str(cart_total))
        if total <= Decimal('0.00'):
            return Decimal('0.00')

        if self.discount_type == 'FLAT':
            return min(self.discount_value, total)
        elif self.discount_type == 'PERCENTAGE':
            discount = (self.discount_value / Decimal('100.00')) * total
            if self.max_discount_amount:
                discount = min(discount, self.max_discount_amount)
            return min(discount, total)
        return Decimal('0.00')

    def __str__(self):
        return f"{self.code} - {self.description}"
