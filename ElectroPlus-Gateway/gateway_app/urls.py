from django.urls import path
from . import views # ¡Importación corregida! Ahora apunta a views.py

app_name = 'gateway_app'

urlpatterns = [
    # ----------------------------------------------------
    # --- Vistas Web (URLs para renderizar páginas) ---
    # ----------------------------------------------------
    path('login/', views.login, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # Rutas de perfil (mantienen prefijo auth/ por ser parte de la gestión de usuarios)
    path('profile/edit/customer/', views.customer_profile_edit, name='customer_profile_edit'),
    path('profile/edit/admin/', views.admin_profile_edit, name='admin_profile_edit'),

    # ----------------------------------------------------
    # --- Vistas API (Para uso interno de AJAX/Frontend) ---
    # ----------------------------------------------------
    path('api/login/', views.login_api, name='login_api'),
    path('api/logout/', views.logout_api, name='logout_api'),
    path('api/register/', views.register_api, name='register_api'),
    path('api/check-auth/', views.check_auth, name='check_auth'),
]
