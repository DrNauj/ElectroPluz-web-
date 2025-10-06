from django.urls import path
from . import views
from . import views_auth

urlpatterns = [
    # Home y catálogo
    path('', views.home, name='home'),
    path('catalog/', views.home, name='catalog'),  # Mismo view que home por ahora
    path('category/<slug:slug>/', views.category_products, name='category_products'),
    
    # Autenticación
    path('login/', views_auth.login_view, name='login'),
    path('logout/', views_auth.logout_view, name='logout'),
    path('register/', views_auth.register_view, name='register'),
    # path('password-reset/', views_auth.password_reset_view, name='password_reset'),  # Pendiente
    
    # Dashboards
    path('dashboard/', views_auth.dashboard_view, name='dashboard'),
    path('dashboard/admin/', views_auth.admin_dashboard, name='admin_dashboard'),
    path('dashboard/employee/', views_auth.employee_dashboard, name='employee_dashboard'),
    path('dashboard/customer/', views_auth.customer_dashboard, name='customer_dashboard'),
    
    # API endpoints
    path('api/productos/', views.ProductosAPIView.as_view(), name='api_productos'),
    path('api/ventas/', views.VentasAPIView.as_view(), name='api_ventas'),
    path('api/check-auth/', views.check_auth, name='check_auth'),
    
    # Carrito y perfil
    path('cart/', views.cart_view, name='cart'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('profile/', views.profile_view, name='profile'),
]