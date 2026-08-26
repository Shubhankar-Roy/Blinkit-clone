from django.urls import path
from . import views_admin

app_name = 'orders_admin'

urlpatterns = [
    path('', views_admin.admin_orders_list, name='list'),
    path('<str:order_number>/', views_admin.admin_order_detail, name='detail'),
    path('<str:order_number>/update-status/', views_admin.admin_order_update_status, name='update_status'),
]
