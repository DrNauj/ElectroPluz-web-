"""
Vistas relacionadas con la autenticación y manejo de sesiones.
"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
import logging
import json

from .services.auth_service import authenticate_with_service

logger = logging.getLogger(__name__)

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def login_api(request):
    """
    API endpoint para autenticación de usuarios.
    """
    try:
        data = request.data
        username = data.get('username', request.POST.get('username'))
        password = data.get('password', request.POST.get('password'))
    except json.JSONDecodeError:
        return Response({'error': 'Formato JSON inválido.'}, status=status.HTTP_400_BAD_REQUEST)

    if not username or not password:
        return Response({'error': 'Nombre de usuario y contraseña son requeridos.'}, status=status.HTTP_400_BAD_REQUEST)

    # 1. Autenticar con el microservicio
    user_data, error = authenticate_with_service(username, password)

    if user_data:
        # 2. Establecer la sesión en el gateway
        request.session['is_authenticated'] = True
        request.session['user'] = user_data
        request.session.modified = True
        logger.info(f"Usuario {username} autenticado correctamente. Rol: {user_data.get('rol')}")

        # Redirección según rol
        redirect_url = '/dashboard/'  # Default
        if user_data.get('rol') == 'cliente':
            redirect_url = '/'  # Home para clientes
        elif user_data.get('rol') in ['admin', 'empleado']:
            redirect_url = '/admin/dashboard/'  # Panel admin

        return Response({
            'success': True,
            'message': 'Inicio de sesión exitoso.',
            'user': {'username': user_data['nombre_usuario'], 'rol': user_data['rol']},
            'redirect_url': redirect_url
        }, status=status.HTTP_200_OK)
    else:
        # 3. Fallo de autenticación
        return Response({'success': False, 'error': error}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
def logout_api(request):
    """
    API endpoint para cerrar la sesión.
    """
    # Limpiar la sesión
    request.session.flush()
    logger.info("Sesión cerrada y limpiada.")
    return Response({
        'success': True, 
        'message': 'Sesión cerrada exitosamente.',
        'redirect_url': '/'
    }, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([AllowAny])
def check_auth_status(request):
    """
    API endpoint para verificar el estado de autenticación.
    """
    is_authenticated = request.session.get('is_authenticated', False)
    user_data = request.session.get('user', None) if is_authenticated else None
    
    return Response({
        'is_authenticated': is_authenticated,
        'user': user_data if user_data else None
    }, status=status.HTTP_200_OK)

@require_http_methods(["GET"])
@ensure_csrf_cookie
def get_csrf_token(request):
    """
    Vista para obtener un token CSRF.
    """
    return JsonResponse({'success': True})