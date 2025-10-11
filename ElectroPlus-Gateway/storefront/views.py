from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Q
from gateway_app.models import Product, Category, Order, OrderItem, Profile # Se asume que estos modelos están en gateway_app
from gateway_app.forms import ProfileForm, CheckoutForm
from .cart import Cart # Importa la clase Cart
from django.conf import settings
from django.contrib import messages
import requests
import logging
import json
from decimal import Decimal

logger = logging.getLogger(__name__)

# --- VISTAS DE PÁGINAS PRINCIPALES ---
# [Las vistas home, product_list, product_detail, category, search, ofertas NO necesitan cambios]

def home(request):
    """Vista de la página principal."""
    categories = Category.objects.all()
    featured_products = Product.objects.filter(featured=True, active=True)[:8]
    
    context = {
        'categories': categories,
        'featured_products': featured_products,
    }
    return render(request, 'storefront/home.html', context)

# ... [Otras vistas de catálogo se mantienen igual] ...
def product_list(request):
    """Lista de todos los productos con filtros y ordenamiento."""
    products = Product.objects.filter(active=True)
    
    # Filtros
    category = request.GET.get('category')
    if category:
        products = products.filter(category__slug=category)
    
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    # Búsqueda
    query = request.GET.get('q')
    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))

    # Ordenamiento
    order = request.GET.get('order', 'name')
    products = products.order_by(order)

    # Paginación
    paginator = Paginator(products, 12) # Muestra 12 productos por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'categories': Category.objects.all(),
        'current_category': category,
        'current_order': order,
        'query': query
    }
    return render(request, 'storefront/product_list.html', context)

def product_detail(request, slug):
    """Detalle de un producto."""
    product = get_object_or_404(Product, slug=slug, active=True)
    return render(request, 'storefront/product_detail.html', {'product': product})

def category(request, slug):
    """Lista de productos por categoría."""
    category_obj = get_object_or_404(Category, slug=slug, active=True)
    products = Product.objects.filter(category=category_obj, active=True).order_by('name')

    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'category': category_obj,
        'page_obj': page_obj,
        'categories': Category.objects.all(),
    }
    return render(request, 'storefront/category.html', context)

def search(request):
    """Función de búsqueda de productos."""
    query = request.GET.get('q')
    products = Product.objects.none()
    
    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) | 
            Q(category__name__icontains=query)
        ).filter(active=True).distinct()

    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'query': query,
        'page_obj': page_obj,
        'categories': Category.objects.all(),
    }
    return render(request, 'storefront/search_results.html', context)

def ofertas(request):
    """Página de ofertas (productos con descuento)."""
    # Suponiendo que 'discount_price' indica una oferta
    products = Product.objects.filter(discount_price__isnull=False, active=True).order_by('-price')
    
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'categories': Category.objects.all(),
        'title': 'Ofertas del Día'
    }
    return render(request, 'storefront/ofertas.html', context)


# --- VISTAS DEL CARRITO ---

def cart(request):
    """Muestra el contenido del carrito."""
    cart_obj = Cart(request)
    return render(request, 'storefront/cart.html', {'cart': cart_obj})

@require_POST
def cart_add(request):
    """Añade un producto al carrito (redirección)."""
    product_id = request.POST.get('product_id')
    quantity = int(request.POST.get('quantity', 1))
    override = request.POST.get('override', False) == 'True'
    
    product = get_object_or_404(Product, id=product_id)
    cart_obj = Cart(request)
    cart_obj.add(product, quantity, override)
    
    messages.success(request, f'{product.name} ha sido añadido al carrito.')
    return redirect('storefront:cart')

@require_POST
def cart_remove(request):
    """Elimina un producto del carrito (redirección)."""
    product_id = request.POST.get('product_id')
    product = get_object_or_404(Product, id=product_id)
    cart_obj = Cart(request)
    cart_obj.remove(product)
    
    messages.info(request, f'{product.name} ha sido eliminado del carrito.')
    return redirect('storefront:cart')

@require_POST
def cart_update(request):
    """Actualiza la cantidad de un producto en el carrito (redirección)."""
    product_id = request.POST.get('product_id')
    quantity = int(request.POST.get('quantity', 1))
    
    product = get_object_or_404(Product, id=product_id)
    cart_obj = Cart(request)
    # Usamos override=True para establecer la cantidad exacta
    cart_obj.add(product, quantity, override_quantity=True) 
    
    messages.success(request, f'Cantidad de {product.name} actualizada.')
    return redirect('storefront:cart')


# --- VISTAS DE CHECKOUT Y PEDIDOS ---

@login_required(login_url='auth:login')
def checkout(request):
    """Muestra el formulario de envío y pago."""
    cart_obj = Cart(request)
    if not cart_obj:
        messages.error(request, "Tu carrito está vacío.")
        return redirect('storefront:products')

    # Intenta precargar el formulario con datos del perfil del cliente
    try:
        profile = Profile.objects.get(user=request.user)
        initial_data = {
            'shipping_name': request.user.get_full_name() or request.user.username,
            'shipping_address': profile.address,
            'shipping_city': profile.city,
            'shipping_state': profile.state,
            'shipping_zip': profile.zip_code,
            'shipping_country': profile.country,
            'email': request.user.email,
            'phone': profile.phone,
        }
    except Profile.DoesNotExist:
        initial_data = {'email': request.user.email}

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            # Guardar temporalmente los datos en la sesión y redirigir a confirmación
            request.session['checkout_data'] = form.cleaned_data
            return redirect('storefront:checkout_confirm')
    else:
        form = CheckoutForm(initial=initial_data)

    context = {
        'cart': cart_obj,
        'form': form,
    }
    return render(request, 'storefront/checkout.html', context)


@login_required(login_url='auth:login')
@require_POST
def checkout_confirm(request):
    """
    Confirma la orden: Simula el pago y envía la orden al Microservicio de Ventas.
    """
    cart_obj = Cart(request)
    checkout_data = request.session.get('checkout_data')

    if not cart_obj or not checkout_data:
        messages.error(request, "Tu sesión de compra ha expirado o el carrito está vacío.")
        return redirect('storefront:checkout')

    # 1. Preparar la estructura de la Orden para el microservicio
    # Mapeo a la estructura esperada por el Microservicio de Ventas
    order_data = {
        'cliente_id': request.user.id, # ID del usuario, usado como clave externa en el microservicio
        'total': float(cart_obj.get_total_price()),
        'estado': 'Pendiente', # Estado inicial
        'direccion_envio': checkout_data['shipping_address'],
        'ciudad_envio': checkout_data['shipping_city'],
        'pais_envio': checkout_data['shipping_country'],
        'detalles': [
            {
                'producto_id': int(item['product'].id), # ID del producto en el catálogo
                'cantidad': item['quantity'],
                'precio_unitario': float(item['price'])
            }
            for item in cart_obj
        ]
    }

    try:
        # 2. Enviar la orden al Microservicio de Ventas
        response = requests.post(
            f"{settings.MICROSERVICES['VENTAS']['BASE_URL']}api/pedidos/crear/",
            json=order_data,
            headers={
                'X-API-Key': settings.MICROSERVICES['VENTAS']['API_KEY'],
                'Authorization': f'Token {request.session["user"]["token"]}' # Usar el token del usuario autenticado
            },
            timeout=10 # Aumentar el timeout por si el proceso de pedido es más largo
        )

        if response.status_code == 201:
            # 3. Orden creada exitosamente
            response_data = response.json()
            order_reference = response_data.get('order_id', 'N/A')
            
            # 4. Vaciar el carrito y la data de checkout
            cart_obj.clear()
            del request.session['checkout_data']
            
            messages.success(request, f'¡Tu pedido ha sido confirmado! Referencia: {order_reference}. Recibirás un correo de confirmación.')
            # Redirigir a la página de detalles del pedido o a una página de éxito
            return redirect('storefront:order_detail', order_id=order_reference)
        else:
            # 5. Error del microservicio
            error_msg = response.json().get('detail', 'No se pudo completar el pedido. Intente de nuevo.')
            logger.error(f"Error MS Ventas al crear pedido (HTTP {response.status_code}): {error_msg}")
            messages.error(request, f'Error al procesar el pedido: {error_msg}')
            return redirect('storefront:checkout') # Volver al checkout

    except requests.RequestException as e:
        # 6. Error de conexión
        logger.error(f"Error de conexión al microservicio de Ventas: {str(e)}")
        messages.error(request, 'Error de conexión. El servicio de pedidos no está disponible. Intente más tarde.')
        return redirect('storefront:checkout')


@login_required(login_url='auth:login')
def profile(request):
    """Muestra la vista de perfil del cliente."""
    # Lógica para obtener el perfil del microservicio de Ventas... (PENDIENTE DE IMPLEMENTAR)
    messages.info(request, "Vista de perfil pendiente de conexión a Microservicio.")
    return render(request, 'storefront/profile.html', {})

@login_required(login_url='auth:login')
def profile_edit(request):
    """Permite al cliente editar su perfil."""
    # Lógica para editar el perfil y enviar los cambios al microservicio... (PENDIENTE DE IMPLEMENTAR)
    return render(request, 'storefront/profile_edit.html', {})

@login_required(login_url='auth:login')
def orders(request):
    """Muestra la lista de pedidos del cliente."""
    # Lógica para obtener la lista de pedidos del microservicio de Ventas... (PENDIENTE DE IMPLEMENTAR)
    return render(request, 'storefront/orders.html', {})

@login_required(login_url='auth:login')
def order_detail(request, order_id):
    """Muestra el detalle de un pedido específico."""
    # Lógica para obtener el detalle de un pedido del microservicio... (PENDIENTE DE IMPLEMENTAR)
    return render(request, 'storefront/order_detail.html', {'order_id': order_id})


# --- VISTAS DE INFORMACIÓN (Estáticas) ---

def about(request):
    """Página Sobre Nosotros."""
    return render(request, 'storefront/about.html')

def contact(request):
    """Página de Contacto (con formulario si es necesario)."""
    return render(request, 'storefront/contact.html')

def faq(request):
    """Página de Preguntas Frecuentes."""
    return render(request, 'storefront/faq.html')

def shipping(request):
    """Página de Políticas de Envío."""
    return render(request, 'storefront/shipping.html')

def returns(request):
    """Página de Políticas de Devolución."""
    return render(request, 'storefront/returns.html')

def warranty(request):
    """Página de Garantía."""
    return render(request, 'storefront/warranty.html')

def privacy(request):
    """Página de Política de Privacidad."""
    return render(request, 'storefront/privacy.html')

def terms(request):
    """Página de Términos y Condiciones."""
    return render(request, 'storefront/terms.html')


# --- API ENDPOINTS DE CARRITO (AJAX) ---
# [Se mantienen los endpoints de API de carrito tal como estaban, ya que solo dependen de la sesión]

@require_POST
def api_cart_add(request):
    """API para añadir productos al carrito (AJAX)."""
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))
        override = data.get('override', False)
        
        product = get_object_or_404(Product, id=product_id)
        cart_obj = Cart(request)
        cart_obj.add(product, quantity, override)
        
        # Recalcular el total y la cantidad de items para la respuesta
        total = float(cart_obj.get_total_price())
        total_items = len(cart_obj)
        
        return JsonResponse({
            'success': True,
            'total': total,
            'total_items': total_items,
            'product_name': product.name,
            'new_quantity': cart_obj.cart.get(str(product_id), {}).get('quantity', 0)
        })
    except Exception as e:
        logger.error(f"Error en api_cart_add: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@require_POST
def api_cart_update(request):
    """API para actualizar la cantidad de un producto."""
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        quantity = int(data.get('quantity'))
        
        product = get_object_or_404(Product, id=product_id)
        cart_obj = Cart(request)
        
        # Usamos add con override=True para establecer la cantidad exacta
        cart_obj.add(product, quantity, override_quantity=True)
        
        total = float(cart_obj.get_total_price())
        total_items = len(cart_obj)
        
        return JsonResponse({
            'success': True,
            'total': total,
            'total_items': total_items,
            'new_quantity': cart_obj.cart.get(str(product_id), {}).get('quantity', 0)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@require_POST
def api_cart_remove(request):
    """API para eliminar productos del carrito."""
    try:
        data = json.loads(request.body)
        product_id = str(data.get('product_id'))
        
        product = get_object_or_404(Product, id=product_id)
        cart_obj = Cart(request)
        cart_obj.remove(product)
        
        total = float(cart_obj.get_total_price())
        total_items = len(cart_obj)
        
        return JsonResponse({
            'success': True,
            'total': total,
            'total_items': total_items
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@require_POST
def api_checkout_validate(request):
    """API para validar datos del checkout."""
    try:
        data = json.loads(request.body)
        form = CheckoutForm(data)
        
        if form.is_valid():
            return JsonResponse({'valid': True})
        else:
            # Devuelve los errores de validación del formulario
            return JsonResponse({
                'valid': False,
                'errors': form.errors.as_json() # Usar as_json para serializar los errores
            }, status=400)
    except Exception as e:
        return JsonResponse({'valid': False, 'error': str(e)}, status=500)
