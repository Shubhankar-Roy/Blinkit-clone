from django.urls import path
from . import views_admin

app_name = 'admin_dashboard'

urlpatterns = [
    path('', views_admin.admin_dashboard_home, name='home'),
    path('products/', views_admin.admin_products_list, name='products'),
    path('products/add/', views_admin.admin_product_add, name='product_add'),
    path('products/<int:product_id>/edit/', views_admin.admin_product_edit, name='product_edit'),
    path('products/<int:product_id>/toggle-stock/', views_admin.admin_product_toggle_stock, name='product_toggle_stock'),
    path('products/<int:product_id>/delete/', views_admin.admin_product_delete, name='product_delete'),
]
