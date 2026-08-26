from django.urls import path
from . import views

app_name = 'darkstore'

urlpatterns = [
    path('set-location/', views.set_location_view, name='set_location'),
    path('api/check-pincode/', views.check_pincode_api, name='check_pincode_api'),
    path('api/popular-locations/', views.get_popular_locations_api, name='popular_locations_api'),
]
