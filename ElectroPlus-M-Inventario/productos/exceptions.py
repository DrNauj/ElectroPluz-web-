from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework import status
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.http import Http404

def custom_exception_handler(exc, context):
    """
    Manejador global de excepciones para estandarizar las respuestas de error.
    """
    # Primero llamamos al manejador por defecto de DRF
    response = exception_handler(exc, context)

    # Si DRF no maneja la excepción, la manejamos nosotros
    if response is None:
        if isinstance(exc, IntegrityError):
            response = Response({
                'error': 'Error de integridad en la base de datos',
                'detail': str(exc)
            }, status=status.HTTP_400_BAD_REQUEST)
        elif isinstance(exc, ValidationError):
            response = Response({
                'error': 'Error de validación',
                'detail': exc.messages if hasattr(exc, 'messages') else str(exc)
            }, status=status.HTTP_400_BAD_REQUEST)
        elif isinstance(exc, Http404):
            response = Response({
                'error': 'No encontrado',
                'detail': 'El recurso solicitado no existe'
            }, status=status.HTTP_404_NOT_FOUND)
        else:
            response = Response({
                'error': 'Error interno del servidor',
                'detail': str(exc)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Si ya hay una respuesta de DRF, la estandarizamos
    if response is not None and not isinstance(response.data, dict):
        response.data = {
            'error': 'Error de validación',
            'detail': response.data
        }

    return response

class InventarioError(APIException):
    """
    Excepción base para errores específicos del módulo de inventario.
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Se ha producido un error en el módulo de inventario.'
    default_code = 'inventario_error'

class StockInsuficienteError(InventarioError):
    """
    Excepción para cuando no hay suficiente stock para una operación.
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'No hay suficiente stock disponible.'
    default_code = 'stock_insuficiente'