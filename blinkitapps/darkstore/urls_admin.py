from django.urls import path
from . import views_admin

app_name = 'darkstore_admin'

urlpatterns = [
    path('', views_admin.admin_darkstore_dashboard, name='dashboard'),
    path('stores/', views_admin.admin_darkstore_list, name='list'),
    path('stores/create/', views_admin.admin_darkstore_create, name='create'),
    path('stores/<int:store_id>/edit/', views_admin.admin_darkstore_edit, name='edit'),
    path('stores/<int:store_id>/toggle/', views_admin.admin_darkstore_toggle_status, name='toggle'),
    path('stores/<int:store_id>/delete/', views_admin.admin_darkstore_delete, name='delete'),
    path('stores/<int:store_id>/inventory/', views_admin.admin_darkstore_inventory, name='inventory'),
    path('inventory/<int:inventory_id>/update/', views_admin.admin_darkstore_stock_update, name='stock_update'),
    path('stores/<int:store_id>/bulk-restock/', views_admin.admin_darkstore_bulk_restock, name='bulk_restock'),
    path('simulator/', views_admin.admin_darkstore_simulator, name='simulator'),
    path('assign-pincode/', views_admin.admin_darkstore_quick_assign_pincode, name='assign_pincode'),
]
