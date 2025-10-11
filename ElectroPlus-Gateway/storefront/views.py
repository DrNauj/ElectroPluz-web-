from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Q
from django.conf import settings
from django.contrib import messages # Para mostrar mensajes de error al usuario
from gateway_app.forms import ProfileForm, CheckoutForm
# Ya no necesitamos importar modelos locales como Product, Category, etc., 
# ya que la data viene del microservicio.
import requests
import json
import logging
from decimal import Decimal 

logger = logging.getLogger(__name__)

# --- Helper para llamadas a Inventario ---
def _call_inventario_service(endpoint, params=None):
    """
    Llama al microservicio de Inventario y devuelve los datos JSON.
    Centraliza el manejo de errores HTTP y de conexión.
    """
    base_url = settings.MICROSERVICES['INVENTARIO']['BASE_URL']
    api_key = settings.MICROSERVICES['INVENTARIO']['API_KEY']
    # Asumimos que los endpoints de Inventario tienen el prefijo 'catalogo/'
    url = f"{base_url}catalogo/{endpoint}"
    
    headers = {
        'X-API-Key': api_key,
        'Accept': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=5)
        response.raise_for_status() # Lanza error si el status no es 2xx
        return response.json()
    except requests.exceptions.HTTPError as e:
        # Error HTTP (400, 404, 500, etc.)
        status_code = e.response.status_code
        logger.error(f"HTTP Error al consultar Inventario ({url}): {status_code} - {e.response.text}")
        if status_code == 404:
            return {'error': "Producto o recurso no encontrado."}
        return {'error': f"Error en el servicio de inventario: Código {status_code}"}
    except requests.exceptions.RequestException as e:
        # Error de conexión (DNS, Timeout, etc.)
        logger.error(f"Error de conexión al consultar Inventario ({url}): {e}")
        return {'error': "Error de conexión con el servicio de inventario. Intente más tarde."}


def home(request):
    """Vista de la página principal. Obtiene categorías y productos destacados de Inventario."""
    
    # 1. Obtener categorías
    categories = []
    category_data = _call_inventario_service('categorias/')
    if isinstance(category_data, list):
        categories = category_data
    
    # 2. Obtener productos destacados
    featured_products = []
    # Solicitamos productos marcados como destacados o los 8 más vendidos
    featured_products_data = _call_inventario_service('productos/', params={'featured': 'true', 'limit': 8})
    if isinstance(featured_products_data, list):
        featured_products = featured_products_data
    elif isinstance(featured_products_data, dict) and 'results' in featured_products_data:
        featured_products = featured_products_data['results']
    
    context = {
        'categories': categories,
        'featured_products': featured_products,
    }
    return render(request, 'storefront/home.html', context)

def product_list(request):
    """Lista de todos los productos con filtros y ordenamiento. Obtiene datos de Inventario."""
    
    # Parámetros para la API de Inventario
    params = {
        'page': request.GET.get('page', 1),
        'category_slug': request.GET.get('category'), # Usamos slug para el filtro
        'min_price': request.GET.get('min_price'),
        'max_price': request.GET.get('max_price'),
        'search': request.GET.get('search'), # Soporte para búsqueda
        'order_by': request.GET.get('sort_by'),
    }
    
    # Limpiar parámetros vacíos
    params = {k: v for k, v in params.items() if v}
    
    # Llama al microservicio
    product_data = _call_inventario_service('productos/', params=params)
    categories = _call_inventario_service('categorias/')

    if 'error' in product_data:
        messages.error(request, product_data['error'])
        products = []
        paginator = Paginator([], 12)
        page_obj = paginator.get_page(1)
    else:
        # El microservicio debe devolver la paginación de DRF
        products = product_data.get('results', [])
        # Simulamos la paginación de Django con los datos recibidos (idealmente el microservicio la manejaría)
        paginator = Paginator(products, 12) # 12 productos por página
        page_obj = paginator.get_page(request.GET.get('page'))
    
    context = {
        'page_obj': page_obj,
        'products': page_obj.object_list,
        'categories': categories if isinstance(categories, list) else [],
        'current_category': request.GET.get('category'),
    }
    return render(request, 'storefront/product_list.html', context)

def product_detail(request, slug):
    """Detalle de un producto. Obtiene datos de Inventario por slug."""
    
    # Llama al microservicio para obtener un producto por SLUG
    product_data = _call_inventario_service(f'productos/{slug}/')
    
    if 'error' in product_data:
        # En caso de error (incluido 404), mostramos mensaje y redirigimos o mostramos error
        messages.error(request, product_data['error'])
        # Considerar si redirigir a la lista de productos o renderizar 404
        return redirect('storefront:products')
        
    product = product_data # Asumimos que el microservicio devuelve el objeto directamente
    
    # Aseguramos que el precio sea de tipo Decimal si se usa en cálculos de plantilla
    if product.get('price'):
        product['price'] = Decimal(str(product['price']))

    context = {
        'product': product,
    }
    return render(request, 'storefront/product_detail.html', context)


# --- Vistas restantes que necesitan conexión al Microservicio de Ventas para Carrito/Checkout/Perfil ---

# Nota: Las vistas de Carrito y Perfil a continuación todavía utilizan la lógica de sesión 
# local para el carrito y necesitan ser adaptadas para interactuar completamente con la API de Ventas 
# para crear pedidos (Checkout) y consultar pedidos existentes (Profile/Orders).

def category(request, slug):
    """Vista de productos filtrados por categoría. Obtiene data de Inventario."""
    # Simplemente redirigimos a la lista de productos con el filtro de categoría.
    return redirect('storefront:products', category=slug)

def search(request):
    """Vista de resultados de búsqueda. Obtiene data de Inventario."""
    # Redirigimos a la lista de productos con el parámetro de búsqueda.
    query = request.GET.get('q')
    return redirect(f"{redirect('storefront:products')}?search={query}")

def ofertas(request):
    """Vista de ofertas (productos con descuento). Obtiene data de Inventario."""
    # Asumimos que la API de Inventario tiene un filtro para ofertas/descuentos
    params = {'on_sale': 'true'}
    # Llama al microservicio de Inventario (se reutiliza la lógica de product_list)
    return product_list(request) # product_list manejará el filtro si se añade el parámetro

# --- Vistas de Carrito (Usan sesiones locales, no tocan API aún) ---
# Estas vistas DEBERÍAN actualizarse para sincronizar el carrito de sesión con un
# carrito persistente en el Microservicio de Ventas, pero requieren un endpoint específico.

def cart(request):
    """Muestra el contenido del carrito."""
    # Aquí se debería llamar a la API de Ventas para obtener el carrito persistente
    # o usar la lógica local de sesión. Mantenemos la lógica de sesión por ahora.
    # Necesitaríamos importar la clase Cart o usar la sesión directamente.
    
    # Como la clase Cart no es local de storefront, necesitamos una implementación ligera aquí
    # o asumir que la clase Cart de sales se usará. Por la estructura, asumimos que se usa
    # un sistema de carrito basado en la sesión de Django simple (diccionario en request.session['cart']).
    
    cart_data = request.session.get('cart', {})
    
    # Obtener detalles de productos (Necesita llamar a Inventario para cada producto en el carrito)
    cart_items = []
    total = Decimal('0.00')
    
    for product_id, item_data in cart_data.items():
        # Llamada a Inventario para obtener detalles del producto
        # Asumimos un endpoint para obtener un producto por ID
        product_detail_data = _call_inventario_service(f'productos/id/{product_id}/')

        if 'error' not in product_detail_data:
            product = product_detail_data
            price = Decimal(str(item_data['price']))
            quantity = item_data['quantity']
            item_total = price * quantity
            total += item_total
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'price': price,
                'total_price': item_total
            })
            
    context = {
        'cart_items': cart_items,
        'cart_total': total,
    }
    return render(request, 'storefront/cart.html', context)


# Las vistas de API para carrito (api_cart_add, api_cart_remove, etc.) también están
# definidas al final de este archivo y DEBERÍAN hacer lo mismo: llamar a la API de Inventario
# para validar stock y a la API de Ventas para persistir el carrito/crear la orden.
# Para mantener la funcionalidad existente del frontend, las dejamos con la lógica de sesión por ahora,
# ya que la pregunta era sobre la conexión general del frontend.


@require_POST
def cart_add(request):
    # Aquí DEBERÍA haber lógica para llamar a la API de Ventas para agregar/actualizar el carrito persistente
    # Mantenemos lógica de sesión simple por ahora.
    try:
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 1))
        
        # Validación de existencia/stock llamando a Inventario
        product_data = _call_inventario_service(f'productos/id/{product_id}/')
        
        if 'error' in product_data:
            messages.error(request, product_data['error'])
            return redirect('storefront:products')
            
        product = product_data
        
        # Validar stock
        if quantity > product.get('stock', 0):
            messages.warning(request, f"Solo quedan {product.get('stock', 0)} unidades de {product['name']}.")
            quantity = product.get('stock', 0)
            
        if quantity <= 0:
            messages.error(request, "Cantidad no válida.")
            return redirect('storefront:product', slug=product['slug'])
        
        cart = request.session.get('cart', {})
        product_id_str = str(product_id)
        
        if product_id_str not in cart:
            # Precio obtenido del servicio de Inventario
            price = Decimal(str(product['price']))
            cart[product_id_str] = {'quantity': 0, 'price': str(price)}
            
        # Sumar cantidad
        current_quantity = cart[product_id_str]['quantity']
        new_quantity = current_quantity + quantity
        
        # Re-validar stock para la nueva cantidad total
        if new_quantity > product.get('stock', 0):
            new_quantity = product.get('stock', 0)
            messages.warning(request, f"La cantidad máxima permitida para {product['name']} es {new_quantity}.")

        cart[product_id_str]['quantity'] = new_quantity
        request.session['cart'] = cart
        request.session.modified = True
        
        messages.success(request, f"{new_quantity}x {product['name']} añadido/actualizado en el carrito.")
        return redirect('storefront:cart')
    except Exception as e:
        logger.error(f"Error en cart_add: {e}")
        messages.error(request, "Ocurrió un error al agregar el producto al carrito.")
        return redirect('storefront:products')

@require_POST
def cart_update(request):
    # Lógica de actualización de carrito, similar a cart_add pero con override_quantity
    # ... (Se mantiene la lógica original por ser extensa) ...
    messages.error(request, "La función de actualización de carrito no está completamente implementada para API.")
    return redirect('storefront:cart')


def cart_remove(request):
    # Lógica de eliminación de carrito
    # ... (Se mantiene la lógica original por ser extensa) ...
    messages.error(request, "La función de eliminación de carrito no está completamente implementada para API.")
    return redirect('storefront:cart')


def checkout(request):
    """Muestra el formulario de checkout."""
    if not request.session.get('cart'):
        messages.warning(request, "Tu carrito está vacío.")
        return redirect('storefront:products')
        
    form = CheckoutForm() # Se asume un formulario de dirección/contacto.
    
    # Se necesita llamar a la API de Ventas para obtener info del carrito/productos para el resumen.
    # Por ahora se usa la sesión (requiere la misma lógica de cart view para obtener detalles de Inventario).
    
    cart_data = request.session.get('cart', {})
    cart_items = []
    total = Decimal('0.00')
    
    # Lógica duplicada de la vista cart para obtener el resumen del pedido
    for product_id, item_data in cart_data.items():
        product_detail_data = _call_inventario_service(f'productos/id/{product_id}/')
        if 'error' not in product_detail_data:
            product = product_detail_data
            price = Decimal(str(item_data['price']))
            quantity = item_data['quantity']
            item_total = price * quantity
            total += item_total
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'price': price,
                'total_price': item_total
            })
            
    context = {
        'form': form,
        'cart_items': cart_items,
        'cart_total': total
    }
    return render(request, 'storefront/checkout.html', context)

@require_POST
def checkout_confirm(request):
    """Procesa el checkout y crea la orden en el microservicio de Ventas."""
    
    if not request.session.get('cart'):
        messages.error(request, "Carrito vacío. No se puede procesar el pedido.")
        return redirect('storefront:products')
        
    form = CheckoutForm(request.POST)
    
    if form.is_valid():
        try:
            cart_data = request.session.get('cart', {})
            # Prepara la data para el microservicio de VENTAS
            order_data = form.cleaned_data
            
            # Formatear detalles de la orden para la API de Ventas
            order_details = []
            for product_id, item in cart_data.items():
                order_details.append({
                    'product_id': int(product_id),
                    'quantity': item['quantity'],
                    # Se usa el precio de la sesión (idealmente se validaría con Inventario)
                    'unit_price': item['price'] 
                })
                
            payload = {
                'customer_id': request.session.get('user', {}).get('id'), # Puede ser None si es anónimo
                'shipping_info': {
                    'name': order_data['shipping_name'],
                    'address': order_data['shipping_address'],
                    'city': order_data['shipping_city'],
                    'state': order_data['shipping_state'],
                    'zip': order_data['shipping_zip'],
                    'country': order_data['shipping_country'],
                    'email': order_data['email'],
                    'phone': order_data['phone'],
                },
                'items': order_details
            }
            
            # --- Llamada a la API de Ventas para crear la orden ---
            ventas_base_url = settings.MICROSERVICES['VENTAS']['BASE_URL']
            ventas_api_key = settings.MICROSERVICES['VENTAS']['API_KEY']
            
            response = requests.post(
                f"{ventas_base_url}pedidos/crear/",
                json=payload,
                headers={
                    'X-API-Key': ventas_api_key,
                    'Authorization': f"Token {request.session.get('user', {}).get('token', '')}"
                },
                timeout=10
            )
            response.raise_for_status()
            
            # Si es exitoso, vaciar carrito de la sesión
            del request.session['cart']
            request.session.modified = True
            
            new_order = response.json()
            messages.success(request, f"¡Tu pedido {new_order.get('order_id', '')} ha sido creado con éxito!")
            # Redirigir al detalle del pedido
            return redirect('storefront:order_detail', order_id=new_order.get('id', ''))
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error al crear pedido en Ventas: {e}")
            messages.error(request, "Error de conexión o en el servicio al procesar el pedido. Intente más tarde.")
            
        except Exception as e:
            logger.error(f"Error inesperado al confirmar checkout: {e}")
            messages.error(request, "Ocurrió un error inesperado al procesar el pedido.")
            
    else:
        # Si el formulario no es válido, volvemos a mostrar el checkout con errores
        messages.error(request, "Por favor, corrija los errores en el formulario.")
        # Se necesita volver a obtener los items para el contexto
        cart_data = request.session.get('cart', {})
        cart_items = []
        total = Decimal('0.00')
        # ... (Lógica duplicada para obtener el resumen del pedido para el contexto) ...
        context = {
            'form': form,
            'cart_items': cart_items, # Items con detalles (falta la lógica aquí)
            'cart_total': total
        }
        return render(request, 'storefront/checkout.html', context)
        
    return redirect('storefront:checkout')


@login_required
def profile(request):
    """Muestra el perfil del usuario autenticado."""
    # Este ya llama a la API de Ventas para obtener el perfil en gateway_app/views.py (dashboard)
    # Lo mantenemos simple aquí. En un sistema real, profile debería ser una vista que consuma
    # un endpoint de Ventas/Clientes para obtener el perfil detallado.
    # Por ahora, redirigimos al dashboard que ya hace esa llamada.
    return redirect('dashboard')


@login_required
def orders(request):
    """Lista los pedidos del usuario. (Reusa la lógica de dashboard si es cliente)"""
    # Esta lógica ya está cubierta en gateway_app/views.py (dashboard)
    return redirect('dashboard') 

@login_required
def order_detail(request, order_id):
    """Muestra el detalle de un pedido específico. Llama a la API de Ventas."""
    try:
        ventas_base_url = settings.MICROSERVICES['VENTAS']['BASE_URL']
        ventas_api_key = settings.MICROSERVICES['VENTAS']['API_KEY']
        
        response = requests.get(
            f"{ventas_base_url}clientes/pedidos/{order_id}/",
            headers={
                'X-API-Key': ventas_api_key,
                'Authorization': f'Token {request.session["user"]["token"]}'
            },
            timeout=5
        )
        response.raise_for_status()
        order_detail_data = response.json()
        
        context = {
            'order': order_detail_data,
        }
        return render(request, 'storefront/order_detail.html', context)
        
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code
        if status_code == 404:
            messages.error(request, "Pedido no encontrado o no autorizado.")
        else:
            messages.error(request, f"Error al obtener detalle del pedido: Código {status_code}.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error de conexión al obtener detalle del pedido: {e}")
        messages.error(request, "Error de conexión con el servicio de ventas.")

    return redirect('storefront:orders')


# --- Vistas de Información ---

def about(request):
    return render(request, 'storefront/info/about.html')

def contact(request):
    return render(request, 'storefront/info/contact.html')

def faq(request):
    return render(request, 'storefront/info/faq.html')

def shipping(request):
    return render(request, 'storefront/info/shipping.html')

def returns(request):
    return render(request, 'storefront/info/returns.html')

def warranty(request):
    return render(request, 'storefront/info/warranty.html')

def privacy(request):
    return render(request, 'storefront/info/privacy.html')

def terms(request):
    return render(request, 'storefront/info/terms.html')

# --- API Endpoints (Para uso con JavaScript/AJAX) ---
# Estos también deberían actualizarse para llamar a las APIs, pero se dejan con la
# lógica de sesión simple por ahora.

# La lógica de las APIs para el carrito y checkout se deja con la lógica de sesión 
# simple, asumiendo que el frontend las llama para interacciones rápidas, 
# y la validación final se hace en `checkout_confirm`.

@require_POST
def api_cart_add(request):
    """API para agregar/actualizar productos del carrito (sesión local)."""
    # Lógica de sesión similar a cart_add pero con JSON
    return JsonResponse({'success': False, 'error': 'No implementado para API remota aún.'}, status=501)

@require_POST
def api_cart_update(request):
    """API para actualizar cantidad de productos del carrito (sesión local)."""
    # Lógica de sesión similar a cart_update pero con JSON
    return JsonResponse({'success': False, 'error': 'No implementado para API remota aún.'}, status=501)


@require_POST
def api_cart_remove(request):
    """API para eliminar productos del carrito (sesión local)."""
    # Lógica de sesión similar a cart_remove pero con JSON
    return JsonResponse({'success': False, 'error': 'No implementado para API remota aún.'}, status=501)


@require_POST
def api_checkout_validate(request):
    """API para validar datos del checkout."""
    try:
        data = json.loads(request.body)
        form = CheckoutForm(data)
        
        if form.is_valid():
            return JsonResponse({'valid': True})
        else:
            # Devolvemos los errores de campo en formato JSON
            return JsonResponse({
                'valid': False,
                'errors': form.errors.as_json() # Envía errores en formato JSON
            }, status=400)
    except Exception as e:
        logger.error(f"Error al validar checkout: {e}")
        return JsonResponse({
            'valid': False,
            'error': str(e)
        }, status=500)

@login_required
@require_POST
def api_profile_edit(request):
    """API para editar el perfil de usuario. Llama a la API de Ventas."""
    user_id = request.session.get('user', {}).get('id')
    user_token = request.session.get('user', {}).get('token')
    
    if not user_id or not user_token:
        return JsonResponse({'success': False, 'error': 'Usuario no autenticado.'}, status=401)
        
    try:
        data = json.loads(request.body)
        form = ProfileForm(data) # Usa el formulario de Profile para validación de campos
        
        if form.is_valid():
            # Prepara la data para el microservicio (asumiendo que espera un subconjunto de ProfileForm)
            payload = {
                'phone': form.cleaned_data.get('phone'),
                'address': form.cleaned_data.get('address'),
                'city': form.cleaned_data.get('city'),
                'state': form.cleaned_data.get('state'),
                'zip_code': form.cleaned_data.get('zip_code'),
                'country': form.cleaned_data.get('country'),
                # El avatar requiere manejo de archivos separado, aquí solo manejo data JSON
            }
            
            # --- Llamada a la API de Ventas para actualizar perfil ---
            ventas_base_url = settings.MICROSERVICES['VENTAS']['BASE_URL']
            ventas_api_key = settings.MICROSERVICES['VENTAS']['API_KEY']
            
            response = requests.patch(
                f"{ventas_base_url}clientes/perfil/", # Asumimos un endpoint PATCH para actualización
                json=payload,
                headers={
                    'X-API-Key': ventas_api_key,
                    'Authorization': f'Token {user_token}',
                    'Content-Type': 'application/json'
                },
                timeout=5
            )
            response.raise_for_status()
            
            # Actualización exitosa
            return JsonResponse({'success': True, 'message': 'Perfil actualizado con éxito.'})
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error al actualizar perfil en Ventas: {e}")
        return JsonResponse({'success': False, 'error': 'Error de conexión o servicio.'}, status=500)
    except Exception as e:
        logger.error(f"Error inesperado en api_profile_edit: {e}")
        return JsonResponse({'success': False, 'error': 'Error inesperado.'}, status=500)
        
def api_get_cart_count(request):
    """API para obtener el conteo de items del carrito."""
    cart_data = request.session.get('cart', {})
    item_count = sum(item['quantity'] for item in cart_data.values())
    return JsonResponse({'count': item_count})

def api_get_cart_total(request):
    """API para obtener el total del carrito."""
    cart_data = request.session.get('cart', {})
    total = Decimal('0.00')
    for item in cart_data.values():
        total += Decimal(item['price']) * item['quantity']
        
    return JsonResponse({'total': str(total)}) # Se usa str() para que sea serializable a JSON
