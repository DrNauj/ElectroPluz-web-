from django.urls import path
from . import views
from .reports_views import reports

app_name = 'dashboard'

urlpatterns = [
    # Dashboard principal
    path('', views.dashboard_home, name='home'),
    
    # Productos
    path('productos/', views.product_list, name='product_list'),
    path('productos/crear/', views.product_create, name='product_create'),
    path('productos/<int:pk>/editar/', views.product_edit, name='product_edit'),
    path('productos/<int:pk>/eliminar/', views.product_delete, name='product_delete'),
    
    # Categorías 
    path('categorias/', views.category_list, name='category_list'),
    path('categorias/crear/', views.category_create, name='category_create'),
    path('categorias/<int:pk>/editar/', views.category_edit, name='category_edit'),
    path('categorias/<int:pk>/eliminar/', views.category_delete, name='category_delete'),
    
    # Pedidos
    path('pedidos/', views.order_list, name='order_list'),
    path('pedidos/<int:pk>/', views.order_detail, name='order_detail'),
    path('pedidos/<int:pk>/actualizar-estado/', views.order_update_status, name='order_update_status'),
    
    # Reclamos
    path('reclamos/', views.claims_list, name='claims_list'),
    path('reclamos/<int:pk>/', views.claim_detail, name='claim_detail'),
    path('reclamos/<int:pk>/actualizar-estado/', views.claims_update_status, name='claims_update_status'),
    
    # Reportes
    path('reportes/', reports, name='reports'),
    
    # Inventario
    path('inventario/', views.inventory_list, name='inventory_list'),
    path('inventario/crear/', views.inventory_create, name='inventory_create'),
    path('inventario/actualizar/', views.inventory_update, name='inventory_update'),
    path('inventario/<int:pk>/', views.inventory_detail, name='inventory_detail'),
    path('inventario/<int:pk>/editar/', views.inventory_edit, name='inventory_edit'),
    
    # Clientes
    path('clientes/', views.customer_list, name='customer_list'),
    path('clientes/<int:pk>/', views.customer_detail, name='customer_detail'),
    
    # Usuarios Staff
    path('usuarios/', views.staff_list, name='staff_list'),
    path('usuarios/crear/', views.staff_create, name='staff_create'),
    path('usuarios/<int:pk>/editar/', views.staff_edit, name='staff_edit'),
    
    # Finanzas
    path('finanzas/', views.finances, name='finances'),
    path('finanzas/presupuesto/', views.budget_manage, name='budget_manage'),
    path('finanzas/transaccion/', views.transaction_add, name='transaction_add'),
]