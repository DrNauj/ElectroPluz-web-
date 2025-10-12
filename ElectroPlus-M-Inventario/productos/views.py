from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from django.db import models
from .models import Categoria, Proveedor, Producto, HistorialInventario
from .serializers import (
    CategoriaSerializer, ProveedorSerializer,
    ProductoSerializer, ProductoDetalladoSerializer,
    HistorialInventarioSerializer
)

class CategoriaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para visualizar categorías.
    Solo lectura ya que las categorías son datos maestros.
    """
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer

class ProveedorViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para visualizar proveedores.
    Solo lectura ya que los proveedores son datos maestros.
    """
    queryset = Proveedor.objects.all()
    serializer_class = ProveedorSerializer


class ProductoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar productos.
    Permite operaciones CRUD completas y manejo especial del stock.
    """
    queryset = Producto.objects.all().select_related('categoria', 'proveedor')
    serializer_class = ProductoSerializer
    lookup_field = 'slug'
    lookup_url_kwarg = 'slug'

    def retrieve(self, request, *args, **kwargs):
        """Sobreescribir retrieve para manejar búsqueda por slug."""
        try:
            instance = self.get_object()
            serializer = ProductoDetalladoSerializer(instance)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': f'No se encontró el producto: {str(e)}'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def get_queryset(self):
        """Personalizar el queryset base con filtros y búsqueda."""
        queryset = super().get_queryset()
        
        # Obtener parámetros de consulta
        busqueda = self.request.query_params.get('busqueda', None)
        categoria = self.request.query_params.get('categoria', None)
        precio_min = self.request.query_params.get('precio_min', None)
        precio_max = self.request.query_params.get('precio_max', None)
        con_descuento = self.request.query_params.get('con_descuento', None)
        ordering = self.request.query_params.get('ordering', None)
        exclude = self.request.query_params.get('exclude', None)
        
        # Aplicar búsqueda por nombre o descripción
        if busqueda:
            queryset = queryset.filter(nombre__icontains=busqueda) | queryset.filter(descripcion__icontains=busqueda)
        
        # Filtrar por categoría
        if categoria:
            queryset = queryset.filter(categoria_id=categoria)
        
        # Filtrar por rango de precios
        if precio_min:
            queryset = queryset.filter(precio__gte=float(precio_min))
        if precio_max:
            queryset = queryset.filter(precio__lte=float(precio_max))
        
        # Filtrar productos con descuento
        if con_descuento and con_descuento.lower() == 'true':
            queryset = queryset.filter(precio_original__isnull=False, precio__lt=models.F('precio_original'))
        
        # Aplicar ordenamiento
        if ordering:
            if ordering.startswith('-'):
                field = ordering[1:]
                if hasattr(Producto, field):
                    queryset = queryset.order_by(ordering)
            else:
                if hasattr(Producto, ordering):
                    queryset = queryset.order_by(ordering)
        
        return queryset

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProductoDetalladoSerializer
        return ProductoSerializer

    @action(detail=True, methods=['post'])
    def actualizar_stock(self, request, pk=None):
        """Actualizar stock y registrar movimiento en `HistorialInventario`.

        Parámetros esperados en body:
        - cantidad: número (positivo)
        - tipo_movimiento: string (ej. 'Entrada', 'Salida por Venta', ...)
        - usuario: id del usuario (opcional)
        - request_id: string para trazabilidad (opcional)
        """
        producto = self.get_object()

        # Intentar parsear la cantidad
        try:
            cantidad = request.data.get('cantidad')
            if cantidad is None:
                return Response({'error': 'Falta el parámetro "cantidad".'}, status=status.HTTP_400_BAD_REQUEST)
            cantidad = int(cantidad)
        except (ValueError, TypeError):
            return Response({'error': 'Cantidad inválida. Debe ser un número entero.'}, status=status.HTTP_400_BAD_REQUEST)

        tipo_movimiento = request.data.get('tipo_movimiento')
        if not tipo_movimiento:
            return Response({'error': 'Falta el parámetro "tipo_movimiento".'}, status=status.HTTP_400_BAD_REQUEST)

        usuario = request.data.get('usuario')
        request_id = request.headers.get('X-Request-ID') or request.data.get('request_id')

        # Verificar stock para salidas
        if tipo_movimiento.lower().startswith('salida') and producto.stock < cantidad:
            return Response({'error': 'Stock insuficiente', 'stock_actual': producto.stock}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                # Aplicar cambio de stock
                if tipo_movimiento.lower().startswith('salida'):
                    producto.stock -= cantidad
                else:
                    producto.stock += cantidad
                producto.save()

                # Registrar movimiento en historial (usar campos del modelo)
                HistorialInventario.objects.create(
                    producto=producto,
                    tipo_movimiento=tipo_movimiento,
                    cantidad=cantidad,
                    fecha=timezone.now(),
                    usuario=usuario if usuario is not None else None,
                    request_id=request_id
                )

            return Response({'mensaje': 'Stock actualizado correctamente', 'nuevo_stock': producto.stock}, status=status.HTTP_200_OK)

        except Producto.DoesNotExist:
            return Response({'error': 'Producto no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': 'Falla interna del servidor', 'detail': str(e) if settings.DEBUG else None}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class HistorialInventarioViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para consultar el historial de inventario.
    Solo lectura ya que el historial se genera automáticamente.
    Provee datos para el dashboard a través del API Gateway.
    """
    queryset = HistorialInventario.objects.all()
    serializer_class = HistorialInventarioSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtros para el dashboard
        producto_id = self.request.query_params.get('producto', None)
        fecha_inicio = self.request.query_params.get('fecha_inicio', None)
        fecha_fin = self.request.query_params.get('fecha_fin', None)
        tipo_movimiento = self.request.query_params.get('tipo_movimiento', None)
        request_id = self.request.query_params.get('request_id', None)

        if producto_id:
            queryset = queryset.filter(producto_id=producto_id)
        if fecha_inicio:
            queryset = queryset.filter(fecha__gte=fecha_inicio)
        if fecha_fin:
            queryset = queryset.filter(fecha__lte=fecha_fin)
        if tipo_movimiento:
            queryset = queryset.filter(tipo_movimiento=tipo_movimiento)
        if request_id:
            queryset = queryset.filter(request_id=request_id)

        # Incluir datos relacionados para optimizar consultas
        queryset = queryset.select_related('producto', 'producto__categoria')
        
        return queryset.order_by('-fecha')
