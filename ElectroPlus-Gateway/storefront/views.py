"""
Vistas para la aplicación storefront (frontend público de la tienda).

Este módulo es responsable de renderizar las páginas del catálogo,
página de inicio, detalle de producto y las vistas de carrito y checkout.
Todas las vistas que acceden a datos de productos o categorías
se comunican con el Microservicio de INVENTARIO (8001) y las de
ventas/carrito/checkout con el Microservicio de VENTAS (8002).
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Q
from django.conf import settings
from django.contrib import messages # Necesario para los mensajes de éxito/error
import requests
import json
import logging
from requests.exceptions import RequestException

# Importaciones específicas para la lógica del carrito y checkout
from .cart import Cart
from gateway_app.forms import CheckoutForm 
# Nota: La importación de formularios debe ser desde donde se definieron (gateway_app/forms.py)

logger = logging.getLogger(__name__)

# --- Funciones Auxiliares de Conexión ---

def fetch_data_from_inventario(endpoint, params=None):
    """
    Realiza una petición GET al Microservicio de Inventario (puerto 8001).
    Asegura la inclusión de la clave de seguridad (X-API-Key).
    """
    base_url = settings.MICROSERVICES['INVENTARIO']['BASE_URL']
    api_key = settings.MICROSERVICES['INVENTARIO']['API_KEY']
    url = f"{base_url}{endpoint}"
    
    headers = {
        'X-API-Key': api_key,
        'Content-Type': 'application/json'
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=5)
        response.raise_for_status()  # Lanza una excepción para errores 4xx/5xx
        
        return response.json()
    
    except RequestException as e:
        logger.error(f"Error de conexión con Microservicio INVENTARIO en {url}: {e}")
        return {'results': [], 'count': 0} if endpoint.endswith('/') else None
    
    except Exception as e:
        logger.error(f"Error inesperado al procesar la respuesta de INVENTARIO: {e}")
        return {'results': [], 'count': 0} if endpoint.endswith('/') else None

def make_ventas_request(request, method, endpoint, data=None):
    """
    Función genérica para realizar peticiones al Microservicio de Ventas (puerto 8002).
    Asegura la inclusión del API Key y el token de usuario si está disponible.
    """
    base_url = settings.MICROSERVICES['VENTAS']['BASE_URL']
    url = f"{base_url}{endpoint}"
    
    headers = {
        'X-API-Key': settings.MICROSERVICES['VENTAS']['API_KEY'],
        'Content-Type': 'application/json'
    }

    # Incluir token de autenticación si el usuario está logueado
    if request.session.get('is_authenticated'):
        user_token = request.session['user']['token']
        headers['Authorization'] = f'Token {user_token}'

    try:
        if method == 'get':
            response = requests.get(url, headers=headers, timeout=5)
        elif method == 'post':
            response = requests.post(url, headers=headers, json=data, timeout=5)
        elif method == 'put':
            response = requests.put(url, headers=headers, json=data, timeout=5)
        elif method == 'delete':
            response = requests.delete(url, headers=headers, json=data, timeout=5)
        else:
            raise ValueError("Método HTTP no soportado.")

        response.raise_for_status()
        
        if response.status_code == 204:
            return {}
            
        return response.json()
    
    except RequestException as e:
        logger.error(f"Error de conexión con Microservicio VENTAS en {url} ({method}): {e}")
        return None
    except Exception as e:
        logger.error(f"Error inesperado al procesar la respuesta de VENTAS: {e}")
        return None


# --- Vistas de Catálogo (Mantenidas) ---

def home(request):
    """Vista de la página principal. Muestra productos destacados y categorías."""
    
    categories_data = fetch_data_from_inventario('api/categorias/')
    categories = categories_data.get('results', [])
    
    products_data = fetch_data_from_inventario('api/productos/', params={'limit': 8, 'featured': 'true'})
    featured_products = products_data.get('results', [])
    
    context = {
        'categories': categories,
        'featured_products': featured_products,
    }
    return render(request, 'storefront/home.html', context)

def product_list(request):
    """Lista de todos los productos con filtros, búsqueda y paginación."""
    
    params = {}
    
    search_query = request.GET.get('q')
    category_slug = request.GET.get('category')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    
    if search_query:
        params['search'] = search_query 
    if category_slug:
        params['category_slug'] = category_slug 
    if min_price:
        params['min_price'] = min_price
    if max_price:
        params['max_price'] = max_price
        
    page_number = request.GET.get('page')
    page_size = 12 
    params['page'] = page_number
    params['page_size'] = page_size
    
    products_data = fetch_data_from_inventario('api/productos/', params=params)
    products = products_data.get('results', [])
    
    categories_data = fetch_data_from_inventario('api/categorias/')
    categories = categories_data.get('results', [])

    context = {
        'products': products,
        'categories': categories,
        'search_query': search_query,
    }
    return render(request, 'storefront/product_list.html', context)


def product_detail(request, slug):
    """Detalle de un producto específico."""
    
    product = fetch_data_from_inventario(f'api/productos/slug/{slug}/')
    
    if not product:
        return render(request, 'storefront/product_not_found.html', {'slug': slug}, status=404)
    
    context = {
        'product': product,
    }
    return render(request, 'storefront/product_detail.html', context)

def category(request, slug):
    """Lista de productos filtrados por categoría (Redirección)."""
    return redirect(f'{redirect("storefront:products").url}?category={slug}')

# --- Vistas de Carrito (Refactorizadas) ---

def cart(request):
    """Muestra el carrito de compras, obteniendo datos del Microservicio de Ventas."""
    cart_instance = Cart(request)
    cart_data = cart_instance.get_data()
    
    context = {
        'cart': cart_data,
        'cart_id': cart_instance.cart_id # Útil para debug o scripts JS
    }
    return render(request, 'storefront/cart.html', context)

@require_POST
def cart_add(request):
    """Agrega un producto al carrito (usando el Microservicio)."""
    cart = Cart(request)
    
    try:
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 1))
        # Nota: Asume que el formulario envía 'override_quantity' como 'True' o 'False'
        override = request.POST.get('override_quantity', 'False').lower() == 'true'
        
        if not product_id or quantity <= 0:
            raise ValueError("ID de producto o cantidad inválida.")

        success = cart.add(product_id=product_id, quantity=quantity, override_quantity=override)
        
        if success:
            messages.success(request, 'Producto agregado al carrito con éxito.')
        else:
            messages.error(request, 'Hubo un problema al agregar el producto. Revise el stock.')

    except ValueError as e:
        messages.error(request, f'Error de datos: {e}')
    except Exception as e:
        logger.error(f"Error desconocido al agregar al carrito: {e}")
        messages.error(request, 'Error inesperado al procesar la solicitud.')
        
    # Redirige al carrito
    return redirect('storefront:cart') 

@require_POST
def cart_remove(request):
    """Elimina un producto del carrito (usando el Microservicio)."""
    cart = Cart(request)
    product_id = request.POST.get('product_id')
    
    if product_id:
        success = cart.remove(product_id=product_id)
        if success:
            messages.info(request, 'Producto eliminado del carrito.')
        else:
            messages.error(request, 'Error al eliminar el producto del carrito.')
    
    return redirect('storefront:cart')

@require_POST
def cart_update(request):
    """Actualiza la cantidad de un producto del carrito (usando el Microservicio)."""
    cart = Cart(request)
    product_id = request.POST.get('product_id')
    
    try:
        quantity = int(request.POST.get('quantity', 0))
    except ValueError:
        messages.error(request, 'La cantidad debe ser un número entero.')
        return redirect('storefront:cart')
    
    if product_id and quantity > 0:
        success = cart.update_quantity(product_id=product_id, quantity=quantity)
        if success:
            messages.info(request, 'Cantidad del producto actualizada.')
        else:
            messages.error(request, 'Error al actualizar la cantidad del producto. Revise el stock.')
    elif quantity == 0:
        cart.remove(product_id)
        messages.info(request, 'Producto eliminado del carrito.')
    else:
        messages.error(request, 'Cantidad o ID de producto inválido.')

    return redirect('storefront:cart')


# --- Vistas de Checkout (Implementadas) ---

def checkout(request):
    """Proceso de checkout. Muestra el formulario de envío y el resumen del carrito."""
    cart_instance = Cart(request)
    cart_data = cart_instance.get_data()

    if not cart_data.get('items'):
        messages.warning(request, 'Su carrito está vacío. Agregue productos para continuar.')
        return redirect('storefront:cart')

    # Intentar prellenar el formulario con datos de sesión (si están disponibles de gateway_app/views_auth.py)
    initial_data = {}
    if request.session.get('is_authenticated'):
        user_info = request.session['user']
        # Se asumen nombres de campo similares a CheckoutForm
        initial_data = {
            'shipping_name': user_info.get('nombre_completo', ''),
            'email': user_info.get('email', ''),
            'phone': user_info.get('phone', ''),
            # Aquí podrías mapear otros campos de dirección si estuvieran disponibles
        }
    
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            # Guardar datos del formulario en la sesión temporalmente
            request.session['checkout_data'] = form.cleaned_data
            request.session.modified = True
            return redirect('storefront:checkout_confirm')
    else:
        form = CheckoutForm(initial=initial_data)

    context = {
        'cart': cart_data,
        'form': form,
        'cart_id': cart_instance.cart_id
    }
    return render(request, 'storefront/checkout.html', context)


def checkout_confirm(request):
    """Confirmación final de la orden y creación de la orden en el microservicio."""
    cart_instance = Cart(request)
    cart_data = cart_instance.get_data()
    checkout_data = request.session.get('checkout_data')

    if not cart_data.get('items') or not checkout_data:
        messages.warning(request, 'El proceso de compra no está completo. Vuelva al checkout.')
        return redirect('storefront:checkout')

    if request.method == 'POST':
        # 1. Preparar la estructura de la orden para el microservicio
        order_payload = {
            'cart_id': cart_instance.cart_id,
            # Obtener el ID del usuario autenticado si existe
            'user_id': request.session.get('user', {}).get('id'), 
            # Añadir los campos de envío/contacto del formulario
            **checkout_data,
            'payment_method': request.POST.get('payment_method', 'Efectivo') # Asume un campo de pago en el formulario
        }
        
        # 2. Llamar al microservicio para crear la orden (POST)
        # Endpoint: /api/ordenes/crear/
        new_order = make_ventas_request(request, 'post', 'api/ordenes/crear/', data=order_payload)

        if new_order and new_order.get('id'):
            # 3. Éxito: Limpiar el carrito local y la sesión de checkout
            cart_instance.clear() 
            if 'checkout_data' in request.session:
                del request.session['checkout_data']
                request.session.modified = True

            messages.success(request, f'¡Gracias! Su pedido #{new_order["id"]} ha sido creado con éxito.')
            return render(request, 'storefront/checkout_success.html', {'order': new_order})
        else:
            messages.error(request, 'Error al procesar el pedido. El servicio de ventas no pudo crear la orden.')
            return redirect('storefront:checkout')

    context = {
        'cart': cart_data,
        'checkout_data': checkout_data,
    }
    return render(request, 'storefront/checkout_confirm.html', context)

# --- Vistas de Información ---

def search(request):
    """Redirige la búsqueda a la vista de lista de productos."""
    query = request.GET.get('q', '')
    if query:
        return redirect(f'{redirect("storefront:products").url}?q={query}')
    return redirect('storefront:products')

def ofertas(request):
    """Muestra productos en oferta."""
    params = {'offer': 'true', 'page_size': 20}
    products_data = fetch_data_from_inventario('api/productos/', params=params)
    
    context = {
        'products': products_data.get('results', []),
        'title': 'Ofertas del Día'
    }
    return render(request, 'storefront/product_list.html', context) 


def about(request):
    """Página Sobre Nosotros."""
    return render(request, 'storefront/about.html')

def contact(request):
    """Página de Contacto."""
    return render(request, 'storefront/contact.html')

def faq(request):
    """Página de Preguntas Frecuentes."""
    return render(request, 'storefront/faq.html')

def shipping(request):
    """Página de Envíos."""
    return render(request, 'storefront/shipping.html')

def returns(request):
    """Página de Devoluciones."""
    return render(request, 'storefront/returns.html')

def warranty(request):
    """Página de Garantía."""
    return render(request, 'storefront/warranty.html')

def privacy(request):
    """Página de Privacidad."""
    return render(request, 'storefront/privacy.html')

def terms(request):
    """Página de Términos y Condiciones."""
    return render(request, 'storefront/terms.html')

# --- Vistas de Usuario (DEBEN SER MANEJADAS PRINCIPALMENTE POR GATEWAY_APP) ---

def profile(request):
    """Muestra el perfil del usuario."""
    return redirect('gateway_app:customer_dashboard') # Redirige al dashboard del cliente

@login_required
def orders(request):
    """Muestra la lista de pedidos del usuario."""
    # Esta vista debe llamar al Microservicio de VENTAS usando el token de Auth.
    # Por ahora, se redirige al dashboard del cliente, que ya implementa esta lógica.
    return redirect('gateway_app:customer_dashboard') 

@login_required
def order_detail(request, order_id):
    """Detalle de un pedido específico."""
    # Esta vista debe llamar al Microservicio de VENTAS para obtener el detalle.
    order_data = make_ventas_request(request, 'get', f'api/ordenes/{order_id}/')
    
    if not order_data:
        messages.error(request, 'No se pudo encontrar el detalle del pedido o hubo un error de conexión.')
        return redirect('storefront:orders')

    return render(request, 'storefront/order_detail.html', {'order': order_data})
