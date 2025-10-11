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
from django.http import JsonResponse # Importación añadida para compatibilidad si se necesitara
# Se mantienen los imports de DRF para las funciones _api
from rest_framework.response import Response
from rest_framework import status
import requests
import logging
import json

# IMPORTANTE: Se actualiza el import para usar CustomLoginForm según el archivo forms.py
from .forms import CustomLoginForm, RegisterForm

logger = logging.getLogger(__name__)

def authenticate_with_service(username_or_id, password):
    """
    Autentica el usuario contra el servicio de ventas.
    
    Mapea los nombres de variables locales (username, password) a los esperados 
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
            # Se devuelven los datos crudos del usuario autenticado
            return {
                'id': data['id'],
                'nombre_usuario': data['nombre_usuario'],
                'rol': data['rol'],
                'token': data['token']
            }
        
        return None
        
    except requests.RequestException:
        logger.error("Error al autenticar con el servicio de ventas", exc_info=True)
        return None

@require_http_methods(["POST"])
def login_api(request):
    """API para login de usuarios (usando JSON body)"""
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return Response({
                'success': False,
                'error': 'Nombre de usuario y contraseña son requeridos'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # Llamada a la función de autenticación
        user = authenticate_with_service(username, password)
        
        if user:
            # Almacenar en la sesión de Django
            request.session['user'] = user
            request.session['is_authenticated'] = True 
            
            return Response({
                'success': True,
                'user': {
                    'id': user['id'],
                    'username': user['nombre_usuario'],
                    'role': user['rol']
                }
            })
            
        return Response({
            'success': False,
            'error': 'Credenciales inválidas'
        }, status=status.HTTP_401_UNAUTHORIZED)
        
    except json.JSONDecodeError:
        return Response({
            'success': False,
            'error': 'Datos JSON inválidos'
        }, status=status.HTTP_400_BAD_REQUEST)

@require_http_methods(["POST"])
def logout_api(request):
    """API para logout de usuarios"""
    logout(request)
    return Response({'success': True})

@require_http_methods(["GET"])
def check_auth(request):
    """API para verificar estado de autenticación (DRF Response)"""
    user = request.session.get('user')
    
    if user and request.session.get('is_authenticated'):
        return Response({
            'success': True,
            'user': {
                'id': user['id'],
                'username': user['nombre_usuario'],
                'role': user['rol']
            }
        })
        
    # Usamos la respuesta de DRF con 401 para API
    return Response({
        'success': False,
        'error': 'Usuario no autenticado'
    }, status=status.HTTP_401_UNAUTHORIZED)

@require_http_methods(["POST"])
def register_api(request):
    """API para registro de nuevos clientes (usando JSON body)"""
    try:
        data = json.loads(request.body)
        
        # Validación de campos mínimos (usando los nombres que espera el API)
        if not all(k in data for k in ['first_name', 'email', 'username', 'password']):
             return Response({
                'success': False,
                'error': 'Faltan campos requeridos (nombre, email, username, password)'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            response = requests.post(
                f"{settings.MICROSERVICES['VENTAS']['BASE_URL']}api/clientes/registro/",
                json={
                    # Mapeo a los nombres esperados por el microservicio
                    'nombre': data.get('first_name') or data.get('nombre', ''),
                    'email': data['email'],
                    'nombre_usuario': data['username'],
                    'contrasena': data['password']
                },
                headers={'X-API-Key': settings.MICROSERVICES['VENTAS']['API_KEY']},
                timeout=5
            )
            
            if response.status_code == 201:
                return Response({
                    'success': True,
                    'message': 'Registro exitoso'
                })
            else:
                error_data = response.json()
                error_msg = error_data.get('detail', 'Error en el registro')
                return Response({
                    'success': False,
                    'error': error_msg
                }, status=response.status_code)
                
        except requests.RequestException as e:
            logger.error(f"Error al registrar cliente: {str(e)}")
            return Response({
                'success': False,
                'error': 'Error de conexión: El servicio de registro no está disponible'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
    except json.JSONDecodeError:
        return Response({
            'success': False,
            'error': 'Datos JSON inválidos'
        }, status=status.HTTP_400_BAD_REQUEST)

@require_http_methods(["GET", "POST"])
def register_view(request):
    """Vista de registro de clientes (usando formularios tradicionales de Django)"""
    if request.method == "POST":
        form = RegisterForm(request.POST) 
        if form.is_valid():
            
            # Mapeo de campos del formulario a la estructura esperada por el microservicio
            data_to_send = {
                'nombre': form.cleaned_data['first_name'],
                'email': form.cleaned_data['email'],
                'nombre_usuario': form.cleaned_data['username'],
                'contrasena': form.cleaned_data['password']
            }
            
            try:
                response = requests.post(
                    f"{settings.MICROSERVICES['VENTAS']['BASE_URL']}api/clientes/registro/",
                    json=data_to_send,
                    headers={'X-API-Key': settings.MICROSERVICES['VENTAS']['API_KEY']},
                    timeout=5
                )
                
                if response.status_code == 201:
                    messages.success(request, '¡Registro exitoso! Ya puedes iniciar sesión.')
                    return redirect('login')
                else:
                    error_data = response.json()
                    # Muestra un mensaje de error general o específico del microservicio
                    error_msg = error_data.get('detail', 'Ocurrió un error al registrar el usuario. Intente con otro nombre de usuario o email.')
                    messages.error(request, error_msg)
            
            except requests.RequestException as e:
                logger.error(f"Error al registrar cliente desde register_view: {str(e)}")
                messages.error(request, 'Error de conexión con el servicio. Intente más tarde.')
                
        # Si el formulario no es válido o hay un error de microservicio, se renderiza de nuevo con el formulario y errores.
    else:
        form = RegisterForm()
    
    return render(request, 'auth/register.html', {'form': form})

@require_http_methods(["GET", "POST"])
def login_view(request):
    """Vista de login (usando formularios tradicionales de Django)"""
    if request.method == "POST":
        # Usamos CustomLoginForm
        # El argumento 'request' es necesario porque CustomLoginForm hereda de AuthenticationForm
        form = CustomLoginForm(request, data=request.POST) 
        if form.is_valid():
            # **AJUSTE CRÍTICO:** Los campos ahora son 'username' y 'password'
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            
            # user_type se infiere del nombre de usuario si es necesario
            user_type = 'customer'
            # La lógica de prefijos para empleados se mueve a la verificación de rol
            
            remember = form.cleaned_data.get('remember', False)
            
            user_data = authenticate_with_service(username, password)
            
            if user_data:
                # 1. Verificar Rol esperado (se mantiene la lógica original de prefijos/roles)
                # Esta lógica de prefijo (EMP) debería estar idealmente en el microservicio.
                expected_role = 'empleado' if username.startswith('EMP') else 'cliente'
                
                if user_data['rol'] != expected_role:
                    messages.error(request, 'Tipo de usuario o credenciales incorrectas para este acceso.')
                    return render(request, 'auth/login.html', {'form': form})
                
                # 2. Establecer Sesión
                request.session['user'] = user_data
                request.session['is_authenticated'] = True
                
                # 3. Control de "Recordarme"
                if remember:
                    request.session.set_expiry(30 * 24 * 60 * 60)  # 30 días
                else:
                    request.session.set_expiry(0)  # Sesión de navegador
                
                messages.success(request, f'¡Bienvenido de nuevo, {user_data["nombre_usuario"]}!')
                
                # 4. Redirección
                if user_data['rol'] == 'empleado':
                    return redirect('employee_dashboard')
                else:
                    return redirect('customer_dashboard')
            else:
                # Error de autenticación del servicio
                messages.error(request, 'Usuario o contraseña incorrectos.')
        # Si el formulario no es válido, los errores se mostrarán en la plantilla
    else:
        # Usamos CustomLoginForm
        form = CustomLoginForm()
    
    return render(request, 'auth/login.html', {'form': form})

def logout_view(request):
    """Vista de logout"""
    request.session.flush()
    messages.info(request, 'Has cerrado sesión correctamente')
    return redirect('login')

def login_required(view_func):
    """Decorador personalizado de login_required para microservicios"""
    def wrapper(request, *args, **kwargs):
        if not request.session.get('is_authenticated'):
            messages.error(request, 'Debe iniciar sesión para acceder a esta página')
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper

@login_required
def dashboard_view(request):
    """Vista del dashboard principal"""
    rol = request.session['user']['rol']
    if rol == 'empleado':
        return redirect('employee_dashboard')
    else:
        return redirect('customer_dashboard')

@login_required
def admin_dashboard(request):
    """Vista del dashboard de administrador. Se asume que solo ciertos empleados tienen acceso."""
    try:
        # Obtener estadísticas administrativas de VENTAS
        ventas_stats_response = requests.get(
            f"{settings.MICROSERVICES['VENTAS']['BASE_URL']}admin/estadisticas/",
            headers={
                'X-API-Key': settings.MICROSERVICES['VENTAS']['API_KEY'],
                'Authorization': f'Token {request.session["user"]["token"]}'
            },
            timeout=5
        )
        
        # Obtener estadísticas administrativas de INVENTARIO
        inventario_stats_response = requests.get(
            f"{settings.MICROSERVICES['INVENTARIO']['BASE_URL']}admin/estadisticas/",
            headers={'X-API-Key': settings.MICROSERVICES['INVENTARIO']['API_KEY']},
            timeout=5
        )
        
        if ventas_stats_response.status_code == 200 and inventario_stats_response.status_code == 200:
            context = {
                'ventas_stats': ventas_stats_response.json(),
                'inventario_stats': inventario_stats_response.json()
            }
            return render(request, 'dashboard/admin_dashboard.html', context)
        else:
            # Mensaje de error detallado sobre qué servicio falló
            error_msg = 'Error al cargar estadísticas.'
            if ventas_stats_response.status_code != 200:
                 error_msg += f" (Ventas: HTTP {ventas_stats_response.status_code})"
            if inventario_stats_response.status_code != 200:
                 error_msg += f" (Inventario: HTTP {inventario_stats_response.status_code})"
                 
            messages.error(request, error_msg)
            return render(request, 'dashboard/admin_dashboard.html', {})
            
    except requests.RequestException as e:
        logger.error(f"Error al obtener estadísticas del administrador: {str(e)}")
        messages.error(request, 'Error de conexión con los servicios. Intente más tarde.')
        return render(request, 'dashboard/admin_dashboard.html', {})

@login_required
def employee_dashboard(request):
    """Vista del dashboard de empleado"""
    if request.session['user']['rol'] != 'empleado':
        messages.error(request, 'Acceso no autorizado: Solo empleados.')
        return redirect('dashboard')
        
    try:
        # Obtener datos del empleado (perfil)
        employee_response = requests.get(
            f"{settings.MICROSERVICES['VENTAS']['BASE_URL']}empleados/perfil/",
            headers={
                'X-API-Key': settings.MICROSERVICES['VENTAS']['API_KEY'],
                'Authorization': f'Token {request.session["user"]["token"]}'
            },
            timeout=5
        )
        
        # Obtener tareas pendientes
        tasks_response = requests.get(
            f"{settings.MICROSERVICES['VENTAS']['BASE_URL']}empleados/tareas/",
            headers={
                'X-API-Key': settings.MICROSERVICES['VENTAS']['API_KEY'],
                'Authorization': f'Token {request.session["user"]["token"]}'
            },
            timeout=5
        )
        
        context = {}
        if employee_response.status_code == 200:
            context['employee_info'] = employee_response.json()
        if tasks_response.status_code == 200:
            context['tasks'] = tasks_response.json()
            
        return render(request, 'dashboard/employee_dashboard.html', context)
            
    except requests.RequestException as e:
        logger.error(f"Error al obtener datos del empleado: {str(e)}")
        messages.error(request, 'Error de conexión con los servicios. Intente más tarde.')
        return render(request, 'dashboard/employee_dashboard.html', {})

@login_required
def customer_dashboard(request):
    """Vista del dashboard de cliente"""
    if request.session['user']['rol'] != 'cliente':
        messages.error(request, 'Acceso no autorizado: Solo clientes.')
        return redirect('dashboard')
        
    try:
        # Obtener datos del cliente (perfil)
        customer_response = requests.get(
            f"{settings.MICROSERVICES['VENTAS']['BASE_URL']}clientes/perfil/",
            headers={
                'X-API-Key': settings.MICROSERVICES['VENTAS']['API_KEY'],
                'Authorization': f'Token {request.session["user"]["token"]}'
            },
            timeout=5
        )
        
        # Obtener historial de pedidos
        orders_response = requests.get(
            f"{settings.MICROSERVICES['VENTAS']['BASE_URL']}clientes/pedidos/",
            headers={
                'X-API-Key': settings.MICROSERVICES['VENTAS']['API_KEY'],
                'Authorization': f'Token {request.session["user"]["token"]}'
            },
            timeout=5
        )
        
        context = {}
        if customer_response.status_code == 200:
            context['customer_info'] = customer_response.json()
        if orders_response.status_code == 200:
            context['orders'] = orders_response.json()
            
        return render(request, 'dashboard/customer_dashboard.html', context)
            
    except requests.RequestException as e:
        logger.error(f"Error al obtener datos del cliente: {str(e)}")
        messages.error(request, 'Error de conexión con los servicios. Intente más tarde.')
        return render(request, 'dashboard/customer_dashboard.html', {})
