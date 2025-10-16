"""
URL configuration for ElectroPlus_Gateway_New project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

def home(request):
    """
    Vista principal que redirige a:
    - Tienda para usuarios no autenticados o clientes
    - Dashboard para staff, pero solo si acceden específicamente a /dashboard/
    """
    return redirect('storefront:product_list')

urlpatterns = [
    path('', home, name='home'),
    path('admin/', admin.site.urls),
    path('tienda/', include('storefront.urls', namespace='storefront')),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('dashboard/', include('dashboard.urls', namespace='dashboard')),
]

# URL de login para usar en los templates
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'home'
