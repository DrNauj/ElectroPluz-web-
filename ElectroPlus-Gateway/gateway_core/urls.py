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
    # CRÍTICO: Se añade el namespace 'dashboard' aquí para que las redirecciones funcionen (e.g., redirect('dashboard:inventory:list_products'))
    path('dashboard/', include(([
        path('', gateway_views.dashboard, name='dashboard'),  # Vista principal del dashboard (inventario/ventas)
        path('inventory/', include('inventory.urls')),  # Submódulos del inventario
    ], 'dashboard'), namespace='dashboard')), 
    
    # Rutas de autenticación (login, register, logout, APIs, customer-dashboard)
    path('auth/', include('gateway_app.urls')),
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
