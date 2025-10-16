from rest_framework.routers import DefaultRouter
from django.urls import path, include
from . import views, views_auth

router = DefaultRouter()
router.register(r'usuarios', views.UsuarioViewSet)
router.register(r'clientes', views.ClienteViewSet)
router.register(r'ventas', views.VentaViewSet)
router.register(r'devoluciones', views.DevolucionViewSet)

urlpatterns = [
    path('auth/login/', views_auth.login, name='login'),  # La ruta de autenticación va primero
    path('', include(router.urls)),
]