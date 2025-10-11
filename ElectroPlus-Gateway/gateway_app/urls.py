from django.urls import path
# CRÍTICO: Importar el módulo de vistas unificado
from . import views 

app_name = 'auth'

urlpatterns = [
    # Autenticación via API (Usados por JS)
    path('api/login/', views.login_api, name='login_api'),
    path('api/logout/', views.logout_api, name='logout_api'),
    path('api/register/', views.register_api, name='register_api'),
    # Nota: la función check_auth se renombra a check_auth_api en views.py para consistencia
    path('api/check-auth/', views.check_auth_api, name='check_auth'), 

    # Vistas de autenticación (Frontend con formularios)
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # Vista del Dashboard del Cliente
    path('customer-dashboard/', views.customer_dashboard, name='customer_dashboard'),
]
