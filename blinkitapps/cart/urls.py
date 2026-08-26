from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    path('', views.cart_detail_view, name='detail'),
    path('update/', views.update_cart, name='update'),
    path('set-tip/', views.set_tip_view, name='set_tip'),
    path('clear/', views.clear_cart_view, name='clear'),
]
