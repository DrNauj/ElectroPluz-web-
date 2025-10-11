"""
URL configuration for gateway_core project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from gateway_app import views as gateway_views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Rutas públicas de la tienda (incluye catálogo, carrito, checkout, etc.)
    path('', include('storefront.urls')), 
    
    # Dashboard y sus submódulos
    path('dashboard/', include('inventory.urls', namespace='dashboard')),
    
    # Rutas de autenticación (login, register, logout, APIs, customer-dashboard)
    path('auth/', include('gateway_app.urls')),
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
