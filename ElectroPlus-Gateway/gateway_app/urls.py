from django.urls import path
from . import views # Corregido: Importamos views.py en lugar de views_auth(no existe)

app_name = 'auth'

urlpatterns = [
    # Autenticación via API
    path('api/login/', views.login_api, name='login_api'), # Referencia corregida a views
    path('api/logout/', views.logout_api, name='logout_api'), # Referencia corregida a views
    path('api/register/', views.register_api, name='register_api'), # Referencia corregida a views
    path('api/check-auth/', views.check_auth, name='check_auth'), # Referencia corregida a views
]
