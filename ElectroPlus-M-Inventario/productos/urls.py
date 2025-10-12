from rest_framework.routers import DefaultRouter
from django.urls import path, include
from . import views
from . import views_cupones

router = DefaultRouter()
router.register(r'categorias', views.CategoriaViewSet)
router.register(r'proveedores', views.ProveedorViewSet)
router.register(r'productos', views.ProductoViewSet)
router.register(r'historial', views.HistorialInventarioViewSet)
router.register(r'cupones', views_cupones.CuponViewSet)

urlpatterns = [
    path('', include(router.urls)),
]