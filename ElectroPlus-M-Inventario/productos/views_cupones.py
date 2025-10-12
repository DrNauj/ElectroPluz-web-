from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db import transaction
from .models_cupones import Cupon, UsoCupon
from .serializers_cupones import CuponSerializer, UsoCuponSerializer
import logging

logger = logging.getLogger(__name__)

class CuponViewSet(viewsets.ModelViewSet):
    queryset = Cupon.objects.all()
    serializer_class = CuponSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        # Filtrar por estado (activo/inactivo)
        activo = self.request.query_params.get('activo')
        if activo is not None:
            ahora = timezone.now()
            if activo.lower() == 'true':
                queryset = queryset.filter(
                    fecha_inicio__lte=ahora,
                    fecha_fin__gte=ahora
                )
            elif activo.lower() == 'false':
                queryset = queryset.exclude(
                    fecha_inicio__lte=ahora,
                    fecha_fin__gte=ahora
                )
                
        # Filtrar por producto
        producto_id = self.request.query_params.get('producto')
        if producto_id:
            queryset = queryset.filter(valido_para_producto_id=producto_id)
            
        return queryset

    @action(detail=True, methods=['post'])
    def validar(self, request, pk=None):
        """Valida si un cupón puede ser usado para una compra específica."""
        cupon = self.get_object()
        
        # Verificar si el cupón está activo
        if not cupon.esta_activo:
            return Response({
                'valido': False,
                'mensaje': 'El cupón ha expirado o aún no está activo'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # Verificar producto si el cupón es específico
        producto_id = request.data.get('producto_id')
        if cupon.valido_para_producto_id and str(cupon.valido_para_producto_id) != str(producto_id):
            return Response({
                'valido': False,
                'mensaje': 'El cupón no es válido para este producto'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # Calcular descuento
        precio_original = float(request.data.get('precio', 0))
        precio_final = cupon.aplicar_descuento(precio_original)
        
        return Response({
            'valido': True,
            'descuento': precio_original - precio_final,
            'precio_final': precio_final
        })

    @action(detail=True, methods=['post'])
    def usar(self, request, pk=None):
        """Registra el uso de un cupón en una venta."""
        cupon = self.get_object()
        
        # Verificar datos requeridos
        id_venta = request.data.get('id_venta')
        if not id_venta:
            return Response({
                'error': 'Se requiere el ID de la venta'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # Verificar si el cupón está activo
        if not cupon.esta_activo:
            return Response({
                'error': 'El cupón ha expirado o aún no está activo'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            with transaction.atomic():
                # Registrar uso del cupón
                uso_cupon = UsoCupon.objects.create(
                    cupon=cupon,
                    id_venta=id_venta,
                    fecha_uso=timezone.now()
                )
                
                return Response({
                    'mensaje': f'Cupón {cupon.codigo} aplicado correctamente',
                    'uso_cupon_id': uso_cupon.id
                })
                
        except Exception as e:
            logger.error(f"Error al registrar uso del cupón: {e}")
            return Response({
                'error': 'Error al registrar el uso del cupón'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)