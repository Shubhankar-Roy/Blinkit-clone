from django.urls import path
from . import views

app_name = 'payment'

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('pay/<str:order_number>/', views.order_payment, name='order_payment'),
    path('paymenthandler/', views.paymenthandler, name='paymenthandler'),
]
