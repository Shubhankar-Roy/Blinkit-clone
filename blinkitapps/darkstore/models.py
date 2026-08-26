from django.db import models
from django.db.models import Sum


class DarkStore(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True, help_text="Unique Dark Store Identifier e.g. DS-BLR-01")
    address = models.TextField(help_text="Detailed physical address of micro-fulfillment center")
    city = models.CharField(max_length=50, default='Bengaluru')
    state = models.CharField(max_length=50, default='Karnataka')
    serviceable_pincodes = models.TextField(
        help_text="Comma-separated serviceable pincodes e.g. 560034, 560095, 560047, 560100"
    )
    avg_delivery_mins = models.IntegerField(default=10, help_text="Average delivery turnaround in minutes")
    is_active = models.BooleanField(default=True, help_text="Operational status (Open / Closed)")
    
    # Geolocation coordinates for routing simulation
    latitude = models.FloatField(default=12.9352, help_text="Store latitude coordinate")
    longitude = models.FloatField(default=77.6245, help_text="Store longitude coordinate")
    
    # Operational contacts
    contact_phone = models.CharField(max_length=20, default='+91 9876543210', blank=True)
    manager_name = models.CharField(max_length=100, default='Store Supervisor', blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = "Dark Store"
        verbose_name_plural = "Dark Stores"

    def is_pincode_serviceable(self, pincode):
        if not pincode:
            return False
        clean_pincode = str(pincode).strip()
        pincodes = [p.strip() for p in self.serviceable_pincodes.split(',') if p.strip()]
        return clean_pincode in pincodes

    @property
    def pincode_list(self):
        if not self.serviceable_pincodes:
            return []
        return [p.strip() for p in self.serviceable_pincodes.split(',') if p.strip()]

    @property
    def pincode_count(self):
        return len(self.pincode_list)

    @property
    def total_inventory_items(self):
        return self.inventories.count()

    @property
    def total_stock_units(self):
        return self.inventories.aggregate(total=Sum('stock_quantity'))['total'] or 0

    @property
    def low_stock_count(self):
        return self.inventories.filter(stock_quantity__gt=0, stock_quantity__lte=10, is_available=True).count()

    @property
    def out_of_stock_count(self):
        return self.inventories.filter(models.Q(stock_quantity=0) | models.Q(is_available=False)).count()

    @property
    def in_stock_count(self):
        return self.inventories.filter(stock_quantity__gt=10, is_available=True).count()

    def __str__(self):
        return f"{self.name} ({self.code}) - {self.city}"


class DarkStoreInventory(models.Model):
    dark_store = models.ForeignKey(DarkStore, on_delete=models.CASCADE, related_name='inventories')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='store_inventories')
    stock_quantity = models.PositiveIntegerField(default=50)
    is_available = models.BooleanField(default=True, help_text="Store-level product availability switch")
    low_stock_threshold = models.PositiveIntegerField(default=10, help_text="Quantity threshold for low stock alert")
    last_restocked_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('dark_store', 'product')
        ordering = ['dark_store', 'product__name']
        verbose_name = "Dark Store Inventory"
        verbose_name_plural = "Dark Store Inventories"

    @property
    def is_low_stock(self):
        return self.is_available and 0 < self.stock_quantity <= self.low_stock_threshold

    @property
    def is_out_of_stock(self):
        return not self.is_available or self.stock_quantity == 0

    def __str__(self):
        return f"{self.product.name} @ {self.dark_store.code}: {self.stock_quantity} units"
