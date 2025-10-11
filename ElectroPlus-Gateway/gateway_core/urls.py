"""
URL configuration for gateway_core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from gateway_app import views as gateway_views # Importación de vistas del gateway

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('storefront.urls')),
    
    # Dashboard y sus submódulos
    path('dashboard/', include([
        path('', gateway_views.dashboard, name='dashboard'),  # Vista principal del dashboard
        path('inventory/', include('inventory.urls')),  # Submódulos del inventario
    ])),
    
    path('auth/', include('gateway_app.urls')),  # Para autenticación y funcionalidades base
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
