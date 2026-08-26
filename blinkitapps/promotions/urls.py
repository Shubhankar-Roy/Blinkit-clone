from django.urls import path
from . import views

app_name = 'promotions'

urlpatterns = [
    path('apply-coupon/', views.apply_coupon_view, name='apply_coupon'),
    path('remove-coupon/', views.remove_coupon_view, name='remove_coupon'),
    path('api/available-coupons/', views.available_coupons_api, name='available_coupons_api'),
]
