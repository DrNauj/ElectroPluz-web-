from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Q
from django.conf import settings
from django.contrib import messages # Para mostrar mensajes de error al usuario
from gateway_app.forms import ProfileForm, CheckoutForm
from gateway_app.models import Product, Category, Order, OrderItem, Profile
from gateway_app.forms import ProfileForm, CheckoutForm
from django.conf import settings # Importar settings
import requests
import json
import logging
from decimal import Decimal 
from .cart import Cart 

logger = logging.getLogger(__name__)

# --- Helper para llamadas a Inventario ---
def _call_inventario_service(endpoint, params=None):
    """
    Llama al microservicio de Inventario y devuelve los datos JSON.
    Centraliza el manejo de errores HTTP y de conexión.
    """
    base_url = settings.MICROSERVICES['INVENTARIO']['BASE_URL'].rstrip('/')
    api_key = settings.MICROSERVICES['INVENTARIO']['API_KEY']
    # Usar el endpoint con prefijo 'api/'
    url = f"{base_url}/api/{endpoint}"
    
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
    """Vista de la página principal, obtiene productos destacados del MS-Inventario."""
    categories = Category.objects.all()
    featured_products = [] # Inicializar como lista vacía por defecto

    try:
        # URL para obtener productos destacados (asumiendo que el MS tiene un endpoint para esto)
        # O usar el endpoint de lista y filtrar: /api/productos/?featured=true&limit=8
        inventory_url = f"{settings.MICROSERVICES['INVENTARIO']['BASE_URL']}api/productos/?featured=true&limit=8"

        response = requests.get(
            inventory_url,
            headers={'X-API-Key': settings.MICROSERVICES['INVENTARIO']['API_KEY']},
            timeout=5
        )
        
        # Manejo de la respuesta
        if response.status_code == 200:
            featured_products_data = response.json()
            
            # --- CORRECCIÓN CLAVE ---
            # Verificar si la respuesta JSON es un diccionario antes de usar .get()
            if isinstance(featured_products_data, dict):
                # Extraer la lista de productos de la clave 'results' (asumiendo paginación DRF)
                featured_products = featured_products_data.get('results', [])
            else:
                # Si no es un diccionario, logueamos el error y dejamos featured_products como lista vacía
                logger.error(f"MS-Inventario devolvió datos inesperados (no-diccionario) para destacados: {featured_products_data}")
                featured_products = [] # Asegurar que es una lista
        else:
            logger.warning(f"Error al obtener productos destacados del MS-Inventario. Status: {response.status_code}")

    except requests.exceptions.RequestException as e:
        logger.error(f"Error de conexión al obtener productos destacados: {str(e)}")
        # featured_products se mantiene como lista vacía

    context = {
        'categories': categories,
        'featured_products': featured_products, # featured_products es ahora garantizado como lista
    }
    return render(request, 'storefront/home.html', context)

def product_list(request):
    """Lista de todos los productos con filtros y ordenamiento. Obtiene datos de Inventario."""
    
    # Parámetros para la API de Inventario
    params = {
        'page': request.GET.get('page', 1),
        'categoria': request.GET.get('category'),  # ID de la categoría
        'min_price': request.GET.get('min_price'),
        'max_price': request.GET.get('max_price'),
        'search': request.GET.get('search'),  # Soporte para búsqueda
        'ordering': request.GET.get('ordering', '-fecha_creacion'),  # Ordenamiento
        'active_coupon': request.GET.get('active_coupon'),  # Filtrar por cupones activos
    }

    # Obtener la categoría seleccionada si existe
    selected_category = None
    if params['categoria']:
        categoria_data = _call_inventario_service(f'categorias/{params["categoria"]}/')
        if 'error' not in categoria_data:
            selected_category = categoria_data
    
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
        'categoria': selected_category,
        'search_query': request.GET.get('search'),
        'is_ofertas': request.GET.get('active_coupon') == 'true',
        'ordering': request.GET.get('ordering', '-fecha_creacion'),
        'selected_category': params['categoria']
    }
    return render(request, 'storefront/shop/product_list.html', context)

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
    """Vista de ofertas (productos con cupones activos). Obtiene data de Inventario."""
    # Añadimos los parámetros de ofertas al request
    request.GET = request.GET.copy()
    request.GET['active_coupon'] = 'true'  # Filtrar productos con cupones activos
    request.GET['ordering'] = '-descuento'  # Ordenar por mayor descuento primero
    return product_list(request)

# --- Vistas de Carrito (Usan sesiones locales, no tocan API aún) ---
# Estas vistas DEBERÍAN actualizarse para sincronizar el carrito de sesión con un
# carrito persistente en el Microservicio de Ventas, pero requieren un endpoint específico.

def cart(request):
    """Muestra el contenido del carrito de compras."""
    # 1. Instanciar el objeto Cart usando la sesión del request
    cart_obj = Cart(request)
    
    # 2. Obtener el formulario de checkout (se puede necesitar en esta misma página)
    # Si el usuario está autenticado, intentar pre-llenar el formulario.
    if request.user.is_authenticated:
        try:
            profile = request.user.profile
            initial_data = {
                'shipping_name': profile.user.get_full_name() or profile.user.username,
                'shipping_address': profile.address,
                'shipping_city': profile.city,
                'shipping_state': profile.state,
                'shipping_zip': profile.zip_code,
                'shipping_country': profile.country,
                'email': profile.user.email,
                'phone': profile.phone,
            }
            form = CheckoutForm(initial=initial_data)
        except Profile.DoesNotExist:
             form = CheckoutForm()
    else:
        form = CheckoutForm()

    context = {
        'cart': cart_obj,
        'checkout_form': form, # El formulario de checkout también puede ser útil aquí
        'categories': Category.objects.filter(active=True),
    }
    
    # El traceback indica que faltaba 'storefront/cart.html'.
    # Si existe 'storefront/templates/shop/cart.html', esto funcionará.
    return render(request, 'storefront/shop/cart.html', context)


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
    try:
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 0))
        
        # Validación con inventario
        product_data = _call_inventario_service(f'productos/id/{product_id}/')
        
        if 'error' in product_data:
            messages.error(request, product_data['error'])
            return redirect('storefront:cart')
            
        product = product_data
        
        # Validar stock
        if quantity > product.get('stock', 0):
            messages.warning(request, f"Solo hay {product.get('stock', 0)} unidades disponibles.")
            quantity = product.get('stock', 0)
            
        if quantity <= 0:
            # Si la cantidad es 0 o negativa, eliminar del carrito
            return cart_remove(request)
        
        cart = request.session.get('cart', {})
        product_id_str = str(product_id)
        
        if product_id_str in cart:
            cart[product_id_str]['quantity'] = quantity
            request.session['cart'] = cart
            request.session.modified = True
            messages.success(request, f"Cantidad actualizada para {product['nombre']}")
        else:
            messages.error(request, "Producto no encontrado en el carrito")
            
        return redirect('storefront:cart')
    except Exception as e:
        logger.error(f"Error en cart_update: {e}")
        messages.error(request, "Error al actualizar el carrito")
        return redirect('storefront:cart')


@require_POST
def cart_remove(request):
    try:
        product_id = request.POST.get('product_id')
        cart = request.session.get('cart', {})
        product_id_str = str(product_id)
        
        if product_id_str in cart:
            # Obtener info del producto para el mensaje
            product_data = _call_inventario_service(f'productos/id/{product_id}/')
            product_name = product_data.get('nombre', 'Producto') if 'error' not in product_data else 'Producto'
            
            del cart[product_id_str]
            request.session['cart'] = cart
            request.session.modified = True
            messages.success(request, f"{product_name} eliminado del carrito")
        else:
            messages.error(request, "Producto no encontrado en el carrito")
            
        return redirect('storefront:cart')
    except Exception as e:
        logger.error(f"Error en cart_remove: {e}")
        messages.error(request, "Error al eliminar del carrito")
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
            
            # Actualizar stock en inventario
            for item in order_details:
                # Llamar a la API de inventario para actualizar stock
                stock_update = {
                    'cantidad': item['quantity'],
                    'tipo_movimiento': 'Salida por Venta',
                    'request_id': new_order.get('order_id', '')
                }
                try:
                    stock_response = requests.post(
                        f"{settings.INVENTORY_API_URL}/productos/{item['product_id']}/actualizar_stock/",
                        json=stock_update,
                        headers={'X-API-Key': settings.INVENTORY_API_KEY},
                        timeout=5
                    )
                    stock_response.raise_for_status()
                except Exception as e:
                    logger.error(f"Error actualizando stock para producto {item['product_id']}: {e}")
                    # No revertimos la orden pero registramos el error
            
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
