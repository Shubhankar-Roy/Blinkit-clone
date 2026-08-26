from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'full_name', 'phone_number', 'email', 'is_staff', 'is_active')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Blinkit Profile', {'fields': ('phone_number', 'full_name')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Blinkit Profile', {'fields': ('phone_number', 'full_name')}),
    )
