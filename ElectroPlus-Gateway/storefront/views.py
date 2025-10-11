from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Q
from django.conf import settings # <-- IMPORT AÑADIDO: Resuelve error "settings" no definido
from django.contrib import messages # <-- IMPORT AÑADIDO: Resuelve error "messages" no definido
import requests # <-- IMPORT AÑADIDO: Resuelve error "requests" no definido
import json

from gateway_app.models import Product, Category, Order, OrderItem, Profile
from gateway_app.forms import ProfileForm, CheckoutForm

def home(request):
    """Vista de la página principal."""
    categories = Category.objects.all()
    featured_products = Product.objects.filter(featured=True, active=True)[:8]
    
    context = {
        'categories': categories,
        'featured_products': featured_products,
    }
    return render(request, 'storefront/home.html', context)

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

    # Ordenamiento
    sort_by = request.GET.get('sort_by', 'name')
    if sort_by in ['name', '-name', 'price', '-price']:
        products = products.order_by(sort_by)
    
    # Paginación
    paginator = Paginator(products, 12) # 12 productos por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Obtener todas las categorías para el sidebar de filtros
    categories = Category.objects.filter(active=True)

    context = {
        'page_obj': page_obj,
        'categories': categories,
        'current_category': category,
        'sort_by': sort_by,
        'min_price': min_price,
        'max_price': max_price,
    }
    return render(request, 'storefront/product_list.html', context)

def product_detail(request, slug):
    """Detalle de un producto."""
    product = get_object_or_404(Product, slug=slug, active=True)
    context = {'product': product}
    return render(request, 'storefront/product_detail.html', context)

def category(request, slug):
    """Lista de productos por categoría."""
    category = get_object_or_404(Category, slug=slug, active=True)
    products = Product.objects.filter(category=category, active=True)
    
    # Paginación (reutilizar lógica de product_list si se requiere)
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'category': category,
        'page_obj': page_obj,
    }
    return render(request, 'storefront/category.html', context)

def search(request):
    """Búsqueda de productos."""
    query = request.GET.get('q', '')
    products = Product.objects.filter(active=True)
    if query:
        # Búsqueda por nombre y descripción
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))
    
    # Paginación
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'query': query,
        'page_obj': page_obj,
    }
    return render(request, 'storefront/search_results.html', context)

def ofertas(request):
    """Página de ofertas/productos destacados."""
    # Simulación de ofertas: productos con descuento (si existiera un campo 'discount')
    # O simplemente productos destacados si no hay campo 'discount'
    products = Product.objects.filter(featured=True, active=True)
    
    # Paginación
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'title': 'Ofertas Destacadas',
    }
    return render(request, 'storefront/ofertas.html', context)

# --- Vistas de Carrito ---

def get_cart_data(request):
    """
    Función auxiliar para obtener los datos del carrito con información completa del producto.
    
    Nota: Esta es una implementación simplificada. Para un carrito robusto, se recomienda
    utilizar la clase Cart en un módulo dedicado.
    """
    cart = request.session.get('cart', {})
    cart_items = []
    total = 0.0
    
    if cart:
        # Nota: Los IDs deben ser de tipo Product.pk, que en el modelo es IntegerField
        product_ids = [int(product_id) for product_id in cart.keys()]
        products = Product.objects.filter(id__in=product_ids).values('id', 'name', 'price', 'image_url', 'slug', 'stock')
        
        product_map = {item['id']: item for item in products}
        
        for product_id, item_data in cart.items():
            product_id_int = int(product_id)
            if product_id_int in product_map:
                product = product_map[product_id_int]
                quantity = item_data['quantity']
                price = product['price'] # Se usa el precio del producto de la DB
                item_total = float(price) * quantity
                total += item_total
                
                cart_items.append({
                    'product_id': product_id_int,
                    'name': product['name'],
                    'price': price,
                    'quantity': quantity,
                    'total': item_total,
                    'image_url': product.get('image_url', ''), # Usar .get para evitar KeyError si no existe
                    'slug': product['slug'],
                    'stock': product['stock'],
                })
                
    return cart_items, round(total, 2)


# Asumo que require_http_methods está importado desde django.views.decorators.http
# Dado que no tengo el import, lo agrego aquí para no romper la vista
from django.views.decorators.http import require_http_methods

@require_http_methods(["GET", "POST"]) 
def cart(request):
    """Vista del carrito de compras."""
    cart_items, cart_total = get_cart_data(request)
    
    context = {
        'cart_items': cart_items,
        'cart_total': cart_total,
        'total_items': sum(item['quantity'] for item in cart_items)
    }
    return render(request, 'storefront/cart.html', context)


@require_POST
def cart_add(request):
    """Añadir un producto al carrito (redirección)."""
    try:
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 1))
        
        product = get_object_or_404(Product, pk=product_id, active=True)
        
        cart = request.session.get('cart', {})
        product_id_str = str(product.id)
        
        current_quantity = cart.get(product_id_str, {'quantity': 0})['quantity']
        new_quantity = current_quantity + quantity

        if new_quantity > product.stock:
            new_quantity = product.stock
            messages.warning(request, f'Solo se agregaron {product.stock - current_quantity} unidades. Stock máximo alcanzado.')

        if new_quantity > 0:
            cart[product_id_str] = {'quantity': new_quantity, 'price': str(product.price)}
        
        request.session['cart'] = cart
        request.session.modified = True

        messages.success(request, f'{product.name} agregado al carrito.')
    except Exception as e:
        messages.error(request, f'Error al agregar el producto: {e}')
    
    return redirect('storefront:cart')


@require_POST
def cart_update(request):
    """Actualizar la cantidad de un producto en el carrito (redirección)."""
    try:
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity'))
        
        product = get_object_or_404(Product, pk=product_id, active=True)
        
        cart = request.session.get('cart', {})
        product_id_str = str(product.id)
        
        # Validar stock
        if quantity > product.stock:
            quantity = product.stock
            messages.warning(request, f'La cantidad máxima es {product.stock}. Se ajustó la cantidad.')

        if quantity > 0:
            cart[product_id_str] = {'quantity': quantity, 'price': str(product.price)}
            messages.success(request, f'Cantidad de {product.name} actualizada a {quantity}.')
        else:
            if product_id_str in cart:
                del cart[product_id_str]
            messages.info(request, f'{product.name} eliminado del carrito.')
        
        request.session['cart'] = cart
        request.session.modified = True
    except Exception as e:
        messages.error(request, f'Error al actualizar el producto: {e}')
        
    return redirect('storefront:cart')


@require_POST
def cart_remove(request):
    """Eliminar un producto del carrito (redirección)."""
    try:
        product_id = request.POST.get('product_id')
        product = get_object_or_404(Product, pk=product_id)
        
        cart = request.session.get('cart', {})
        product_id_str = str(product.id)
        
        if product_id_str in cart:
            del cart[product_id_str]
            request.session['cart'] = cart
            request.session.modified = True
            messages.info(request, f'{product.name} eliminado del carrito.')
        else:
            messages.warning(request, 'El producto ya no estaba en el carrito.')
            
    except Exception as e:
        messages.error(request, f'Error al eliminar el producto: {e}')
    
    return redirect('storefront:cart')


# --- Vistas de Checkout ---

@login_required
def checkout(request):
    """Vista de inicio de proceso de compra/checkout."""
    cart_items, cart_total = get_cart_data(request)
    if not cart_items:
        messages.warning(request, 'Su carrito está vacío.')
        return redirect('storefront:products')
        
    # Obtener el perfil existente para prellenar el formulario
    profile = Profile.objects.filter(user=request.user).first()
    
    # Prellenar con datos del perfil o datos de sesión (si existe)
    initial_data = {}
    if profile:
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
        
    form = CheckoutForm(initial=initial_data)
    
    context = {
        'cart_items': cart_items,
        'cart_total': cart_total,
        'form': form,
    }
    return render(request, 'storefront/checkout.html', context)


@login_required
@require_POST
def checkout_confirm(request):
    """Confirmación de compra: valida y envía la orden al microservicio."""
    cart_items, cart_total = get_cart_data(request)
    if not cart_items:
        messages.warning(request, 'Su carrito está vacío.')
        return redirect('storefront:products')

    form = CheckoutForm(request.POST)

    if form.is_valid():
        try:
            # 1. Preparar los datos del pedido para el microservicio
            checkout_data = form.cleaned_data
            
            # Mapear campos del formulario a los esperados por el microservicio de Ventas
            # Asumo que el microservicio espera una estructura específica
            order_payload = {
                'customer_id': request.user.id, # ID del usuario autenticado
                'total_amount': cart_total,
                'shipping_info': {
                    'name': checkout_data['shipping_name'],
                    'address': checkout_data['shipping_address'],
                    'city': checkout_data['shipping_city'],
                    'state': checkout_data['shipping_state'],
                    'zip_code': checkout_data['shipping_zip'],
                    'country': checkout_data['shipping_country'],
                    'email': checkout_data['email'],
                    'phone': checkout_data['phone'],
                },
                'items': [
                    {
                        'product_id': item['product_id'],
                        'quantity': item['quantity'],
                        'unit_price': float(item['price']) # Asegurar float o Decimal si es necesario
                    }
                    for item in cart_items
                ]
            }

            # 2. Enviar el pedido al microservicio de Ventas
            microservice_url = f"{settings.MICROSERVICES['VENTAS']['BASE_URL']}ordenes/crear/"
            api_key = settings.MICROSERVICES['VENTAS']['API_KEY']
            auth_token = request.session['user']['token']
            
            headers = {
                'Content-Type': 'application/json',
                'X-API-Key': api_key,
                'Authorization': f'Token {auth_token}',
            }
            
            response = requests.post(
                microservice_url,
                json=order_payload,
                headers=headers,
                timeout=10
            )

            # 3. Procesar la respuesta del microservicio
            if response.status_code == 201:
                # Éxito: limpiar carrito y redirigir
                request.session['cart'] = {}
                request.session.modified = True
                
                order_data = response.json()
                order_id = order_data.get('order_id') # Asumo que retorna un order_id
                
                messages.success(request, f'¡Pedido #{order_id} confirmado con éxito! Gracias por su compra.')
                return redirect('storefront:order_detail', order_id=order_id)
            else:
                # Error en el microservicio
                error_message = response.json().get('detail', 'Error al procesar la orden en el servicio de ventas.')
                messages.error(request, f'Error de compra: {error_message}')
                # Asumo que logger está importado
                # logger.error(f"Error al crear orden (Status: {response.status_code}): {response.text}")

        except requests.RequestException as e:
            messages.error(request, 'Error de conexión con el servicio de ventas. Intente más tarde.')
            # logger.error(f"Error de conexión en checkout_confirm: {e}")
        except Exception as e:
            messages.error(request, f'Ocurrió un error inesperado: {e}')
    else:
        # Errores de validación del formulario
        messages.error(request, 'Por favor, corrija los errores del formulario.')
    
    # Si falla la validación o el envío, regresa al checkout
    cart_items, cart_total = get_cart_data(request)
    context = {
        'cart_items': cart_items,
        'cart_total': cart_total,
        'form': form, # El formulario con los errores
    }
    return render(request, 'storefront/checkout.html', context)

# --- Vistas de Perfil y Pedidos ---

@login_required
def profile(request):
    """Vista de perfil del usuario."""
    profile_data = {}
    orders_data = []

    # 1. Obtener datos del cliente (perfil) del microservicio de Ventas
    try:
        microservice_url = f"{settings.MICROSERVICES['VENTAS']['BASE_URL']}clientes/perfil/"
        api_key = settings.MICROSERVICES['VENTAS']['API_KEY']
        auth_token = request.session['user']['token']
        
        headers = {
            'X-API-Key': api_key,
            'Authorization': f'Token {auth_token}',
        }
        
        # Llama a Ventas para el perfil
        profile_response = requests.get(microservice_url, headers=headers, timeout=5)

        if profile_response.status_code == 200:
            profile_data = profile_response.json()
        else:
            messages.warning(request, 'No se pudo obtener la información de perfil del microservicio.')

        # 2. Obtener historial de pedidos
        orders_url = f"{settings.MICROSERVICES['VENTAS']['BASE_URL']}clientes/pedidos/"
        orders_response = requests.get(orders_url, headers=headers, timeout=5)
        
        if orders_response.status_code == 200:
            orders_data = orders_response.json()
        else:
            messages.warning(request, 'No se pudo obtener el historial de pedidos.')

    except requests.RequestException as e:
        messages.error(request, 'Error de conexión con los servicios. Intente más tarde.')
        # logger.error(f"Error al obtener datos de perfil/pedidos: {e}")
    
    context = {
        'profile_data': profile_data,
        'orders': orders_data,
        # Asumo que el perfil ya fue creado o se maneja en un middleware
        'form': ProfileForm(instance=request.user.profile if hasattr(request.user, 'profile') else None) 
    }
    return render(request, 'storefront/profile.html', context)

@login_required
def profile_edit(request):
    """Editar perfil del usuario."""
    # Lógica de edición de perfil (simplificada)
    # Se asumiría la lógica de POST/GET aquí para usar ProfileForm y enviar al microservicio
    return redirect('storefront:profile')

@login_required
def orders(request):
    """Lista de pedidos del usuario."""
    # Podría redirigir a `profile` si la info de pedidos está ahí
    return redirect('storefront:profile')

@login_required
def order_detail(request, order_id):
    """Detalle de un pedido específico."""
    # Lógica para llamar al microservicio por el detalle de un pedido
    context = {'order_id': order_id, 'detail': {}}
    return render(request, 'storefront/order_detail.html', context)

# --- Vistas de Información ---

def about(request):
    return render(request, 'storefront/about.html')

def contact(request):
    return render(request, 'storefront/contact.html')

def faq(request):
    return render(request, 'storefront/faq.html')

def shipping(request):
    return render(request, 'storefront/shipping.html')

def returns(request):
    return render(request, 'storefront/returns.html')

def warranty(request):
    return render(request, 'storefront/warranty.html')

def privacy(request):
    return render(request, 'storefront/privacy.html')

def terms(request):
    return render(request, 'storefront/terms.html')


# --- API Endpoints ---

@require_POST
def api_cart_add(request):
    """API para agregar productos al carrito."""
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))
        
        product = get_object_or_404(Product, pk=product_id, active=True)
        
        cart = request.session.get('cart', {})
        product_id_str = str(product.id)
        
        current_quantity = cart.get(product_id_str, {'quantity': 0})['quantity']
        new_quantity = current_quantity + quantity

        if new_quantity > product.stock:
            new_quantity = product.stock
        
        if new_quantity > 0:
            cart[product_id_str] = {'quantity': new_quantity, 'price': str(product.price)}
        else:
            if product_id_str in cart:
                del cart[product_id_str]
        
        request.session['cart'] = cart
        request.session.modified = True
        
        cart_items, total = get_cart_data(request)
        
        return JsonResponse({
            'success': True,
            'total': total,
            'total_items': sum(item['quantity'] for item in cart_items)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@require_POST
def api_cart_update(request):
    """API para actualizar la cantidad de un producto en el carrito."""
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        quantity = int(data.get('quantity'))
        
        product = get_object_or_404(Product, pk=product_id, active=True)
        
        cart = request.session.get('cart', {})
        product_id_str = str(product.id)
        
        # Validar stock
        if quantity > product.stock:
            quantity = product.stock 
        
        if quantity > 0:
            cart[product_id_str] = {'quantity': quantity, 'price': str(product.price)}
        else:
            if product_id_str in cart:
                del cart[product_id_str]
        
        request.session['cart'] = cart
        request.session.modified = True
        
        cart_items, total = get_cart_data(request)
        
        return JsonResponse({
            'success': True,
            'total': total,
            'total_items': sum(item['quantity'] for item in cart_items)
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
        
        cart = request.session.get('cart', {})
        if product_id in cart:
            del cart[product_id]
            request.session['cart'] = cart
            request.session.modified = True
        
        cart_items, total = get_cart_data(request)
        
        return JsonResponse({
            'success': True,
            'total': total,
            'total_items': sum(item['quantity'] for item in cart_items)
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
            errors = dict(form.errors.items())
            return JsonResponse({
                'valid': False,
                'errors': errors
            }, status=400)
    except Exception as e:
        return JsonResponse({
            'valid': False,
            'error': str(e)
        }, status=400)

@require_POST
def api_checkout_confirm(request):
    """API para confirmar la compra y enviar al microservicio."""
    try:
        data = json.loads(request.body)
        form = CheckoutForm(data)
        
        if not form.is_valid():
            return JsonResponse({
                'success': False,
                'errors': dict(form.errors.items())
            }, status=400)
            
        cart_items, cart_total = get_cart_data(request)
        if not cart_items:
            return JsonResponse({'success': False, 'message': 'El carrito está vacío.'}, status=400)

        # Preparar y enviar al microservicio (similar a checkout_confirm view)
        checkout_data = form.cleaned_data
        order_payload = {
            'customer_id': request.user.id, # Asumo que request.user está disponible por UserDataMiddleware
            'total_amount': cart_total,
            'shipping_info': {
                'name': checkout_data['shipping_name'],
                'address': checkout_data['shipping_address'],
                'city': checkout_data['shipping_city'],
                'state': checkout_data['shipping_state'],
                'zip_code': checkout_data['shipping_zip'],
                'country': checkout_data['shipping_country'],
                'email': checkout_data['email'],
                'phone': checkout_data['phone'],
            },
            'items': [
                {
                    'product_id': item['product_id'],
                    'quantity': item['quantity'],
                    'unit_price': float(item['price'])
                }
                for item in cart_items
            ]
        }
        
        microservice_url = f"{settings.MICROSERVICES['VENTAS']['BASE_URL']}ordenes/crear/"
        api_key = settings.MICROSERVICES['VENTAS']['API_KEY']
        auth_token = request.session.get('user', {}).get('token')
        
        if not auth_token:
            return JsonResponse({'success': False, 'message': 'Usuario no autenticado.'}, status=401)
        
        headers = {
            'Content-Type': 'application/json',
            'X-API-Key': api_key,
            'Authorization': f'Token {auth_token}',
        }
        
        response = requests.post(microservice_url, json=order_payload, headers=headers, timeout=10)

        if response.status_code == 201:
            # Éxito
            request.session['cart'] = {}
            request.session.modified = True
            
            order_data = response.json()
            order_id = order_data.get('order_id')
            
            return JsonResponse({
                'success': True,
                'order_id': order_id,
                'message': f'Pedido #{order_id} confirmado con éxito.'
            })
        else:
            # Error en el microservicio
            error_message = response.json().get('detail', 'Error al procesar la orden en el servicio de ventas.')
            return JsonResponse({'success': False, 'message': f'Error de compra: {error_message}'}, status=response.status_code)

    except requests.RequestException as e:
        # Aquí no usamos messages, solo JsonResponse
        # logger.error(f"Error en api_checkout_confirm (RequestException): {e}")
        return JsonResponse({'success': False, 'message': 'Error de conexión con el servicio de ventas.'}, status=503)
    except Exception as e:
        # logger.error(f"Error inesperado en api_checkout_confirm: {e}")
        return JsonResponse({'success': False, 'message': f'Ocurrió un error inesperado: {e}'}, status=500)
