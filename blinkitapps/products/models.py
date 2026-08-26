from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    icon_url = models.URLField(blank=True, null=True)
    is_popular = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)

    class Meta:
        ordering = ['display_order', 'name']
        verbose_name_plural = "Categories"

    def get_image(self):
        if self.image:
            return self.image.url
        if self.icon_url:
            return self.icon_url
        return '/static/images/default.svg'

    def __str__(self):
        return self.name

class SubCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ['name']
        verbose_name_plural = "Sub Categories"

    def __str__(self):
        return f"{self.category.name} -> {self.name}"

class Product(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    subcategory = models.ForeignKey(SubCategory, on_delete=models.CASCADE, null=True, blank=True)
    unit_quantity = models.CharField(max_length=50)
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

    class Meta:
        ordering = ['name']

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
        return '/static/images/default.svg'

    def __str__(self):
        return self.name
