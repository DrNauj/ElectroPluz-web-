"""
Vistas para la aplicación storefront (frontend público de la tienda).

Este módulo es responsable de renderizar las páginas del catálogo,
página de inicio, detalle de producto y las vistas de carrito y checkout.
Todas las vistas que acceden a datos de productos o categorías
se comunican con el Microservicio de INVENTARIO (8001) y las de
ventas/carrito con el Microservicio de VENTAS (8002).
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Q
from django.conf import settings
import requests
import json
import logging
from requests.exceptions import RequestException

# Nota: Hemos eliminado los imports de modelos locales (Product, Category, etc.)
# ya que ahora obtenemos los datos de los Microservicios.
# from gateway_app.models import Product, Category, Order, OrderItem, Profile
# from gateway_app.forms import ProfileForm, CheckoutForm

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
        
        # El endpoint de lista (como /api/productos/) generalmente devuelve una lista o un objeto con resultados.
        return response.json()
    
    except RequestException as e:
        logger.error(f"Error de conexión con Microservicio INVENTARIO en {url}: {e}")
        # En caso de error, devolvemos datos vacíos para que la página no colapse
        return {'results': [], 'count': 0} if endpoint.endswith('/') else None
    
    except Exception as e:
        logger.error(f"Error inesperado al procesar la respuesta de INVENTARIO: {e}")
        return {'results': [], 'count': 0} if endpoint.endswith('/') else None

# --- Vistas de Catálogo ---

def home(request):
    """Vista de la página principal. Muestra productos destacados y categorías."""
    
    # Obtener categorías
    categories_data = fetch_data_from_inventario('api/categorias/')
    categories = categories_data.get('results', [])
    
    # Obtener productos (ej: los 8 primeros destacados, si el microservicio lo soporta)
    # Si el microservicio no tiene el filtro 'featured', simplemente traemos los 8 primeros
    products_data = fetch_data_from_inventario('api/productos/', params={'limit': 8, 'featured': 'true'})
    featured_products = products_data.get('results', [])
    
    context = {
        'categories': categories,
        'featured_products': featured_products,
    }
    return render(request, 'storefront/home.html', context)

def product_list(request):
    """Lista de todos los productos con filtros, búsqueda y paginación."""
    
    # Parámetros para enviar al microservicio
    params = {}
    
    # 1. Búsqueda y Filtros
    search_query = request.GET.get('q')
    category_slug = request.GET.get('category')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    
    if search_query:
        params['search'] = search_query # Asume que el microservicio tiene un filtro 'search'
    if category_slug:
        params['category_slug'] = category_slug # Asume que el microservicio filtra por slug
    if min_price:
        params['min_price'] = min_price
    if max_price:
        params['max_price'] = max_price
        
    # 2. Paginación
    page_number = request.GET.get('page')
    page_size = 12 # Hardcodeado, pero podría ser un setting
    params['page'] = page_number
    params['page_size'] = page_size
    
    # Obtener productos del microservicio
    products_data = fetch_data_from_inventario('api/productos/', params=params)
    products = products_data.get('results', [])
    
    # Nota: La paginación real debe manejarla el microservicio (Django REST Framework lo hace)
    # y el Gateway solo pasa el JSON al template.
    
    categories_data = fetch_data_from_inventario('api/categorias/')
    categories = categories_data.get('results', [])

    context = {
        'products': products,
        'categories': categories,
        'search_query': search_query,
        # Si el microservicio devuelve info de paginación, pasarla aquí
    }
    return render(request, 'storefront/product_list.html', context)


def product_detail(request, slug):
    """Detalle de un producto específico."""
    
    # Asume que el microservicio tiene un endpoint para obtener el producto por slug
    product = fetch_data_from_inventario(f'api/productos/slug/{slug}/')
    
    if not product:
        # Aquí deberías manejar un 404 real si el producto no existe
        # Pero dado que la función auxiliar devuelve None en caso de error,
        # lo manejamos como un error de conexión/producto no encontrado.
        return render(request, 'storefront/product_not_found.html', {'slug': slug}, status=404)
    
    context = {
        'product': product,
    }
    return render(request, 'storefront/product_detail.html', context)

def category(request, slug):
    """Lista de productos filtrados por categoría."""
    
    # La vista product_list ya puede manejar la lógica de categoría.
    # Simplemente redirigimos con el parámetro de filtro.
    return redirect(f'{redirect("products").url}?category={slug}')

# Vistas de Carrito (pendientes de integración con Microservicio de VENTAS)
# Estas vistas necesitan la misma refactorización que las de catálogo.

# def cart(request):
#     """Muestra el carrito de compras."""
#     # Lógica actual que usa sesión local y ORM (DEBE SER REEMPLAZADA)
#     return render(request, 'storefront/cart.html', {'cart': Cart(request)})

# def checkout(request):
#     """Proceso de checkout (DEBE SER REEMPLAZADA)."""
#     pass # Implementación pendiente

# def checkout_confirm(request):
#     """Confirmación final de la orden (DEBE SER REEMPLAZADA)."""
#     pass # Implementación pendiente

# --- Vistas de Información ---

def search(request):
    """Redirige la búsqueda a la vista de lista de productos."""
    query = request.GET.get('q', '')
    if query:
        # Redirige a product_list con el parámetro 'q'
        return redirect(f'{redirect("products").url}?q={query}')
    return redirect('products')

def ofertas(request):
    """Muestra productos en oferta."""
    # Simplemente llama al microservicio con un filtro de oferta.
    params = {'offer': 'true', 'page_size': 20}
    products_data = fetch_data_from_inventario('api/productos/', params=params)
    
    context = {
        'products': products_data.get('results', []),
        'title': 'Ofertas del Día'
    }
    return render(request, 'storefront/product_list.html', context) # Reutiliza la plantilla de lista


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

# --- Vistas de Usuario (DEBEN SER MOVIDAS AL GATEWAY o ya están en gateway_app) ---

# Nota: Las vistas de perfil (profile, orders, etc.) ya están o deberían estar en gateway_app/views.py
# porque dependen del token de usuario. Si las dejas aquí, asegúrate de protegerlas
# y usar el token de la sesión para las llamadas a microservicios.

# Por ahora, se mantendrán las vistas de usuario simples sin lógica de microservicio
# ya que el foco está en el catálogo.

def profile(request):
    """Muestra el perfil del usuario."""
    # Esta vista generalmente es manejada por gateway_app/views.py o un redirect.
    return redirect('gateway_app:customer_dashboard') # Asumiendo que la tienes en el gateway_app

def orders(request):
    """Muestra la lista de pedidos del usuario."""
    # Lógica de microservicio de VENTAS pendiente
    return render(request, 'storefront/orders.html')

def order_detail(request, order_id):
    """Detalle de un pedido específico."""
    # Lógica de microservicio de VENTAS pendiente
    return render(request, 'storefront/order_detail.html', {'order_id': order_id})
