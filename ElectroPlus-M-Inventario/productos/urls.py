from rest_framework.routers import DefaultRouter
from django.urls import path, include
from . import views

router = DefaultRouter()
router.register(r'categorias', views.CategoriaViewSet)
router.register(r'proveedores', views.ProveedorViewSet)
router.register(r'productos', views.ProductoViewSet)
router.register(r'historial', views.HistorialInventarioViewSet)

urlpatterns = [
    path('', include(router.urls)),
]