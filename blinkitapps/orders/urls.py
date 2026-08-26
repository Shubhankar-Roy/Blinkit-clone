from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('', views.order_history_view, name='history'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('payment-verify/', views.razorpay_payment_verify, name='payment_verify'),
    path('track/<str:order_number>/', views.order_tracking_view, name='track'),
    path('invoice/<str:order_number>/', views.order_invoice_view, name='invoice'),
    path('cancel/<str:order_number>/', views.cancel_order_view, name='cancel'),
    path('api/status/<str:order_number>/', views.order_status_api, name='status_api'),
    path('rider-location/<str:order_number>/', views.rider_location_api, name='rider_location_api'),
    path('<str:order_number>/reorder/', views.reorder_view, name='reorder'),
]
