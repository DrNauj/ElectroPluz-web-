"""
Vistas de autenticación, funciones base y API endpoints del gateway.

Este módulo proporciona las vistas y funciones básicas necesarias para la
autenticación y funcionalidad base del gateway, actuando como intermediario
hacia los microservicios de Ventas e Inventario.
"""
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes # Importaciones necesarias para API decorators
from rest_framework.permissions import AllowAny
import requests
import logging
import json

from .forms import CustomLoginForm, RegisterForm # Se asume que estos son necesarios para las vistas web, aunque aquí solo se implementan las API.

logger = logging.getLogger(__name__)

# --- Funciones Auxiliares de Autenticación ---

def authenticate_with_service(username_or_id, password):
    """
    Autentica el usuario contra el servicio de ventas.

    Mapea los nombres de variables locales a los esperados
    por el microservicio ('nombre_usuario', 'contrasena').
    """
    try:
        response = requests.post(
            f"{settings.MICROSERVICES['VENTAS']['BASE_URL']}auth/login/",
            json={
                'nombre_usuario': username_or_id,
                'contrasena': password
            },
            headers={
                'X-API-Key': settings.MICROSERVICES['VENTAS']['API_KEY']
            },
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            # Se devuelven los datos crudos del usuario autenticado (id, nombre, token, rol)
            return {
                'id': data.get('id'),
                'nombre_usuario': data.get('nombre_usuario'),
                'token': data.get('token'),
                'rol': data.get('rol', 'cliente') # Asume 'cliente' por defecto
            }, None
        else:
            error_data = response.json()
            # Asume que el microservicio devuelve un campo 'detail' o 'non_field_errors'
            error_message = error_data.get('detail', 'Credenciales inválidas o error desconocido.')
            return None, error_message

    except requests.RequestException as e:
        logger.error(f"Error de conexión con el microservicio de ventas (Login): {str(e)}")
        return None, "Error de conexión con el servicio de autenticación."

# --- Vistas API (Endpoints JSON) ---

@api_view(['POST'])
@permission_classes([AllowAny])
def login_api(request):
    """
    Endpoint de API para iniciar sesión.

    Autentica al usuario contra el microservicio de ventas y almacena
    los datos en la sesión del gateway.
    """
    # Intentar cargar el cuerpo como JSON
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
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

        # Determinar redirección según rol
        redirect_url = '/'  # Default para clientes
        if user_data.get('rol') == 'admin':
            redirect_url = '/admin/dashboard/'
        elif user_data.get('rol') == 'empleado':
            redirect_url = '#'  # No redireccionar automáticamente, esperar selección

        # Personalizar mensaje según rol
        welcome_message = f"¡Bienvenido {user_data['nombre_usuario']}!"
        if user_data.get('rol') == 'empleado':
            welcome_message += " Por favor, seleccione su vista preferida."
        elif user_data.get('rol') == 'admin':
            welcome_message += " Accediendo al panel de administración."
        else:
            welcome_message += " Gracias por visitarnos."

        return Response({
            'success': True,
            'message': welcome_message,
            'user': {
                'username': user_data['nombre_usuario'],
                'rol': user_data['rol'],
                'id': user_data['id']
            },
            'redirect_url': redirect_url,
            'has_role_choice': user_data.get('rol') == 'empleado'  # Flag para indicar si mostrar selección de vista
        }, status=status.HTTP_200_OK)
    else:
        # 3. Fallo de autenticación
        return Response({'success': False, 'error': error}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
def logout_api(request):
    """
    Endpoint de API para cerrar la sesión.
    """
    # Limpiar la sesión
    request.session.flush()
    logger.info("Sesión cerrada y limpiada.")
    return Response({'success': True, 'message': 'Sesión cerrada exitosamente.'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def register_api(request):
    """
    Endpoint de API para registrar un nuevo usuario.

    Delega el registro al microservicio de ventas.
    """
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        # Otros campos requeridos por el microservicio de registro
        nombre_completo = data.get('nombre_completo')
        telefono = data.get('telefono')
    except json.JSONDecodeError:
        return Response({'error': 'Formato JSON inválido.'}, status=status.HTTP_400_BAD_REQUEST)

    required_fields = ['username', 'password', 'email', 'nombre_completo']
    if not all(data.get(field) for field in required_fields):
        return Response({'error': 'Faltan campos obligatorios (username, password, email, nombre_completo).'}, status=status.HTTP_400_BAD_REQUEST)

    # Preparar datos para el microservicio
    payload = {
        'nombre_usuario': username,
        'contrasena': password,
        'email': email,
        'nombre_completo': nombre_completo,
        'telefono': telefono,
        # ... otros campos si son necesarios
    }

    try:
        response = requests.post(
            f"{settings.MICROSERVICES['VENTAS']['BASE_URL']}auth/register/",
            json=payload,
            headers={
                'X-API-Key': settings.MICROSERVICES['VENTAS']['API_KEY']
            },
            timeout=5
        )

        if response.status_code == 201:
            return Response({
                'success': True,
                'message': 'Registro exitoso. Puede iniciar sesión.',
                'user_data': response.json()
            }, status=status.HTTP_201_CREATED)
        else:
            # Propagar errores de validación del microservicio
            error_data = response.json()
            return Response({'success': False, 'error': error_data}, status=response.status_code)

    except requests.RequestException as e:
        logger.error(f"Error de conexión con el microservicio de ventas (Registro): {str(e)}")
        return Response({'success': False, 'error': 'Error de conexión con el servicio de registro.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


def check_auth(request):
    """Verifica el estado de autenticación del usuario (vista JSON)."""
    user_info = request.session.get("user", {})
    return JsonResponse({
        "is_authenticated": request.session.get("is_authenticated", False),
        "user": {
            'username': user_info.get('nombre_usuario'),
            'rol': user_info.get('rol'),
            'id': user_info.get('id')
        }
    })

# --- Vistas Web (HTML) ---

def dashboard(request):
    """
    Vista principal del dashboard para usuarios autenticados.
    Redirige según el rol: admin/empleado o cliente.
    """
    if not request.session.get('is_authenticated', False):
        messages.error(request, 'Debe iniciar sesión para acceder al dashboard.')
        return redirect('auth:login') # Asegurarse de usar el nombre de la ruta

    user_info = request.session['user']
    user_rol = user_info.get('rol', 'cliente')

    if user_rol in ['admin', 'empleado']:
        # Redirigir al dashboard de gestión (asumido en 'inventory.urls')
        return redirect('inventory:dashboard_home') # Asume una ruta con nombre 'dashboard_home' en la app 'inventory'

    elif user_rol == 'cliente':
        # Mostrar el dashboard de cliente, que usa llamadas a microservicios
        try:
            # Obtener datos del cliente (perfil)
            customer_response = requests.get(
                f"{settings.MICROSERVICES['VENTAS']['BASE_URL']}clientes/perfil/",
                headers={
                    'X-API-Key': settings.MICROSERVICES['VENTAS']['API_KEY'],
                    # Se usa el token para autenticar en el microservicio
                    'Authorization': f'Token {request.session["user"]["token"]}'
                },
                timeout=5
            )

            # Obtener historial de pedidos
            orders_response = requests.get(
                f"{settings.MICROSERVICES['VENTAS']['BASE_URL']}clientes/pedidos/",
                headers={
                    'X-API-Key': settings.MICROSERVICES['VENTAS']['API_KEY'],
                    # Se usa el token para autenticar en el microservicio
                    'Authorization': f'Token {request.session["user"]["token"]}'
                },
                timeout=5
            )

            context = {
                'customer_info': None,
                'orders': []
            }
            if customer_response.status_code == 200:
                context['customer_info'] = customer_response.json()
            else:
                logger.warning(f"Error al obtener perfil del cliente ({customer_response.status_code}): {customer_response.text}")

            if orders_response.status_code == 200:
                context['orders'] = orders_response.json()
            else:
                logger.warning(f"Error al obtener pedidos del cliente ({orders_response.status_code}): {orders_response.text}")

            # Nota: Asegurar que 'dashboard/customer_dashboard.html' exista.
            return render(request, 'dashboard/customer_dashboard.html', context)

        except requests.RequestException as e:
            logger.error(f"Error al obtener datos del cliente: {str(e)}")
            messages.error(request, 'Error de conexión con los servicios. Intente más tarde.')
            return render(request, 'dashboard/customer_dashboard.html', {'error': 'Error de conexión con los servicios.'})

    else:
        messages.error(request, 'Rol de usuario no reconocido.')
        return redirect('auth:login') # Redirigir si el rol es inválido.


# --- Vistas Web de Autenticación (con formularios) ---

def login_view(request):
    """Vista web para el formulario de inicio de sesión."""
    if request.session.get('is_authenticated', False):
        return redirect('dashboard')

    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST) # CustomLoginForm requiere 'request'
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            # Llamar a la función de autenticación (la misma que usa la API internamente)
            user_data, error = authenticate_with_service(username, password)

            if user_data:
                request.session['is_authenticated'] = True
                request.session['user'] = user_data
                request.session.modified = True
                messages.success(request, f"¡Bienvenido, {username}!")
                return redirect('dashboard')
            else:
                messages.error(request, error)
        else:
            # Los errores del formulario se manejan automáticamente
            messages.error(request, 'Por favor, corrija los errores del formulario.')
    else:
        form = CustomLoginForm()

    return render(request, 'storefront/auth/login.html', {'form': form})

def register_view(request):
    """Vista web para el formulario de registro."""
    if request.session.get('is_authenticated', False):
        return redirect('dashboard')

    if request.method == 'POST':
        form = RegisterForm(request.POST, request.FILES) # Asume que RegisterForm maneja archivos (avatar)
        if form.is_valid():
            data = form.cleaned_data
            payload = {
                'nombre_usuario': data['username'],
                'contrasena': data['password'],
                'email': data['email'],
                'nombre_completo': data['first_name'] + ' ' + data['last_name'], # Combinar nombre
                'telefono': data.get('phone', ''),
                # Otros campos...
            }
            # Nota: El manejo de la subida del avatar al microservicio es complejo y se omite
            # aquí, asumiendo que solo se pasan datos simples en el registro por API.
            # En un sistema real, el gateway subiría el archivo a S3/GCS y enviaría la URL.

            try:
                response = requests.post(
                    f"{settings.MICROSERVICES['VENTAS']['BASE_URL']}auth/register/",
                    json=payload,
                    headers={
                        'X-API-Key': settings.MICROSERVICES['VENTAS']['API_KEY']
                    },
                    timeout=5
                )

                if response.status_code == 201:
                    messages.success(request, 'Registro exitoso. ¡Ahora puedes iniciar sesión!')
                    return redirect('auth:login')
                else:
                    error_data = response.json()
                    # Mostrar errores específicos del microservicio
                    if 'nombre_usuario' in error_data:
                        messages.error(request, f"Nombre de usuario: {error_data['nombre_usuario'][0]}")
                    elif 'email' in error_data:
                        messages.error(request, f"Email: {error_data['email'][0]}")
                    else:
                        messages.error(request, 'Error en el registro. Intente con otros datos.')

            except requests.RequestException as e:
                logger.error(f"Error de conexión con el microservicio de ventas (Registro-Web): {str(e)}")
                messages.error(request, 'Error de conexión con el servicio de registro.')
        else:
            messages.error(request, 'Por favor, corrija los errores del formulario.')
    else:
        form = RegisterForm()

    return render(request, 'auth/register.html', {'form': form})


@require_http_methods(["GET", "POST"])
def logout_view(request):
    """Vista web para cerrar sesión."""
    if request.session.get('is_authenticated', False):
        request.session.flush()
        messages.success(request, '¡Has cerrado sesión exitosamente!')
    return redirect('storefront:home') # Redirigir a la página principal (storefront:home)
