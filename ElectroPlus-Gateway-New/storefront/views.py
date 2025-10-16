from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta
from .models import Product, Category, Order, OrderItem, Review, UserProfile
from .mock_data import get_mock_products, get_mock_categories
from .cart import Cart
import requests
import logging

logger = logging.getLogger(__name__)

# Session global para reutilizar conexiones
_session = None

def get_session():
    """Obtiene una sesión HTTP reutilizable con configuración optimizada."""
    global _session
    if _session is None:
        _session = requests.Session()
        retry_strategy = requests.packages.urllib3.util.retry.Retry(
            total=2,  # Reducido a 2 intentos
            backoff_factor=0.1,
            status_forcelist=[500, 502, 503, 504]
        )
        adapter = requests.adapters.HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=25,  # Pool de conexiones
            pool_maxsize=25
        )
        _session.mount("http://", adapter)
    return _session

# --- Helper para llamadas a Inventario ---
def _call_inventario_service(endpoint, params=None, cache_timeout=300, force_refresh=False):
    """
    Llama al microservicio de Inventario y devuelve los datos JSON.
    Implementa caché y manejo optimizado de errores.
    """
    from django.core.cache import cache
    import hashlib

    base_url = settings.MICROSERVICES['INVENTARIO']['BASE_URL'].rstrip('/')
    api_key = settings.MICROSERVICES['INVENTARIO']['API_KEY']

    # Crear una clave de caché más eficiente
    cache_parts = [endpoint.strip('/')]
    if params:
        param_str = '&'.join(f"{k}={v}" for k, v in sorted(params.items()))
        cache_parts.append(param_str)
    cache_key = hashlib.md5('_'.join(cache_parts).encode()).hexdigest()

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

    # Si no es force_refresh, intentar obtener del caché
    if not force_refresh:
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return cached_data

    url = f"{base_url}/api/{endpoint}/"
    headers = {
        'X-API-Key': api_key,
        'Accept': 'application/json',
        'Connection': 'keep-alive'
    }

    try:
        response = get_session().get(
            url,
            headers=headers,
            params=params,
            timeout=3  # Reducido a 3 segundos
        )
        response.raise_for_status()
        data = response.json()

        # Guardar en caché solo si no hay error
        if isinstance(data, (dict, list)) and 'error' not in data:
            cache.set(cache_key, data, cache_timeout)
        return data

    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code
        logger.error(f"HTTP Error ({url}): {status_code}")
        # Intentar usar caché expirado en caso de error
        stale_data = cache.get(cache_key)
        if stale_data is not None:
            return stale_data
        return {'error': "Servicio temporalmente no disponible"}

    except requests.exceptions.RequestException as e:
        logger.error(f"Error de conexión ({url}): {str(e)}")
        # Intentar usar caché expirado en caso de error
        stale_data = cache.get(cache_key)
        if stale_data is not None:
            return stale_data
        return {'error': "Error de conexión"}

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
    category_slug = request.GET.get('category')
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
    search_query = request.GET.get('q')
    if search_query:
        params['busqueda'] = search_query

    # Ordenamiento
    ordering = request.GET.get('sort', '-id')
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

    return render(request, 'storefront/product_list.html', context)

def product_detail(request, slug):
    if settings.MOCK_DATA:
        products = get_mock_products()
        product = next((p for p in products if p.slug == slug), None)
    else:
        product = Product.objects.get(slug=slug)
    
    return render(request, 'storefront/product_detail.html', {
        'product': product
    })

@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    if settings.MOCK_DATA:
        products = get_mock_products()
        product = next((p for p in products if p.id == product_id), None)
    else:
        product = get_object_or_404(Product, id=product_id)
    
    quantity = int(request.POST.get('quantity', 1))
    cart.add(product=product, quantity=quantity, update_quantity=True)
    
    return JsonResponse({
        'cart_total': len(cart),
        'success': True,
        'message': f'{product.name} añadido al carrito'
    })

@login_required
def cart_remove(request, product_id):
    cart = Cart(request)
    if settings.MOCK_DATA:
        products = get_mock_products()
        product = next((p for p in products if p.id == product_id), None)
    else:
        product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    return redirect('storefront:cart_detail')

@login_required
def cart_detail(request):
    cart = Cart(request)
    return render(request, 'storefront/cart_detail.html', {
        'cart': cart
    })

@login_required
def checkout(request):
    cart = Cart(request)
    if len(cart) == 0:
        return redirect('storefront:product_list')
        
    if request.method == 'POST':
        form_data = request.POST
        
        # Validar datos requeridos
        required_fields = ['shipping_address', 'shipping_phone', 'payment_method']
        for field in required_fields:
            if not form_data.get(field):
                return JsonResponse({
                    'success': False,
                    'message': f'El campo {field} es requerido'
                }, status=400)
        
        # Crear la orden
        order = Order.objects.create(
            user=request.user,
            shipping_address=form_data.get('shipping_address'),
            shipping_phone=form_data.get('shipping_phone'),
            payment_method=form_data.get('payment_method'),
            notes=form_data.get('notes', '')
        )

        # Crear los items de la orden
        for item in cart:
            if settings.MOCK_DATA:
                product = next((p for p in get_mock_products() if str(p.id) == item['id']), None)
            else:
                product = Product.objects.get(id=item['id'])
                
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item['quantity']
            )

        # Actualizar totales de la orden
        order.update_totals()
        order.save()

        # Limpiar el carrito
        cart.clear()

        return JsonResponse({
            'success': True,
            'order_id': order.id,
            'message': 'Orden creada exitosamente'
        })

    return render(request, 'storefront/checkout.html', {
        'cart': cart,
        'user_profile': request.user.userprofile if hasattr(request.user, 'userprofile') else None
    })

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'storefront/order_history.html', {
        'orders': orders
    })

@login_required
def toggle_wishlist(request, product_id):
    if not hasattr(request.user, 'userprofile'):
        UserProfile.objects.create(user=request.user)
    
    product = get_object_or_404(Product, id=product_id)
    profile = request.user.userprofile
    
    if product in profile.wishlist.all():
        profile.wishlist.remove(product)
        in_wishlist = False
    else:
        profile.wishlist.add(product)
        in_wishlist = True
    
    return JsonResponse({
        'success': True,
        'in_wishlist': in_wishlist
    })

@login_required
def wishlist(request):
    if not hasattr(request.user, 'userprofile'):
        UserProfile.objects.create(user=request.user)
    
    return render(request, 'storefront/wishlist.html', {
        'wishlist': request.user.userprofile.wishlist.all()
    })

@login_required
def profile(request):
    if not hasattr(request.user, 'userprofile'):
        UserProfile.objects.create(user=request.user)
    
    if request.method == 'POST':
        # Actualizar información del usuario
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        if request.POST.get('email'):
            request.user.email = request.POST.get('email')
        request.user.save()
        
        # Actualizar perfil
        profile = request.user.userprofile
        profile.default_shipping_address = request.POST.get('default_shipping_address', '')
        profile.default_phone = request.POST.get('default_phone', '')
        profile.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Perfil actualizado exitosamente'
        })
    
    return render(request, 'storefront/profile.html', {
        'user': request.user,
        'profile': request.user.userprofile
    })

@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Solo se pueden cancelar pedidos pendientes
    if order.status != 'pending':
        return JsonResponse({
            'success': False,
            'message': 'Solo se pueden cancelar pedidos pendientes'
        }, status=400)
        
    # No se puede cancelar si ha pasado más de 1 hora
    if timezone.now() - order.created_at > timedelta(hours=1):
        return JsonResponse({
            'success': False,
            'message': 'No se puede cancelar el pedido después de 1 hora'
        }, status=400)
        
    order.status = 'cancelled'
    order.save()
    
    return JsonResponse({
        'success': True,
        'message': 'Pedido cancelado exitosamente'
    })

@login_required
def add_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        rating = int(request.POST.get('rating'))
        comment = request.POST.get('comment')
        
        review, created = Review.objects.update_or_create(
            product=product,
            user=request.user,
            defaults={
                'rating': rating,
                'comment': comment
            }
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Reseña agregada exitosamente',
            'avg_rating': product.avg_rating,
            'review_count': product.review_count
        })

    return JsonResponse({
        'success': False,
        'message': 'Método no permitido'
    })
