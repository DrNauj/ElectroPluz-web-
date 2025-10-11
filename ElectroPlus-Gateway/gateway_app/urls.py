from django.urls import path
# IMPORTANTE: Cambiamos la importación de views_auth a views
from . import views 

# app_name se usa para referenciar las rutas dentro de las plantillas (ej: {% url 'auth:login' %})
app_name = 'auth'

urlpatterns = [
    # ----------------------------------------------------
    # Vistas de Autenticación (Formularios para el usuario)
    # ----------------------------------------------------
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'), # Añadida la ruta de registro
    
    # ----------------------------------------------------
    # Vistas de Dashboards (Requieren login_required)
    # ----------------------------------------------------
    # Ruta principal después de loguearse (redirige según el rol)
    path('dashboard/', views.dashboard_view, name='dashboard'), 
    
    # Rutas específicas del dashboard
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/employee/', views.employee_dashboard, name='employee_dashboard'),
    path('dashboard/customer/', views.customer_dashboard, name='customer_dashboard'),
    
    # ----------------------------------------------------
    # API Endpoints (Para comunicación AJAX/Microservicios)
    # ----------------------------------------------------
    path('api/login/', views.login_api, name='login_api'),
    path('api/logout/', views.logout_api, name='logout_api'),
    path('api/register/', views.register_api, name='register_api'),
    path('api/check-auth/', views.check_auth, name='check_auth'),
]
