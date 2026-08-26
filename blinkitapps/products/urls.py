from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('category/', views.all_categories_view, name='all_categories'),
    path('category/<int:id>/', views.category_view, name='category_list'),
    path('product/<int:id>/', views.product_detail_view, name='detail'),
    path('search/', views.search_view, name='search'),
]
