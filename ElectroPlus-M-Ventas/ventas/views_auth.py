"""
Vistas de autenticación para el microservicio de ventas.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.hashers import check_password
from .models import Usuario

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    Endpoint de login para autenticar usuarios.
    """
    nombre_usuario = request.data.get('nombre_usuario')
    contrasena = request.data.get('contrasena')

    if not nombre_usuario or not contrasena:
        return Response({
            'error': 'Se requieren nombre de usuario y contraseña'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        usuario = Usuario.objects.get(nombre_usuario=nombre_usuario)
        if usuario.contrasena == contrasena:  # En producción usar check_password
            return Response({
                'id': usuario.id,
                'nombre_usuario': usuario.nombre_usuario,
                'rol': usuario.rol
            })
        else:
            return Response({
                'error': 'Credenciales inválidas'
            }, status=status.HTTP_401_UNAUTHORIZED)

    except Usuario.DoesNotExist:
        return Response({
            'error': 'Usuario no encontrado'
        }, status=status.HTTP_401_UNAUTHORIZED)