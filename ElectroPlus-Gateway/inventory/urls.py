from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.dashboard_home, name='dashboard_home'),
    path('products/', views.product_management, name='product_management'),
    path('products/import/', views.product_import, name='product_import'),
    path('orders/', views.order_list, name='order_list'),
    path('api/products/', views.product_list_create, name='product_list_create'),
    path('api/products/<int:pk>/', views.product_detail, name='product_detail'),
    path('api/products/import/', views.product_import, name='product_import'),
]