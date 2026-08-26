from django.db import models
from django.conf import settings
from blinkitapps.products.models import Product
from blinkitapps.darkstore.models import DarkStore
from decimal import Decimal
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
        ('RAZORPAY', 'Online Payment (Razorpay / UPI / Cards)'),
    )

    PAYMENT_STATUS_CHOICES = (
        ('PENDING', 'Pending Payment'),
        ('SUCCESS', 'Paid Successfully'),
        ('FAILED', 'Payment Failed'),
    )

    order_number = models.CharField(max_length=25, unique=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    dark_store = models.ForeignKey(DarkStore, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    
    delivery_address = models.TextField(help_text="Full street address and landmark for delivery")
    pincode = models.CharField(max_length=10)
    phone = models.CharField(max_length=15)
    
    items_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    coupon_discount = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    delivery_fee = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    handling_fee = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('4.00'))
    tip_amount = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    grand_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='COD')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='PENDING')
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)
    
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='PLACED')
    eta_minutes = models.IntegerField(default=10)
    
    # Phase 7: Real-Time Delivery Rider Details & GPS Coordinates
    rider_name = models.CharField(max_length=100, default='Ramesh Kumar')
    rider_phone = models.CharField(max_length=20, default='+91 98765 43210')
    rider_rating = models.DecimalField(max_digits=3, decimal_places=1, default=Decimal('4.9'))
    vehicle_number = models.CharField(max_length=20, default='KA-01-EQ-9872')
    
    darkstore_lat = models.FloatField(default=12.9352)
    darkstore_lng = models.FloatField(default=77.6245)
    dest_lat = models.FloatField(default=12.9390)
    dest_lng = models.FloatField(default=77.6290)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Order"
        verbose_name_plural = "Orders & Deliveries"

    @property
    def delivery_partner_name(self):
        return self.rider_name

    @property
    def delivery_partner_phone(self):
        return self.rider_phone

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f"BLK-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    @property
    def total_item_count(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def tracking_step(self):
        """
        Returns numeric stage 1 to 4 for progress tracking.
        """
        mapping = {
            'PLACED': 1,
            'PACKING': 2,
            'OUT_FOR_DELIVERY': 3,
            'DELIVERED': 4,
            'CANCELLED': 0,
        }
        return mapping.get(self.status, 1)

    def __str__(self):
        return f"Order #{self.order_number} ({self.status}) - ₹{self.grand_total}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    product_name = models.CharField(max_length=200)
    unit_quantity = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ['id']
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"

    def __str__(self):
        return f"{self.quantity} x {self.product_name} in Order #{self.order.order_number}"
