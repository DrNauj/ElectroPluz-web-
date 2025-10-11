from django.urls import path
from . import views # Importamos desde el archivo views.py consolidado

app_name = 'auth'

urlpatterns = [
    # Vistas Web de Autenticación
    # Estas vistas usan formularios y renderizan HTML
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),

    # Autenticación via API (Endpoints JSON)
    path('api/login/', views.login_api, name='login_api'),
    path('api/logout/', views.logout_api, name='logout_api'),
    path('api/register/', views.register_api, name='register_api'),
    path('api/check-auth/', views.check_auth, name='check_auth'),
]
