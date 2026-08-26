from django.urls import path
from . import views_admin

app_name = 'promotions_admin'

urlpatterns = [
    path('', views_admin.admin_coupons_list, name='list'),
    path('create/', views_admin.admin_coupon_create, name='create'),
    path('<int:coupon_id>/edit/', views_admin.admin_coupon_edit, name='edit'),
    path('<int:coupon_id>/toggle/', views_admin.admin_coupon_toggle, name='toggle'),
    path('<int:coupon_id>/delete/', views_admin.admin_coupon_delete, name='delete'),
]
