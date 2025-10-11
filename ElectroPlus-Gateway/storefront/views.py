"""
Vistas del frontend público (storefront).

Este módulo implementa la lógica de presentación, actuando como cliente de los
microservicios de Inventario y Ventas. Se han eliminado todas las dependencias
a los modelos locales de 'gateway_app'.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.conf import settings
import requests
import json
import logging

# Importamos las utilidades de cart y forms (asumiendo que forms.py está en gateway_app)
from .cart import Cart
from gateway_app.forms import CheckoutForm # Usamos el formulario de envío (sin ModelForm)

logger = logging.getLogger(__name__)

# --- Funciones de Utilidad de Microservicios ---

def fetch_data_from_inventario(endpoint, params=None):
    """Realiza una solicitud GET al Microservicio de Inventario."""
    try:
        url = f"{settings.MICROSERVICES['INVENTARIO']['BASE_URL']}{endpoint}"
        response = requests.get(
            url,
            params=params,
            headers={'X-API-Key': settings.MICROSERVICES['INVENTARIO']['API_KEY']},
            timeout=5
        )
        response.raise_for_status() # Lanza error para códigos 4xx/5xx
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error al conectar con Inventario en {url}: {e}")
        return None

def fetch_data_from_ventas(endpoint, request_session_token=None, method='GET', data=None):
    """Realiza una solicitud a Microservicio de Ventas."""
    try:
        url = f"{settings.MICROSERVICES['VENTAS']['BASE_URL']}{endpoint}"
        headers = {
            'X-API-Key': settings.MICROSERVICES['VENTAS']['API_KEY'],
            'Content-Type': 'application/json' if data is not None else 'application/json',
        }
        
        # Si se proporciona un token de sesión (para operaciones autenticadas)
        if request_session_token:
            headers['Authorization'] = f'Token {request_session_token}'

        if method == 'GET':
            response = requests.get(url, headers=headers, params=data, timeout=5)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=data, timeout=5)
        
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.HTTPError as e:
        logger.warning(f"Error HTTP en Ventas ({e.response.status_code}): {e.response.text}")
        # Devuelve el cuerpo del error si es un 4xx/5xx (ej: 400 Bad Request)
        try:
            return {'error': e.response.json(), 'status_code': e.response.status_code}
        except json.JSONDecodeError:
            return {'error': f"Error en el microservicio: {e.response.text}", 'status_code': e.response.status_code}
    except requests.exceptions.RequestException as e:
        logger.error(f"Error al conectar con Ventas en {url}: {e}")
        return None

# --- Vistas de Catálogo (Usa Microservicio de Inventario) ---

def home(request):
    """Vista de la página principal (Home)."""
    # Usamos el endpoint que devuelve categorías y productos destacados
    data = fetch_data_from_inventario('catalogo/home/') 
    
    context = {
        'categories': data.get('categories', []) if data else [],
        'featured_products': data.get('featured_products', []) if data else [],
    }
    # Ruta de template ajustada
    return render(request, 'storefront/home.html', context) 

def product_list(request):
    """Lista de todos los productos con filtros y ordenamiento."""
    params = {
        'category_slug': request.GET.get('category'),
        'min_price': request.GET.get('min_price'),
        'max_price': request.GET.get('max_price'),
        'search': request.GET.get('q'),
        'order_by': request.GET.get('sort'),
        'page': request.GET.get('page'),
    }
    
    # Usamos el endpoint que acepta todos los parámetros de filtrado
    data = fetch_data_from_inventario('catalogo/productos/', params=params)
    categories = fetch_data_from_inventario('catalogo/categorias/') # Para mostrar el menú de filtros
    
    context = {
        'products': data.get('products', []) if data else [],
        'categories': categories if categories else [],
        'paginator_data': data.get('paginator', {}) if data else {}, # Contiene info de paginación
        'current_category_slug': params['category_slug']
    }
    # Ruta de template ajustada
    return render(request, 'storefront/product_list.html', context)

def product_detail(request, slug):
    """Detalle de un producto específico."""
    product_data = fetch_data_from_inventario(f'catalogo/productos/{slug}/')
    
    if not product_data or 'error' in product_data:
        messages.error(request, 'Producto no encontrado.')
        return redirect('storefront:products')
        
    context = {
        'product': product_data,
    }
    # Ruta de template ajustada
    return render(request, 'storefront/product_detail.html', context)

def category(request, slug):
    """Lista de productos filtrados por una categoría."""
    # Redirige a la vista principal de productos con el parámetro 'category'
    return redirect('storefront:products', category=slug)

def search(request):
    """Búsqueda de productos."""
    # Redirige a la vista principal de productos con el parámetro 'q'
    return redirect('storefront:products', q=request.GET.get('q', ''))

# La vista de 'ofertas' requeriría un endpoint específico en el microservicio.
def ofertas(request):
    """Vista de productos en oferta."""
    # Asumimos que el microservicio tiene un endpoint 'catalogo/ofertas/'
    data = fetch_data_from_inventario('catalogo/ofertas/')
    categories = fetch_data_from_inventario('catalogo/categorias/')
    
    context = {
        'products': data.get('products', []) if data else [],
        'categories': categories if categories else [],
    }
    # Ruta de template ajustada
    return render(request, 'storefront/ofertas.html', context)


# --- Vistas de Carrito y Compra (Usa Microservicio de Ventas) ---

def cart(request):
    """Muestra el contenido del carrito."""
    cart_obj = Cart(request)
    
    context = {
        'cart': cart_obj.get_data() # Método corregido para obtener datos enriquecidos
    }
    # RUTA AJUSTADA A storefront/shop/cart.html
    return render(request, 'storefront/shop/cart.html', context)

@require_POST
def cart_add(request):
    """Añade un producto al carrito."""
    product_id = request.POST.get('product_id')
    quantity = int(request.POST.get('quantity', 1))
    
    if not product_id:
        messages.error(request, "ID de producto inválido.")
        return redirect('storefront:cart')

    # La lógica de añadir ahora reside en la clase Cart y es segura.
    cart = Cart(request)
    result = cart.add(product_id=product_id, quantity=quantity)
    
    if result.get('success'):
        messages.success(request, result.get('message', 'Producto añadido al carrito.'))
    else:
        messages.error(request, result.get('message', 'Error al añadir el producto. Verifique el stock.'))
        
    # Redirige de vuelta a la página de donde vino o al carrito por defecto
    return redirect(request.POST.get('next', 'storefront:cart'))

@require_POST
def cart_update(request):
    """Actualiza la cantidad de un producto en el carrito."""
    product_id = request.POST.get('product_id')
    quantity = int(request.POST.get('quantity', 1))

    if not product_id or quantity < 1:
        messages.error(request, "Datos de actualización inválidos.")
        return redirect('storefront:cart')
        
    cart = Cart(request)
    result = cart.update(product_id=product_id, quantity=quantity)

    if result.get('success'):
        messages.success(request, result.get('message', 'Cantidad actualizada.'))
    else:
        messages.error(request, result.get('message', 'Error al actualizar. Verifique el stock.'))

    return redirect('storefront:cart')

@require_POST
def cart_remove(request):
    """Elimina un producto del carrito."""
    product_id = request.POST.get('product_id')

    if not product_id:
        messages.error(request, "ID de producto inválido.")
        return redirect('storefront:cart')

    cart = Cart(request)
    result = cart.remove(product_id=product_id)

    if result.get('success'):
        messages.success(request, result.get('message', 'Producto eliminado del carrito.'))
    else:
        messages.error(request, result.get('message', 'Error al eliminar el producto.'))

    return redirect('storefront:cart')

# La vista checkout es GET y POST (maneja la visualización del formulario y la validación previa a la confirmación)
def checkout(request):
    """Muestra el formulario de checkout y maneja la información de envío."""
    cart_obj = Cart(request)
    cart_data = cart_obj.get_data()
    
    if not cart_data.get('items'):
        messages.warning(request, "Tu carrito está vacío. No puedes proceder al pago.")
        return redirect('storefront:cart')
    
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            # Los datos del formulario se guardan temporalmente en la sesión
            request.session['checkout_info'] = form.cleaned_data
            return redirect('storefront:checkout_confirm')
        else:
            messages.error(request, "Por favor, corrige los errores en el formulario de envío.")
    else:
        # Intenta precargar datos si el usuario está autenticado y tiene un perfil
        initial_data = {}
        if request.session.get('is_authenticated') and request.session.get('user', {}).get('id'):
            token = request.session['user']['token']
            profile_data = fetch_data_from_ventas('clientes/perfil/', token)
            
            if profile_data and not profile_data.get('error'):
                # Mapeo de campos del perfil a campos del formulario Checkout
                initial_data = {
                    'shipping_name': f"{profile_data.get('first_name', '')} {profile_data.get('last_name', '')}",
                    'shipping_address': profile_data.get('address'),
                    'shipping_city': profile_data.get('city'),
                    'shipping_state': profile_data.get('state'),
                    'shipping_zip': profile_data.get('zip_code'),
                    'shipping_country': profile_data.get('country'),
                    'email': profile_data.get('email'),
                    'phone': profile_data.get('phone'),
                }
        
        form = CheckoutForm(initial=initial_data)

    context = {
        'cart': cart_data,
        'form': form
    }
    # RUTA AJUSTADA A storefront/shop/checkout.html
    return render(request, 'storefront/shop/checkout.html', context)


def checkout_confirm(request):
    """Muestra la confirmación final antes de crear el pedido en el microservicio."""
    cart_obj = Cart(request)
    cart_data = cart_obj.get_data()
    checkout_info = request.session.get('checkout_info')
    
    if not cart_data.get('items') or not checkout_info:
        messages.error(request, "Faltan datos del carrito o del envío. Intente de nuevo.")
        return redirect('storefront:checkout')

    if request.method == 'POST':
        if not request.session.get('is_authenticated'):
            # Si el usuario no está autenticado, no se permite crear el pedido
            messages.error(request, "Debes iniciar sesión para confirmar tu pedido.")
            return redirect('login') 
        
        token = request.session['user']['token']
        user_id = request.session['user']['id'] # ID del cliente en el microservicio
        
        # 1. Preparar la estructura del pedido para el microservicio de Ventas
        order_details = [
            {
                'product_id': int(item['product_id']),
                'quantity': item['quantity'],
                'unit_price': float(item['price'])
            } for item in cart_data['items']
        ]
        
        order_payload = {
            'customer_id': user_id,
            'details': order_details,
            # Añadir la información de envío guardada en sesión
            'shipping_name': checkout_info.get('shipping_name'),
            'shipping_address': checkout_info.get('shipping_address'),
            'shipping_city': checkout_info.get('shipping_city'),
            'shipping_state': checkout_info.get('shipping_state'),
            'shipping_zip': checkout_info.get('shipping_zip'),
            'shipping_country': checkout_info.get('shipping_country'),
            'email': checkout_info.get('email'),
            'phone': checkout_info.get('phone'),
            'total': float(cart_data['total']) # Total final
        }
        
        # 2. Enviar la orden al microservicio de Ventas
        result = fetch_data_from_ventas(
            endpoint='ventas/ordenes/', 
            request_session_token=token, 
            method='POST', 
            data=order_payload
        )

        if result and result.get('id'):
            # Éxito: Vaciar carrito y sesión de checkout
            cart_obj.clear()
            del request.session['checkout_info']
            messages.success(request, f"¡Tu pedido N° {result['id']} ha sido creado con éxito!")
            # Redirigir a la vista de confirmación
            return redirect('storefront:order_confirmation', order_id=result['id'])
        else:
            # Fallo: Mostrar error
            error_message = result.get('error', {}).get('message') or "Error desconocido al crear el pedido."
            messages.error(request, f"No se pudo completar la compra: {error_message}")
            return redirect('storefront:checkout')
            
    context = {
        'cart': cart_data,
        'checkout_info': checkout_info,
    }
    # RUTA AJUSTADA A storefront/shop/checkout_confirm.html
    return render(request, 'storefront/shop/checkout_confirm.html', context)


def order_confirmation(request, order_id):
    """Muestra la página de confirmación de pedido."""
    # En un entorno real, aquí se llamaría al microservicio para obtener los detalles finales del pedido.
    
    if not request.session.get('is_authenticated'):
        messages.error(request, "Debes iniciar sesión para ver los detalles de un pedido.")
        return redirect('login') 

    token = request.session['user']['token']
    
    order_data = fetch_data_from_ventas(f'ventas/ordenes/{order_id}/', token)
    
    if not order_data or 'error' in order_data:
        messages.error(request, 'Pedido no encontrado o no autorizado.')
        return redirect('storefront:orders')
        
    context = {
        'order': order_data
    }
    # RUTA AJUSTADA A storefront/shop/order_confirmation.html
    return render(request, 'storefront/shop/order_confirmation.html', context)


# --- Vistas de Cuenta y Perfil (Usa Microservicio de Ventas) ---

@login_required(login_url='login')
def profile(request):
    """Muestra el perfil del cliente."""
    token = request.session['user']['token']
    profile_data = fetch_data_from_ventas('clientes/perfil/', token)
    orders_data = fetch_data_from_ventas('clientes/pedidos/', token)
    
    context = {
        'customer_info': profile_data if profile_data and not profile_data.get('error') else None,
        'orders': orders_data if orders_data and not orders_data.get('error') else [],
    }
    # RUTA AJUSTADA A storefront/account/profile.html
    return render(request, 'storefront/account/profile.html', context)

# Las demás vistas de cuenta, info y API (profile_edit, orders, order_detail, etc.)
# seguirían la misma lógica de llamar a `fetch_data_from_ventas` o 
# `fetch_data_from_inventario` y usar la ruta de template ajustada.

# ... (Las demás vistas de tu proyecto deberían usar rutas de templates como las siguientes) ...

@login_required(login_url='login')
def profile_edit(request):
    """Edición del perfil del cliente."""
    # Lógica similar a profile pero con manejo de formulario POST/PUT al microservicio
    return render(request, 'storefront/account/profile_edit.html', {})

@login_required(login_url='login')
def orders(request):
    """Historial de pedidos del cliente."""
    # Lógica de fetch_data_from_ventas('clientes/pedidos/', token)
    return render(request, 'storefront/account/orders.html', {})

@login_required(login_url='login')
def order_detail(request, order_id):
    """Detalle de un pedido específico."""
    # Lógica de fetch_data_from_ventas(f'ventas/ordenes/{order_id}/', token)
    return render(request, 'storefront/account/order_detail.html', {})

def about(request):
    """Página Sobre Nosotros."""
    return render(request, 'storefront/info/about.html', {})

def contact(request):
    """Página de Contacto."""
    return render(request, 'storefront/info/contact.html', {})

def faq(request):
    """Página de Preguntas Frecuentes."""
    return render(request, 'storefront/info/faq.html', {})

def shipping(request):
    """Página de Información de Envíos."""
    return render(request, 'storefront/info/shipping.html', {})

def returns(request):
    """Página de Devoluciones."""
    return render(request, 'storefront/info/returns.html', {})

def warranty(request):
    """Página de Garantía."""
    return render(request, 'storefront/info/warranty.html', {})

def privacy(request):
    """Página de Política de Privacidad."""
    return render(request, 'storefront/info/privacy.html', {})

def terms(request):
    """Página de Términos y Condiciones."""
    return render(request, 'storefront/info/terms.html', {})

# --- Vistas API (JSON Responses) ---

# Mantendríamos las vistas API para JS/fetch si las necesitas.
# Estas vistas simplemente llaman a la lógica del carrito y devuelven JSON.

@require_POST
def api_cart_add(request):
    """API para añadir productos al carrito (Usado por JS)."""
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))
        
        cart = Cart(request)
        result = cart.add(product_id=product_id, quantity=quantity)
        
        if result.get('success'):
            return JsonResponse({
                'success': True,
                'message': result['message'],
                'cart_summary': cart.get_summary() # Resumen simple para el frontend
            })
        else:
            return JsonResponse({
                'success': False,
                'message': result['message']
            }, status=400)
    except Exception as e:
        logger.error(f"Error en api_cart_add: {e}")
        return JsonResponse({'success': False, 'message': 'Error interno del servidor'}, status=500)

@require_POST
def api_cart_remove(request):
    """API para eliminar productos del carrito."""
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        
        cart = Cart(request)
        result = cart.remove(product_id=product_id)

        if result.get('success'):
            return JsonResponse({
                'success': True,
                'message': result['message'],
                'cart_summary': cart.get_summary() 
            })
        else:
             return JsonResponse({
                'success': False,
                'message': result['message']
            }, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': 'Error interno del servidor'}, status=500)

@require_POST
def api_cart_update(request):
    """API para actualizar cantidad en el carrito."""
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))
        
        cart = Cart(request)
        result = cart.update(product_id=product_id, quantity=quantity)

        if result.get('success'):
            return JsonResponse({
                'success': True,
                'message': result['message'],
                'cart_summary': cart.get_summary() 
            })
        else:
             return JsonResponse({
                'success': False,
                'message': result['message']
            }, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': 'Error interno del servidor'}, status=500)

@require_POST
def api_checkout_validate(request):
    """API para validar datos del checkout antes de enviar la orden final."""
    try:
        data = json.loads(request.body)
        # Usamos el mismo formulario de Django para la validación de estructura
        form = CheckoutForm(data)
        
        if form.is_valid():
            return JsonResponse({'valid': True})
        else:
            # Devuelve los errores específicos del formulario
            return JsonResponse({
                'valid': False,
                'errors': form.errors.get_json_data()
            }, status=400)
    except Exception as e:
        logger.error(f"Error en api_checkout_validate: {e}")
        return JsonResponse({'valid': False, 'error': 'Error de procesamiento'}, status=500)
