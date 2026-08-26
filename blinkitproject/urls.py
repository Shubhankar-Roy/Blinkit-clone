from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('blinkitapps.products.urls')),
    path('accounts/', include('blinkitapps.accounts.urls')),
    path('cart/', include('blinkitapps.cart.urls')),
    path('location/', include('blinkitapps.darkstore.urls')),
    path('promotions/', include('blinkitapps.promotions.urls')),
    path('orders/', include('blinkitapps.orders.urls')),
    path('dashboard/', include('blinkitapps.products.urls_admin')),
    path('dashboard/darkstore/', include('blinkitapps.darkstore.urls_admin')),
    path('dashboard/coupons/', include('blinkitapps.promotions.urls_admin')),
    path('dashboard/orders/', include('blinkitapps.orders.urls_admin')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT or (settings.BASE_DIR / 'static'))
