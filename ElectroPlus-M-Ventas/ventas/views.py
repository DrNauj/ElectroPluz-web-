from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
import requests
from .models import Usuario, Cliente, Venta, DetalleVenta, Devolucion
from .serializers import (
    UsuarioSerializer, ClienteSerializer,
    VentaSerializer, VentaCreateSerializer,
    DevolucionSerializer
)

# Configuración del endpoint de inventario
import os

# Leer configuración desde variables de entorno si existen
INVENTARIO_API = os.getenv('INVENTARIO_API', 'http://localhost:8001/api')
SECRET_KEY = os.getenv('SECRET_KEY', 'tu_clave_secreta')

class UsuarioViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para visualizar usuarios.
    Solo lectura por seguridad.
    """
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer

class ClienteViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar clientes.
    Permite todas las operaciones CRUD.
    """
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer

    @action(detail=False, methods=['get'])
    def pedidos(self, request):
        """
        Obtener pedidos de un cliente específico.
        """
        cliente_id = request.query_params.get('cliente_id')
        if not cliente_id:
            return Response(
                {'message': 'cliente_id es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Obtener ventas del cliente
        ventas = Venta.objects.filter(cliente_id=cliente_id).order_by('-fecha_venta')
        serializer = VentaSerializer(ventas, many=True)
        return Response(serializer.data)

class VentaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar ventas.
    Incluye lógica para crear ventas y actualizar stock.
    """
    queryset = Venta.objects.all()
    serializer_class = VentaSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return VentaCreateSerializer
        return VentaSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        Crear una nueva venta y actualizar el stock.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            # 1. Validar stock antes de proceder
            detalles = request.data.get('detalles', [])
            for detalle in detalles:
                response = requests.get(
                    f"{INVENTARIO_API}/productos/{detalle['id_producto']}/",
                    headers={'SECRET_KEY': SECRET_KEY}
                )
                response.raise_for_status()
                producto = response.json()

                if producto['stock'] < detalle['cantidad']:
                    return Response({
                        'message': f'Stock insuficiente para el producto {producto["nombre"]}',
                        'stock_actual': producto['stock'],
                        'cantidad_solicitada': detalle['cantidad']
                    }, status=status.HTTP_400_BAD_REQUEST)

            # 2. Crear la venta
            venta = serializer.save(
                usuario=request.user,  # Requiere autenticación
                fecha_venta=timezone.now()
            )

            # 3. Actualizar stock en inventario
            for detalle in detalles:
                response = requests.patch(
                    f"{INVENTARIO_API}/productos/{detalle['id_producto']}/actualizar_stock/",
                    json={
                        'cantidad': detalle['cantidad'],
                        'tipo_movimiento': 'Salida por Venta'
                    },
                    headers={'SECRET_KEY': SECRET_KEY}
                )
                response.raise_for_status()

            return Response(
                VentaSerializer(venta).data,
                status=status.HTTP_201_CREATED
            )

        except requests.RequestException as e:
            # Rollback automático por @transaction.atomic
            return Response(
                {'message': f'Error al comunicarse con el servicio de inventario: {str(e)}'},
                status=status.HTTP_502_BAD_GATEWAY
            )

    @action(detail=True, methods=['post'])
    def cambiar_estado(self, request, pk=None):
        """
        Cambiar el estado de una venta.
        """
        venta = self.get_object()
        nuevo_estado = request.data.get('estado')

        if nuevo_estado not in dict(Venta.ESTADOS).keys():
            return Response(
                {'message': 'Estado no válido'},
                status=status.HTTP_400_BAD_REQUEST
            )

        venta.estado = nuevo_estado
        venta.save()

        return Response(VentaSerializer(venta).data)

class DevolucionViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar devoluciones.
    """
    queryset = Devolucion.objects.all()
    serializer_class = DevolucionSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        Crear una nueva devolución y actualizar stock.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            # 1. Crear la devolución
            devolucion = serializer.save(fecha_devolucion=timezone.now())
            venta = devolucion.venta
            detalles = request.data.get('detalles', [])

            # 2. Actualizar stock en inventario
            for detalle in detalles:
                response = requests.patch(
                    f"{INVENTARIO_API}/productos/{detalle['id_producto']}/actualizar_stock/",
                    json={
                        'cantidad': detalle['cantidad_devuelta'],
                        'tipo_movimiento': 'Salida por Devolución'
                    },
                    headers={'SECRET_KEY': SECRET_KEY}
                )
                response.raise_for_status()

            # 3. Actualizar estado de la venta si es necesario
            if venta.estado == 'Entregado':
                venta.estado = 'Reembolsado'
                venta.save()

            return Response(
                DevolucionSerializer(devolucion).data,
                status=status.HTTP_201_CREATED
            )

        except requests.RequestException as e:
            return Response(
                {'message': f'Error al comunicarse con el servicio de inventario: {str(e)}'},
                status=status.HTTP_502_BAD_GATEWAY
            )
