from django.db import models
from django.conf import settings
from blinkitapps.products.models import Product
from decimal import Decimal


class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=100, null=True, blank=True)
    coupon = models.ForeignKey('promotions.Coupon', on_delete=models.SET_NULL, null=True, blank=True)
    tip_amount = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'), help_text="Delivery partner tip amount in ₹")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    @property
    def total_mrp(self):
        return sum(item.mrp_subtotal for item in self.items.all()) or Decimal('0.00')

    @property
    def items_subtotal(self):
        return sum(item.subtotal for item in self.items.all()) or Decimal('0.00')

    @property
    def coupon_discount(self):
        if self.coupon and self.item_count > 0:
            is_valid, _ = self.coupon.is_valid_for_cart(self.items_subtotal)
            if is_valid:
                return self.coupon.calculate_discount(self.items_subtotal)
        return Decimal('0.00')

    @property
    def delivery_fee(self):
        # Free delivery above ₹199
        if self.items_subtotal >= Decimal('199.00') or self.item_count == 0:
            return Decimal('0.00')
        return Decimal('25.00')

    @property
    def handling_fee(self):
        return Decimal('4.00') if self.item_count > 0 else Decimal('0.00')

    @property
    def grand_total(self):
        if self.item_count == 0:
            return Decimal('0.00')
        total = self.items_subtotal - self.coupon_discount + self.delivery_fee + self.handling_fee + self.tip_amount
        return max(Decimal('0.00'), total)

    @property
    def total_savings(self):
        catalog_savings = Decimal('0.00')
        if self.total_mrp > self.items_subtotal:
            catalog_savings = self.total_mrp - self.items_subtotal
        return catalog_savings + self.coupon_discount

    @property
    def item_count(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def amount_needed_for_free_delivery(self):
        if self.items_subtotal < Decimal('199.00'):
            return Decimal('199.00') - self.items_subtotal
        return Decimal('0.00')

    @property
    def free_delivery_progress_percentage(self):
        if self.items_subtotal <= Decimal('0.00'):
            return 0
        progress = int((self.items_subtotal / Decimal('199.00')) * 100)
        return min(100, max(0, progress))

    def __str__(self):
        owner = self.user.username if self.user else f"Guest ({self.session_id})"
        return f"Cart #{self.id} for {owner} ({self.item_count} items)"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('cart', 'product')
        ordering = ['id']

    @property
    def subtotal(self):
        return self.product.selling_price * self.quantity

    @property
    def mrp_subtotal(self):
        return self.product.mrp * self.quantity

    @property
    def item_savings(self):
        if self.mrp_subtotal > self.subtotal:
            return self.mrp_subtotal - self.subtotal
        return Decimal('0.00')

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in Cart #{self.cart_id}"
