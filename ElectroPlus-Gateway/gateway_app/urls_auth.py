"""
URLs relacionadas con autenticación y autorización.
"""
from django.urls import path
from . import views_auth

app_name = 'api_auth'

urlpatterns = [
    path('login/', views_auth.login_api, name='login'),
    path('logout/', views_auth.logout_api, name='logout'),
    path('status/', views_auth.check_auth_status, name='status'),
    path('csrf/', views_auth.get_csrf_token, name='csrf'),
]