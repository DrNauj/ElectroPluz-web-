from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Q
from django.conf import settings
from django.contrib import messages # Para mostrar mensajes de error al usuario
from django.urls import reverse
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
def _call_inventario_service(endpoint, params=None, cache_timeout=300):
    """
    Llama al microservicio de Inventario y devuelve los datos JSON.
    Implementa caché y manejo optimizado de errores.
    """
    from django.core.cache import cache
    
    base_url = settings.MICROSERVICES['INVENTARIO']['BASE_URL'].rstrip('/')
    api_key = settings.MICROSERVICES['INVENTARIO']['API_KEY']
    
    # Normalizar el endpoint y crear cache_key
    endpoint = endpoint.strip('/')
    cache_key = f"inv_{endpoint}"
    if params:
        param_str = '_'.join(f"{k}:{v}" for k, v in sorted(params.items()))
        cache_key += f"_{param_str}"
    
    # Intentar obtener del caché
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        return cached_data
    
    url = f"{base_url}/api/{endpoint}/"
    headers = {
        'X-API-Key': api_key,
        'Accept': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=2)
        response.raise_for_status()
        data = response.json()
        
        # Guardar en caché
        cache.set(cache_key, data, cache_timeout)
        return data
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
    """Vista de la página principal optimizada."""
    import time
    start_time = time.time()
    logger.debug("Iniciando vista home")
    
    # Obtener el parámetro de ordenamiento
    sort = request.GET.get('sort', 'default')
    
    # 1. Obtener categorías desde caché o servicio
    from django.core.cache import cache
    cache_key = 'storefront_categories'
    categories = cache.get(cache_key)
    
    if categories is None:
        category_data = _call_inventario_service('categorias/')
        categories = []
        if 'error' not in category_data:
            categories = category_data if isinstance(category_data, list) else []
            # Guardar en caché por 1 hora
            cache.set(cache_key, categories, 3600)
    
    # 2. Obtener productos
    params = {
        'limit': 12,  # Mostrar más productos en la página principal
    }
    
    # Aplicar ordenamiento
    if sort == 'price_low':
        params['ordering'] = 'precio'
    elif sort == 'price_high':
        params['ordering'] = '-precio'
    elif sort == 'name':
        params['ordering'] = 'nombre'
    else:
        params['ordering'] = '-id'  # Por defecto, los más recientes primero
    
    products_data = _call_inventario_service('productos/', params=params)
    logger.debug(f"Respuesta de productos: {products_data}")
    
    products = []
    error = None
    
    if isinstance(products_data, dict):
        if 'results' in products_data:
            products = products_data['results']
        elif 'error' in products_data:
            error = products_data['error']
    elif isinstance(products_data, list):
        products = products_data
    
    # Asegurar que los precios sean Decimal
    for product in products:
        if 'precio' in product and product['precio'] is not None:
            product['precio'] = Decimal(str(product['precio']))
        if 'precio_original' in product and product['precio_original'] is not None:
            product['precio_original'] = Decimal(str(product['precio_original']))
        else:
            product['precio_original'] = product.get('precio')
            
    context = {
        'categories': categories,
        'products': products,
        'error': error,
        'active_sort': sort
    }
    
    end_time = time.time()
    logger.info(f"Tiempo total de carga home: {end_time - start_time:.2f} segundos")
    return render(request, 'storefront/shop/home.html', context)
    
    # 3. Obtener cupones activos
    active_coupons = []
    try:
        coupons_data = _call_inventario_service('cupones/', params={'activo': 'true', 'limit': 3})
        if 'error' not in coupons_data:
            active_coupons = coupons_data if isinstance(coupons_data, list) else []
    except Exception as e:
        logger.error(f"Error al obtener cupones: {e}")

    # 4. Obtener productos recién llegados para el carrusel
    new_arrivals = []
    new_params = {
        'limit': 5,
        'ordering': '-id'
    }
    new_products = _call_inventario_service('productos/', params=new_params)
    if 'error' not in new_products:
        if isinstance(new_products, dict):
            new_arrivals = new_products.get('results', [])
        else:
            new_arrivals = new_products[:5]

    context = {
        'categories': categories,
        'featured_products': featured_products,
        'active_coupons': active_coupons,
        'new_arrivals': new_arrivals,
        'current_section': 'home'  # Para marcar el enlace activo en el navbar
    }
    return render(request, 'storefront/shop/home.html', context)

def category(request, slug):
    """Vista de productos filtrados por categoría usando slug."""
    import time
    start_time = time.time()
    logger.debug(f"Iniciando vista de categoría: {slug}")
    
    # Obtener la categoría desde caché o servicio
    from django.core.cache import cache
    cache_key = f'category_{slug}'
    category = cache.get(cache_key)
    
    if category is None:
        category_data = _call_inventario_service('categorias/')
        if 'error' not in category_data:
            categories = category_data if isinstance(category_data, list) else []
            category = next((cat for cat in categories if cat['slug'] == slug), None)
            if category:
                # Guardar en caché por 1 hora
                cache.set(cache_key, category, 3600)
    
    if category:
        request.GET = request.GET.copy()
        request.GET['category_slug'] = slug
        response = product_list(request)
        
        end_time = time.time()
        logger.info(f"Tiempo total de carga categoría {slug}: {end_time - start_time:.2f} segundos")
        return response
    
    messages.error(request, "Categoría no encontrada")
    return redirect('storefront:products')

def product_list(request):
    """Lista de todos los productos con filtros y ordenamiento."""
    
    # Obtener todas las categorías para el filtro
    categories = []
    category_data = _call_inventario_service('categorias/')
    if 'error' not in category_data:
        categories = category_data if isinstance(category_data, list) else []

    # Preparar parámetros de filtrado
    params = {}
    
    # Filtro por categoría
    category_slug = request.GET.get('category_slug')
    if category_slug:
        params['categoria_slug'] = category_slug
        # Obtener detalles de la categoría seleccionada
        selected_category = next((cat for cat in categories if cat['slug'] == category_slug), None)
        if selected_category:
            params['categoria'] = selected_category['id']  # Mantener compatibilidad con API
    else:
        selected_category = None

    # Filtros de precio
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        params['precio_min'] = min_price
    if max_price:
        params['precio_max'] = max_price

    # Búsqueda
    search_query = request.GET.get('search')
    if search_query:
        params['busqueda'] = search_query

    # Ordenamiento
    ordering = request.GET.get('ordering', '-id')
    if ordering:
        params['ordering'] = ordering

    # Filtro de ofertas
    is_ofertas = request.GET.get('active_coupon') == 'true'
    if is_ofertas:
        params['con_descuento'] = 'true'

    # Paginación
    page = request.GET.get('page', 1)
    params['page'] = page
    params['page_size'] = 12  # productos por página

    # Obtener productos
    product_data = _call_inventario_service('productos/', params=params)
    
    if 'error' in product_data:
        messages.error(request, product_data['error'])
        products = []
        total_pages = 1
        current_page = 1
    else:
        if isinstance(product_data, dict):
            products = product_data.get('results', [])
            total_count = product_data.get('count', 0)
            current_page = product_data.get('current_page', 1)
            total_pages = -(-total_count // 12)  # Ceiling division
        else:
            products = product_data
            total_pages = 1
            current_page = 1

    # Crear objeto de paginación
    paginator = Paginator(range(total_pages * 12), 12)
    page_obj = paginator.get_page(current_page)

    context = {
        'products': products,
        'page_obj': page_obj,
        'categories': categories,
        'categoria': selected_category,
        'search_query': search_query,
        'is_ofertas': is_ofertas,
        'ordering': ordering,
        'selected_category': selected_category
    }
    
    return render(request, 'storefront/shop/product_list.html', context)

def product_detail(request, slug):
    """Detalle de un producto y sus productos relacionados."""
    import time
    start_time = time.time()
    
    try:
        # 1. Obtener detalles del producto desde caché o servicio
        from django.core.cache import cache
        cache_key = f'product_detail_{slug}'
        product_data = cache.get(cache_key)
        
        if product_data is None:
            logger.debug(f"Cache miss para producto {slug}, obteniendo del servicio")
            product_data = _call_inventario_service(f'productos/{slug}')
            if isinstance(product_data, dict) and 'error' not in product_data:
                # Guardar en caché por 15 minutos (más corto que categorías porque los precios pueden cambiar)
                cache.set(cache_key, product_data, 900)
        
        if isinstance(product_data, dict):
            if 'error' in product_data:
                logger.error(f"Error al obtener producto {slug}: {product_data['error']}")
                messages.error(request, "Lo sentimos, no pudimos encontrar el producto solicitado.")
                return redirect('storefront:products')
                
            # Verificar que tengamos los campos necesarios
            required_fields = ['id', 'nombre', 'precio', 'stock']
            if not all(field in product_data for field in required_fields):
                logger.error(f"Datos incompletos para el producto {slug}")
                messages.error(request, "Lo sentimos, los datos del producto están incompletos.")
                return redirect('storefront:products')
        else:
            logger.error(f"Respuesta inesperada para el producto {slug}")
            messages.error(request, "Lo sentimos, ocurrió un error al cargar el producto.")
            return redirect('storefront:products')
    except Exception as e:
        logger.error(f"Error al procesar la solicitud para el producto {slug}: {str(e)}")
        messages.error(request, "Lo sentimos, ocurrió un error al procesar su solicitud.")
        return redirect('storefront:products')
        
    product = product_data
    
    # Asegurar tipos de datos correctos
    if 'precio' in product and product['precio'] is not None:
        product['precio'] = Decimal(str(product['precio']))
    if 'precio_original' in product and product['precio_original'] is not None:
        product['precio_original'] = Decimal(str(product['precio_original']))
    else:
        product['precio_original'] = product.get('precio')
    
    # 2. Obtener productos relacionados (de la misma categoría)
    related_products = []
    if product.get('categoria', {}).get('id'):
        try:
            params = {
                'categoria': product['categoria']['id'],
                'exclude': product['id'],  # No incluir el producto actual
                'limit': 4  # Limitar a 4 productos relacionados
            }
            related_data = _call_inventario_service('productos', params=params)
            if isinstance(related_data, dict) and 'results' in related_data:
                related_products = related_data['results'][:4]
                
                # Asegurar que los productos relacionados tengan todos los campos necesarios
                related_products = [
                    prod for prod in related_products 
                    if all(field in prod for field in ['id', 'nombre', 'precio', 'slug'])
                ]
        except Exception as e:
            logger.warning(f"Error al obtener productos relacionados: {str(e)}")
            # No enviamos mensaje de error al usuario ya que esto no es crítico

    context = {
        'product': product,
        'related_products': related_products,
        'error': None  # Para el manejo de errores en la plantilla
    }
    
    end_time = time.time()
    logger.info(f"Tiempo total de carga detalle producto {slug}: {end_time - start_time:.2f} segundos")
    return render(request, 'storefront/shop/product_detail.html', context)


# --- Vistas restantes que necesitan conexión al Microservicio de Ventas para Carrito/Checkout/Perfil ---

# Nota: Las vistas de Carrito y Perfil a continuación todavía utilizan la lógica de sesión 
# local para el carrito y necesitan ser adaptadas para interactuar completamente con la API de Ventas 
# para crear pedidos (Checkout) y consultar pedidos existentes (Profile/Orders).

def category(request, slug):
    """Vista de productos filtrados por categoría usando slug."""
    # Obtener la categoría por slug
    category_data = _call_inventario_service('categorias/')
    if 'error' not in category_data:
        categories = category_data if isinstance(category_data, list) else []
        category = next((cat for cat in categories if cat['slug'] == slug), None)
        if category:
            # En lugar de redirigir, renderizamos directamente la lista con el filtro
            request.GET = request.GET.copy()
            request.GET['category_slug'] = slug
            return product_list(request)
    
    messages.error(request, "Categoría no encontrada")
    return redirect('storefront:products')

def search(request):
    """Vista de resultados de búsqueda. Obtiene data de Inventario."""
    # Redirigimos a la lista de productos con el parámetro de búsqueda.
    query = request.GET.get('search')
    return redirect('storefront:products') + f'?search={query}'

def search_suggestions(request):
    """API para obtener sugerencias de búsqueda."""
    query = request.GET.get('q', '').strip()
    if not query or len(query) < 2:
        return JsonResponse({'suggestions': []})
        
    # Buscar productos que coincidan con el query
    params = {
        'busqueda': query,
        'limit': 5
    }
    products_data = _call_inventario_service('productos/', params=params)
    
    suggestions = []
    if 'error' not in products_data:
        if isinstance(products_data, dict):
            products = products_data.get('results', [])
        else:
            products = products_data[:5]
            
        for product in products:
            suggestions.append({
                'id': product['id'],
                'nombre': product['nombre'],
                'imagen': product.get('imagen', ''),
                'precio': product['precio'],
                'url': reverse('storefront:product', args=[product['slug']])
            })
            
    return JsonResponse({'suggestions': suggestions})

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
        
    # Si el usuario está autenticado, prellenar el formulario
    if request.user.is_authenticated:
        try:
            profile = request.user.profile
            initial_data = {
                'nombre': profile.user.first_name,
                'apellidos': profile.user.last_name,
                'email': profile.user.email,
                'telefono': profile.phone,
                'direccion': profile.address,
                'ciudad': profile.city,
                'estado': profile.state,
                'cp': profile.zip_code,
            }
            form = CheckoutForm(initial=initial_data)
        except Profile.DoesNotExist:
            form = CheckoutForm()
    else:
        form = CheckoutForm()
    
    cart_data = request.session.get('cart', {})
    cart_items = []
    subtotal = Decimal('0.00')
    
    # Obtener los detalles de los productos y calcular totales
    for product_id, item_data in cart_data.items():
        product_detail_data = _call_inventario_service(f'productos/id/{product_id}/')
        if 'error' not in product_detail_data:
            product = product_detail_data
            price = Decimal(str(item_data['price']))
            quantity = item_data['quantity']
            item_total = price * quantity
            subtotal += item_total
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'price': price,
                'subtotal': item_total
            })

    # Calcular IVA (16%)
    tax = (subtotal * Decimal('0.16')).quantize(Decimal('0.01'))
    
    # Calcular costos de envío
    shipping_cost = Decimal('0.00')
    if subtotal < Decimal('999.00'):  # Envío gratis en compras mayores a $999
        shipping_cost = Decimal('99.00')  # Costo base de envío

    # Verificar cupón si existe
    discount_amount = Decimal('0.00')
    coupon_code = request.session.get('coupon_code')
    if coupon_code:
        coupon_data = _call_inventario_service(f'cupones/{coupon_code}/')
        if 'error' not in coupon_data and coupon_data.get('activo'):
            discount_percentage = Decimal(str(coupon_data.get('descuento', '0')))
            discount_amount = (subtotal * discount_percentage / Decimal('100')).quantize(Decimal('0.01'))

    # Calcular total final incluyendo IVA
    total_with_tax = subtotal + tax + shipping_cost - discount_amount
    
    # Obtener lista de estados
    estados_data = _call_inventario_service('estados/')
    estados = estados_data if 'error' not in estados_data else []
            
    context = {
        'form': form,
        'cart_items': cart_items,
        'cart_total': subtotal,
        'tax': tax,
        'shipping_cost': shipping_cost,
        'discount_amount': discount_amount,
        'total_with_tax': total_with_tax,
        'estados': estados,
        'free_shipping_threshold': Decimal('999.00')
    }
    return render(request, 'storefront/shop/checkout.html', context)

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
    """API para agregar/actualizar productos del carrito."""
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))
        
        if not product_id:
            return JsonResponse({'success': False, 'error': 'ID de producto requerido'}, status=400)
            
        # Obtener el carrito
        cart = Cart(request)
        
        # Agregar al carrito
        cart.add(product_id, quantity)
        
        return JsonResponse({
            'success': True,
            'message': 'Producto agregado al carrito',
            'count': len(cart.get_data()['items'])
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Datos inválidos'}, status=400)
    except Exception as e:
        logger.error(f"Error al agregar al carrito: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

def api_get_cart_count(request):
    """API para obtener el número de items en el carrito."""
    cart = Cart(request)
    cart_data = cart.get_data()
    count = sum(item['cantidad'] for item in cart_data['items'])
    return JsonResponse({'count': count})

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

@require_POST
def validate_coupon(request):
    """API para validar cupones de descuento."""
    try:
        data = json.loads(request.body)
        coupon_code = data.get('codigo')
        
        if not coupon_code:
            return JsonResponse({
                'valid': False,
                'message': 'Código de cupón no proporcionado'
            })
            
        # Validar cupón con el servicio de inventario
        coupon_data = _call_inventario_service(f'cupones/{coupon_code}/')
        
        if 'error' in coupon_data:
            return JsonResponse({
                'valid': False,
                'message': 'Cupón no encontrado'
            })
            
        if not coupon_data.get('activo'):
            return JsonResponse({
                'valid': False,
                'message': 'Este cupón ya no está activo'
            })
            
        # Si el cupón es válido, guardarlo en la sesión
        request.session['coupon_code'] = coupon_code
        request.session.modified = True
        
        return JsonResponse({
            'valid': True,
            'message': f'Cupón aplicado: {coupon_data.get("descuento")}% de descuento',
            'discount_percent': coupon_data.get('descuento')
        })
        
    except Exception as e:
        logger.error(f"Error al validar cupón: {e}")
        return JsonResponse({
            'valid': False,
            'message': 'Error al validar el cupón'
        }, status=500)
