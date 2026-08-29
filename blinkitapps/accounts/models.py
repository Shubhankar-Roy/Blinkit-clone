from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class User(AbstractUser):
    phone_number = models.CharField(max_length=15, unique=True, null=True, blank=True)
    full_name = models.CharField(max_length=150, blank=True, null=True)

    @property
    def display_name(self):
        if self.full_name:
            return self.full_name
        if self.phone_number:
            return f"+91 {self.phone_number}"
        return self.username

    def __str__(self):
        return self.display_name


class Address(models.Model):
    ADDRESS_TYPES = (
        ('Home', 'Home'),
        ('Work', 'Work'),
        ('Other', 'Other'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    house_flat_no = models.CharField(max_length=100)
    area_street = models.TextField()
    landmark = models.CharField(max_length=150, blank=True, null=True)
    pincode = models.CharField(max_length=10)
    city = models.CharField(max_length=50, default='Bengaluru')
    address_type = models.CharField(max_length=10, choices=ADDRESS_TYPES, default='Home')
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_default', '-created_at']

    @property
    def street_address(self):
        return f"{self.house_flat_no}, {self.area_street}"

    def save(self, *args, **kwargs):
        if self.is_default:
            Address.objects.filter(user=self.user).exclude(id=self.id).update(is_default=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.house_flat_no}, {self.area_street}, {self.city} - {self.pincode}"
