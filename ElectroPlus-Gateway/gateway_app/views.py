"""
Vistas de autenticación y funciones base del gateway.

Este módulo proporciona las vistas y funciones básicas necesarias para la
autenticación y funcionalidad base del gateway, actuando como intermediario
hacia los microservicios de Ventas e Inventario.
"""
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import logout
from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse # Importación necesaria para vistas API
from rest_framework.response import Response
from rest_framework import status
import requests
import logging
import json

# Importamos los formularios necesarios para las vistas de autenticación y perfil
from .forms import CustomLoginForm, RegisterForm, ProfileForm 

logger = logging.getLogger(__name__)

# --- Funciones Auxiliares ---

def authenticate_with_service(username_or_id, password):
    """
    Autentica el usuario contra el servicio de ventas (MS Ventas).
    
    Mapea las variables locales a las esperadas por el microservicio ('nombre_usuario', 'contrasena').
    """
    try:
        response = requests.post(
            f"{settings.MICROSERVICES['VENTAS']['BASE_URL']}auth/login/",
            json={
                'nombre_usuario': username_or_id,
                'contrasena': password
            },
            headers={
                # Incluir la clave API del Gateway para acceder al microservicio
                'X-API-Key': settings.MICROSERVICES['VENTAS']['API_KEY']
            },
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            # Devolver los datos clave para la sesión
            return {
                'id': data.get('id'),
                'nombre_usuario': data.get('nombre_usuario'),
                'email': data.get('email'),
                'rol': data.get('rol'),
                'token': data.get('token') # Token de autenticación del usuario
            }
        else:
            logger.warning(f"Fallo de autenticación en MS Ventas. HTTP {response.status_code}: {response.text}")
            return None
            
    except requests.RequestException as e:
        logger.error(f"Error de conexión al microservicio de autenticación: {str(e)}")
        return None

# --- VISTAS DE PÁGINAS WEB (Formularios y Redirecciones) ---

def login(request):
    """Vista de login para el frontend (páginas renderizadas)."""
    if request.session.get('is_authenticated'):
        return redirect('dashboard') # Redirigir si ya está autenticado

    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            # Nota: Los datos provienen del formulario estándar de Django
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            user_data = authenticate_with_service(username, password)
            
            if user_data:
                # Almacenar en sesión y marcar como autenticado
                request.session['is_authenticated'] = True
                request.session['user'] = user_data
                messages.success(request, f'¡Bienvenido, {user_data["nombre_usuario"]}!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Credenciales inválidas o servicio no disponible.')
    else:
        form = CustomLoginForm()
        
    return render(request, 'auth/login.html', {'form': form})


def register(request):
    """Vista de registro para el frontend (páginas renderizadas)."""
    if request.session.get('is_authenticated'):
        return redirect('dashboard')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            
            try:
                # Mapear a los nombres esperados por el microservicio de registro (MS Ventas)
                register_data = {
                    'nombre_usuario': data['username'],
                    'email': data['email'],
                    'contrasena': data['password2'], # Usamos password2 que es el campo confirmado
                    'first_name': data.get('first_name', ''),
                    'last_name': data.get('last_name', ''),
                    'rol': 'cliente' # Rol por defecto para registros de frontend
                }

                response = requests.post(
                    f"{settings.MICROSERVICES['VENTAS']['BASE_URL']}auth/register/",
                    json=register_data,
                    headers={'X-API-Key': settings.MICROSERVICES['VENTAS']['API_KEY']},
                    timeout=5
                )

                if response.status_code == 201:
                    messages.success(request, 'Registro exitoso. ¡Inicia sesión ahora!')
                    return redirect('login')
                else:
                    error_data = response.json()
                    # Intento más detallado de mostrar errores de validación del microservicio
                    if isinstance(error_data, dict):
                         for field, errors in error_data.items():
                             messages.error(request, f"{field}: {', '.join(errors)}")
                    else:
                        messages.error(request, error_data.get('detail', 'Error desconocido al registrar.'))

            except requests.RequestException as e:
                logger.error(f"Error de conexión al microservicio de registro: {str(e)}")
                messages.error(request, 'Error de conexión con los servicios. Intente más tarde.')
    else:
        form = RegisterForm()
        
    return render(request, 'auth/register.html', {'form': form})


def logout_view(request):
    """Vista para cerrar sesión y limpiar la sesión de Django."""
    if request.session.get('is_authenticated'):
        # Limpiar la sesión
        request.session.flush()
        messages.info(request, 'Has cerrado sesión exitosamente.')
    return redirect('home') # Asumimos que 'home' es una URL definida en otro lugar


def dashboard(request):
    """
    Vista principal del dashboard que redirige según el rol del usuario.
    Asume que el AuthenticationMiddleware ya verificó la autenticación.
    """
    # El UserDataMiddleware debe haber agregado request.user
    if not request.user.is_authenticated:
        messages.warning(request, 'Necesita iniciar sesión para acceder al dashboard.')
        return redirect('login')
        
    user_role = request.user.rol
    
    if user_role == 'cliente':
        return customer_dashboard(request)
    elif user_role in ['admin', 'empleado']:
        return admin_dashboard(request)
    else:
        messages.error(request, 'Rol de usuario no reconocido. Redirigiendo a login.')
        return redirect('login')


def customer_dashboard(request):
    """
    Dashboard del cliente: Muestra información de perfil y un resumen de pedidos.
    """
    if request.user.rol != 'cliente':
        messages.error(request, 'Acceso denegado. Solo para clientes.')
        return redirect('dashboard')
        
    user_token = request.session['user']['token']
    
    context = {}
    
    try:
        # 1. Obtener datos del cliente (perfil)
        customer_response = requests.get(
            f"{settings.MICROSERVICES['VENTAS']['BASE_URL']}clientes/perfil/",
            headers={
                'X-API-Key': settings.MICROSERVICES['VENTAS']['API_KEY'],
                'Authorization': f'Token {user_token}'
            },
            timeout=5
        )
        
        # 2. Obtener historial de pedidos (últimos 5)
        orders_response = requests.get(
            f"{settings.MICROSERVICES['VENTAS']['BASE_URL']}clientes/pedidos/?limit=5",
            headers={
                'X-API-Key': settings.MICROSERVICES['VENTAS']['API_KEY'],
                'Authorization': f'Token {user_token}'
            },
            timeout=5
        )
        
        if customer_response.status_code == 200:
            context['customer_info'] = customer_response.json()
        else:
            logger.warning(f"MS Ventas - No se pudo obtener perfil (HTTP {customer_response.status_code})")
            
        if orders_response.status_code == 200:
            context['orders'] = orders_response.json()
        else:
            logger.warning(f"MS Ventas - No se pudo obtener pedidos (HTTP {orders_response.status_code})")
            
        return render(request, 'dashboard/customer_dashboard.html', context)
            
    except requests.RequestException as e:
        logger.error(f"Error al obtener datos del cliente: {str(e)}")
        messages.error(request, 'Error de conexión con los servicios. Intente más tarde.')
        return redirect('home') # Redirigir a home o a una página de error


def admin_dashboard(request):
    """
    Dashboard del administrador/empleado.
    """
    if request.user.rol not in ['admin', 'empleado']:
        messages.error(request, 'Acceso denegado.')
        return redirect('dashboard')
        
    # Lógica pendiente para obtener métricas y datos de gestión de los microservicios
    messages.info(request, 'Dashboard de administración. Lógica de negocio pendiente.')
    return render(request, 'dashboard/admin_dashboard.html', {})


@require_http_methods(["GET", "POST"])
def customer_profile_edit(request):
    """
    Permite al cliente editar su información de perfil.
    """
    if request.user.rol != 'cliente':
        messages.error(request, 'Acceso denegado.')
        return redirect('dashboard')

    user_token = request.session['user']['token']
    profile_url = f"{settings.MICROSERVICES['VENTAS']['BASE_URL']}clientes/perfil/"
    
    headers = {
        'X-API-Key': settings.MICROSERVICES['VENTAS']['API_KEY'],
        'Authorization': f'Token {user_token}'
    }

    if request.method == 'GET':
        try:
            # 1. Obtener datos actuales del perfil
            response = requests.get(profile_url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                profile_data = response.json()
                # Mapeo de datos del MS a los campos del formulario
                initial_data = {
                    'phone': profile_data.get('telefono'),
                    'address': profile_data.get('direccion'),
                    'city': profile_data.get('ciudad'),
                    'state': profile_data.get('estado'),
                    'zip_code': profile_data.get('codigo_postal'),
                    'country': profile_data.get('pais'),
                }
                form = ProfileForm(initial=initial_data)
            else:
                messages.warning(request, 'No se pudieron cargar los datos del perfil actual.')
                form = ProfileForm() # Formulario vacío
        except requests.RequestException as e:
            logger.error(f"Error GET al obtener perfil de cliente: {str(e)}")
            messages.error(request, 'Error de conexión. Intente más tarde.')
            form = ProfileForm() # Formulario vacío
            
    elif request.method == 'POST':
        # Nota: El formulario incluye 'request.FILES' en caso de que se maneje una imagen/avatar
        form = ProfileForm(request.POST, request.FILES) 
        
        if form.is_valid():
            cleaned_data = form.cleaned_data
            
            # 2. Mapear datos del formulario a la estructura del microservicio
            update_data = {
                'telefono': cleaned_data.get('phone'),
                'direccion': cleaned_data.get('address'),
                'ciudad': cleaned_data.get('city'),
                'estado': cleaned_data.get('state'),
                'codigo_postal': cleaned_data.get('zip_code'),
                'pais': cleaned_data.get('country'),
                # El campo 'avatar' debe ser manejado por separado si es un archivo
            }
            
            try:
                # 3. Enviar la actualización (PATCH para actualización parcial)
                response = requests.patch(
                    profile_url, 
                    json=update_data, 
                    headers=headers, 
                    timeout=5
                )

                if response.status_code in [200, 202]: 
                    messages.success(request, 'Perfil actualizado correctamente.')
                    return redirect('customer_dashboard') 
                else:
                    error_msg = response.json().get('detail', 'Error al actualizar el perfil en el servicio.')
                    logger.error(f"MS Ventas - Error PATCH perfil (HTTP {response.status_code}): {error_msg}")
                    messages.error(request, f'No se pudo actualizar el perfil: {error_msg}')
            
            except requests.RequestException as e:
                logger.error(f"Error POST al actualizar perfil de cliente: {str(e)}")
                messages.error(request, 'Error de conexión con los servicios. Intente más tarde.')
        
    return render(request, 'dashboard/customer_profile_edit.html', {'form': form})


@require_http_methods(["GET", "POST"])
def admin_profile_edit(request):
    """
    Vista de edición de perfil para el administrador/empleado.
    """
    if request.user.rol not in ['admin', 'empleado']:
        messages.error(request, 'Acceso denegado.')
        return redirect('dashboard')

    messages.info(request, 'Edición de perfil de administrador/empleado pendiente de implementación.')
    return render(request, 'dashboard/admin_profile_edit.html', {})


# --- VISTAS API (Para uso interno de AJAX/Frontend) ---

@require_http_methods(["POST"])
def login_api(request):
    """API para login (devuelve JSON)."""
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        
        user_data = authenticate_with_service(username, password)
        
        if user_data:
            request.session['is_authenticated'] = True
            request.session['user'] = user_data
            # Devolvemos una respuesta JSON, no DRF Response
            return JsonResponse({'success': True, 'user': user_data, 'message': 'Autenticación exitosa'}, status=200)
        else:
            return JsonResponse({'success': False, 'message': 'Credenciales inválidas'}, status=401)
            
    except Exception as e:
        logger.error(f"Error en login_api: {e}")
        return JsonResponse({'success': False, 'message': 'Error interno del servidor'}, status=500)


@require_http_methods(["POST"])
def logout_api(request):
    """API para logout (devuelve JSON)."""
    if request.session.get('is_authenticated'):
        request.session.flush()
        return JsonResponse({'success': True, 'message': 'Sesión cerrada'}, status=200)
    return JsonResponse({'success': True, 'message': 'No había sesión activa'}, status=200)


@require_http_methods(["POST"])
def register_api(request):
    """API para registro (devuelve JSON)."""
    try:
        data = json.loads(request.body)
        
        register_data = {
            'nombre_usuario': data.get('username'),
            'email': data.get('email'),
            'contrasena': data.get('password'),
            'first_name': data.get('first_name', ''),
            'last_name': data.get('last_name', ''),
            'rol': 'cliente' 
        }

        response = requests.post(
            f"{settings.MICROSERVICES['VENTAS']['BASE_URL']}auth/register/",
            json=register_data,
            headers={'X-API-Key': settings.MICROSERVICES['VENTAS']['API_KEY']},
            timeout=5
        )

        if response.status_code == 201:
            return JsonResponse({'success': True, 'message': 'Registro exitoso. Puede iniciar sesión.'}, status=201)
        else:
            error_data = response.json()
            error_message = error_data.get('detail', 'Error al registrar usuario.')
            # Usamos el código de estado del MS para el response del Gateway
            return JsonResponse({'success': False, 'message': error_message, 'errors': error_data}, status=response.status_code)

    except requests.RequestException as e:
        logger.error(f"Error de conexión al microservicio de registro: {str(e)}")
        return JsonResponse({'success': False, 'message': 'Error de conexión con el servicio de autenticación.'}, status=503)
        
    except Exception as e:
        logger.error(f"Error en register_api: {e}")
        return JsonResponse({'success': False, 'message': 'Error interno del servidor'}, status=500)


def check_auth(request):
    """Verifica el estado de autenticación del usuario."""
    return JsonResponse({
        "is_authenticated": request.session.get("is_authenticated", False), 
        "user": request.session.get("user", {})
    })
