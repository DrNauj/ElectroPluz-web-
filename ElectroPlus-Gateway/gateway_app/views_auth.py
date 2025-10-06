from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import logout
from django.conf import settings
from django.views.decorators.http import require_http_methods
from rest_framework.response import Response
from rest_framework import status
import requests
import logging
from .forms import LoginForm, RegisterForm

logger = logging.getLogger(__name__)

def authenticate_with_service(nombre_usuario, contrasena):
    """
    Autentica el usuario contra el servicio de ventas
    """
    try:
        response = requests.post(
            f"{settings.MICROSERVICES['VENTAS']['BASE_URL']}auth/login/",
            json={
                'nombre_usuario': nombre_usuario,
                'contrasena': contrasena
            },
            headers={
                'X-API-Key': settings.MICROSERVICES['VENTAS']['API_KEY']
            }
        )
        
        if response.status_code == 200:
            data = response.json()
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

@require_http_methods(["GET", "POST"])
def register_view(request):
    """Vista de registro de nuevos clientes"""
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            try:
                response = requests.post(
                    f"{settings.MICROSERVICES['VENTAS']['BASE_URL']}api/clientes/registro/",
                    json={
                        'nombre': form.cleaned_data['nombre'],
                        'email': form.cleaned_data['email'],
                        'nombre_usuario': form.cleaned_data['username'],
                        'contrasena': form.cleaned_data['password1']
                    },
                    headers={'X-API-Key': settings.MICROSERVICES['VENTAS']['API_KEY']}
                )

                if response.status_code == 201:
                    messages.success(request, "¡Registro exitoso! Por favor inicie sesión.")
                    return redirect('login')
                else:
                    error_data = response.json()
                    messages.error(request, error_data.get('detail', 'Error en el registro'))
            except requests.RequestException as e:
                logger.error(f"Error al registrar cliente: {str(e)}")
                messages.error(request, "Error al procesar el registro. Por favor, intente más tarde.")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{error}")
    else:
        form = RegisterForm()

    return render(request, 'auth/register.html', {'form': form})

@require_http_methods(["GET", "POST"])
def login_view(request):
    """Vista de login"""
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            nombre_usuario = form.cleaned_data['nombre_usuario']
            contrasena = form.cleaned_data['contrasena']
            user_type = form.cleaned_data.get('user_type', 'customer')
            remember = form.cleaned_data.get('remember', False)
            
            if user_type == 'employee' and not nombre_usuario.startswith('EMP'):
                nombre_usuario = f'EMP{nombre_usuario}'
            
            user_data = authenticate_with_service(nombre_usuario, contrasena)
            
            if user_data:
                expected_role = 'empleado' if user_type == 'employee' else 'cliente'
                if user_data['rol'] != expected_role:
                    messages.error(request, 'Tipo de usuario incorrecto')
                    return render(request, 'auth/login.html', {'form': form})
                
                request.session['user'] = user_data
                request.session['is_authenticated'] = True
                
                if remember:
                    request.session.set_expiry(30 * 24 * 60 * 60)
                else:
                    request.session.set_expiry(0)
                
                messages.success(request, f'¡Bienvenido de nuevo, {user_data["nombre_usuario"]}!')
                
                if user_data['rol'] == 'empleado':
                    return redirect('employee_dashboard')
                else:
                    return redirect('customer_dashboard')
            else:
                messages.error(request, 'Usuario o contraseña incorrectos')
    else:
        form = LoginForm()
    
    return render(request, 'auth/login.html', {'form': form})

def logout_view(request):
    """Vista de logout"""
    logout(request)
    messages.info(request, 'Has cerrado sesión correctamente')
    return redirect('login')

def login_required(view_func):
    """Decorador personalizado de login_required para microservicios"""
    def wrapper(request, *args, **kwargs):
        if not request.session.get('is_authenticated'):
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper

def dashboard_view(request):
    """Vista del dashboard principal"""
    if not request.session.get('is_authenticated'):
        return redirect('login')
        
    # Redireccionar según el rol del usuario
    rol = request.session['user']['rol']
    if rol == 'empleado':
        return redirect('employee_dashboard')
    else:
        return redirect('customer_dashboard')

@login_required
def admin_dashboard(request):
    """Vista del dashboard de administrador"""
    try:
        # Obtener estadísticas administrativas
        ventas_stats_response = requests.get(
            f"{settings.MICROSERVICES['VENTAS']['BASE_URL']}admin/estadisticas/",
            headers={
                'X-API-Key': settings.MICROSERVICES['VENTAS']['API_KEY'],
                'Authorization': f'Token {request.session["user"]["token"]}'
            }
        )
        
        inventario_stats_response = requests.get(
            f"{settings.MICROSERVICES['INVENTARIO']['BASE_URL']}admin/estadisticas/",
            headers={'X-API-Key': settings.MICROSERVICES['INVENTARIO']['API_KEY']}
        )
        
        if ventas_stats_response.status_code == 200 and inventario_stats_response.status_code == 200:
            context = {
                'ventas_stats': ventas_stats_response.json(),
                'inventario_stats': inventario_stats_response.json()
            }
            return render(request, 'dashboard/admin_dashboard.html', context)
        else:
            messages.error(request, 'Error al cargar las estadísticas')
            return render(request, 'dashboard/admin_dashboard.html', {})
            
    except requests.RequestException as e:
        logger.error(f"Error al obtener estadísticas del administrador: {str(e)}")
        messages.error(request, 'Error de conexión con los servicios')
        return render(request, 'dashboard/admin_dashboard.html', {})

@login_required
def employee_dashboard(request):
    """Vista del dashboard de empleado"""
    if request.session['user']['rol'] != 'empleado':
        messages.error(request, 'Acceso no autorizado')
        return redirect('dashboard')
        
    try:
        # Obtener datos del empleado
        employee_response = requests.get(
            f"{settings.MICROSERVICES['VENTAS']['BASE_URL']}empleados/perfil/",
            headers={
                'X-API-Key': settings.MICROSERVICES['VENTAS']['API_KEY'],
                'Authorization': f'Token {request.session["user"]["token"]}'
            }
        )
        
        # Obtener tareas pendientes
        tasks_response = requests.get(
            f"{settings.MICROSERVICES['VENTAS']['BASE_URL']}empleados/tareas/",
            headers={
                'X-API-Key': settings.MICROSERVICES['VENTAS']['API_KEY'],
                'Authorization': f'Token {request.session["user"]["token"]}'
            }
        )
        
        if employee_response.status_code == 200 and tasks_response.status_code == 200:
            context = {
                'employee_info': employee_response.json(),
                'tasks': tasks_response.json()
            }
            return render(request, 'dashboard/employee_dashboard.html', context)
        else:
            messages.error(request, 'Error al cargar la información')
            return render(request, 'dashboard/employee_dashboard.html', {})
            
    except requests.RequestException as e:
        logger.error(f"Error al obtener datos del empleado: {str(e)}")
        messages.error(request, 'Error de conexión con los servicios')
        return render(request, 'dashboard/employee_dashboard.html', {})

@login_required
def customer_dashboard(request):
    """Vista del dashboard de cliente"""
    if request.session['user']['rol'] != 'cliente':
        messages.error(request, 'Acceso no autorizado')
        return redirect('dashboard')
        
    try:
        # Obtener datos del cliente
        customer_response = requests.get(
            f"{settings.MICROSERVICES['VENTAS']['BASE_URL']}clientes/perfil/",
            headers={
                'X-API-Key': settings.MICROSERVICES['VENTAS']['API_KEY'],
                'Authorization': f'Token {request.session["user"]["token"]}'
            }
        )
        
        # Obtener historial de pedidos
        orders_response = requests.get(
            f"{settings.MICROSERVICES['VENTAS']['BASE_URL']}clientes/pedidos/",
            headers={
                'X-API-Key': settings.MICROSERVICES['VENTAS']['API_KEY'],
                'Authorization': f'Token {request.session["user"]["token"]}'
            }
        )
        
        if customer_response.status_code == 200 and orders_response.status_code == 200:
            context = {
                'customer_info': customer_response.json(),
                'orders': orders_response.json()
            }
            return render(request, 'dashboard/customer_dashboard.html', context)
        else:
            messages.error(request, 'Error al cargar la información')
            return render(request, 'dashboard/customer_dashboard.html', {})
            
    except requests.RequestException as e:
        logger.error(f"Error al obtener datos del cliente: {str(e)}")
        messages.error(request, 'Error de conexión con los servicios')
        return render(request, 'dashboard/customer_dashboard.html', {})