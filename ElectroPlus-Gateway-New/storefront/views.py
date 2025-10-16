from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
import json
import unicodedata
import re
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from decimal import Decimal
from django.conf import settings
from django.core.paginator import Paginator
from django.contrib import messages
from .models import Product, Review, Category, Order
from .cart import Cart

def product_list(request):
    """Vista para mostrar la lista de productos."""
    # Parámetros de filtro y búsqueda
    category_slug = request.GET.get('category')
    search_query = request.GET.get('q', '').strip()
    ordering = request.GET.get('sort', '-id')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    is_ofertas = request.GET.get('active_coupon') == 'true'

    # Consulta base
    products = Product.objects.filter(is_active=True).select_related('category')

    # Aplicar filtros
    if category_slug:
        products = products.filter(category__slug=category_slug)
    if search_query:
        products = products.filter(name__icontains=search_query)
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    # Ordenamiento
    valid_ordering = ['name', '-name', 'price', '-price', 'id', '-id']
    if ordering not in valid_ordering:
        ordering = '-id'
    products = products.order_by(ordering)

    # Paginación
    paginator = Paginator(products, 12)  # 12 productos por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Categorías para el filtro
    categories = Category.objects.all()

    # Obtener categoría seleccionada
    selected_category = None
    if category_slug:
        try:
            selected_category = Category.objects.get(slug=category_slug)
        except Category.DoesNotExist:
            pass

    context = {
        'products': page_obj,
        'categories': categories,
        'selected_category': selected_category,
        'search_query': search_query,
        'ordering': ordering,
        'page_obj': page_obj,
        'is_ofertas': is_ofertas,
    }

    return render(request, 'storefront/product_list.html', context)

def product_detail(request, slug):
    """Vista para mostrar el detalle de un producto."""
    product = get_object_or_404(
        Product.objects.select_related('category').prefetch_related('reviews'),
        slug=slug,
        is_active=True
    )

    # Reseñas del producto
    reviews = product.reviews.all().order_by('-created_at')

    # Obtener productos relacionados de la misma categoría
    related_products = Product.objects.filter(
        category=product.category,
        is_active=True
    ).exclude(id=product.id).order_by('?')[:4]  # Selecciona 4 productos aleatorios

    context = {
        'product': product,
        'reviews': reviews,
        'related_products': related_products,
    }

    return render(request, 'storefront/product_detail.html', context)

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

def chatbot_response(request):
    """Vista para manejar las respuestas del chatbot de atención al cliente."""
    if request.method == 'POST':
        # Soportar tanto application/json (fetch) como form-encoded (POST)
        user_message_raw = ''
        content_type = request.META.get('CONTENT_TYPE', '')
        if content_type.startswith('application/json'):
            try:
                payload = json.loads(request.body.decode('utf-8') or '{}')
                user_message_raw = payload.get('message', '')
            except Exception:
                user_message_raw = ''
        else:
            user_message_raw = request.POST.get('message', '')

        # Normalizar: trim, lower, quitar tildes y puntuación para mejorar matching
        def normalize_text(s):
            if not s:
                return ''
            s = s.strip().lower()
            # Quitar tildes/diacríticos
            s = unicodedata.normalize('NFD', s)
            s = ''.join(ch for ch in s if unicodedata.category(ch) != 'Mn')
            # Quitar caracteres que no sean letras/números/espacio
            s = re.sub(r'[^a-z0-9\s]', ' ', s)
            # Colapsar espacios
            s = re.sub(r'\s+', ' ', s).strip()
            return s

        user_message = normalize_text(user_message_raw)

        # Lógica simple del chatbot basada en reglas
        response = get_chatbot_response(user_message)

        resp = {
            'response': response,
            'timestamp': timezone.now().strftime('%H:%M')
        }

        # Incluir datos de depuración si estamos en DEBUG para ayudar a diagnosticar
        if getattr(settings, 'DEBUG', False):
            resp['debug'] = {
                'raw': user_message_raw,
                'normalized': user_message,
                'content_type': content_type,
            }

        return JsonResponse(resp)

    return JsonResponse({'error': 'Método no permitido'}, status=405)

def get_chatbot_response(message):
    """Función que genera respuestas del chatbot basadas en el mensaje del usuario."""
    
    # Palabras clave y respuestas (mapa base)
    responses = {
        # Saludos
        'hola': '¡Hola! Soy el asistente virtual de ElectroPlus. ¿En qué puedo ayudarte hoy?',
        'buenos dias': '¡Buenos días! ¿Cómo puedo ayudarte con tu compra en ElectroPlus?',
        'buenas tardes': '¡Buenas tardes! Estoy aquí para resolver tus dudas sobre nuestros productos.',
        'buenas noches': '¡Buenas noches! Aunque es tarde, estoy aquí para ayudarte.',
        
        # Información de productos
        'producto': 'Tenemos una amplia gama de productos electrónicos: computadoras, celulares, televisores, consolas y más. ¿Qué tipo de producto buscas?',
        'precio': 'Los precios de nuestros productos varían según el modelo y las ofertas disponibles. ¿Me puedes decir qué producto te interesa?',
        'stock': 'Para verificar la disponibilidad de stock, te recomiendo buscar el producto en nuestra tienda online o contactar a nuestro equipo de ventas.',
        
        # Pedidos y envíos
        'pedido': 'Para hacer un pedido, simplemente agrega los productos al carrito y procede al checkout. ¿Necesitas ayuda con algún pedido específico?',
        'envio': 'Realizamos envíos a todo el Perú. Los tiempos de entrega varían según la ubicación: Lima (1-2 días), provincias (3-5 días). El costo depende del peso y del destino.',
        'entrega': 'El tiempo de entrega depende de tu ubicación. Para Lima: 1-2 días hábiles. Para provincias: 3-5 días hábiles. Te enviaremos actualizaciones por correo electrónico.',
        
        # Devoluciones y cambios
        'devolucion': 'Aceptamos devoluciones dentro de los 7 días posteriores a la entrega, siempre que el producto esté en perfectas condiciones. Contacta a nuestro equipo para iniciar el proceso.',
        'cambio': 'Los cambios están sujetos a la disponibilidad de stock. Puedes cambiar tu producto por otro de igual o mayor valor; la diferencia de precio se cobrará si aplica.',
        'garantia': 'Todos nuestros productos cuentan con la garantía oficial del fabricante. La duración varía según el producto (6 meses a 2 años).',
        
        # Pagos
        'pago': 'Aceptamos tarjetas de crédito/débito, transferencias bancarias y pagos contra entrega. Todos los pagos son seguros.',
        'tarjeta': 'Aceptamos Visa, Mastercard y American Express. Tu información de pago está protegida mediante encriptación SSL.',
        
        # Contacto
        'telefono': 'Puedes contactarnos al: 01-123-4567 (Lima) o por WhatsApp: +51 987 654 321.',
        'email': 'Nuestro correo de atención al cliente es: soporte@electroplus.com.pe',
        'direccion': 'Nuestra tienda principal está en Av. Larco 123, Miraflores, Lima. También atendemos en nuestros locales de San Miguel y Surco.',
        
        # Ayuda general
        'ayuda': 'Estoy aquí para ayudarte con información sobre productos, pedidos, envíos, devoluciones y más. ¿Qué necesitas saber?',
        'gracias': '¡De nada! Fue un placer ayudarte. Si tienes más preguntas, no dudes en consultar.',
        'adios': '¡Hasta luego! Gracias por elegir ElectroPlus. ¡Que tengas un excelente día!',
        'chao': '¡Chao! Recuerda que estamos aquí para cualquier consulta futura.',
    }

    # Mapas de sinónimos: palabras que deberían mapearse a una keyword
    synonyms = {
        'hola': ['hola', 'buenas', 'buenos', 'buenos dias', 'buenas tardes', 'buenas noches'],
        'producto': ['producto', 'productos', 'articulo', 'artículos', 'articulo'],
        'precio': ['precio', 'precios', 'coste', 'costo', 'valor'],
        'stock': ['stock', 'disponible', 'disponibilidad'],
        'pedido': ['pedido', 'orden', 'comprar', 'compra'],
        'envio': ['envio', 'envío', 'entrega', 'tiempo entrega'],
        'devolucion': ['devolucion', 'devoluciones', 'devolver'],
        'garantia': ['garantia', 'garantía', 'garantias'],
        'pago': ['pago', 'pagos', 'metodo pago', 'tarjeta', 'transferencia'],
        'telefono': ['telefono', 'teléfono', 'whatsapp'],
        'email': ['email', 'correo', 'correo electrónico'],
        'direccion': ['direccion', 'ubicacion', 'donde estamos', 'dónde'],
        'ayuda': ['ayuda', 'soporte', 'ayudame'],
        'gracias': ['gracias', 'muchas gracias'],
        'adios': ['adios', 'chao', 'hasta luego']
    }

    # Tokenizar mensaje
    tokens = message.split()

    # 1) Coincidencia exacta
    if message in responses:
        return responses[message]

    # 2) Coincidencia por token usando sinónimos
    for key, syns in synonyms.items():
        for syn in syns:
            if syn in message:
                return responses.get(key, '')

    # 3) Coincidencia por palabras clave en tokens
    for keyword, response in responses.items():
        for token in tokens:
            if token == keyword:
                return response

    # 4) Matching aproximado: Levenshtein para mensajes cortos (fallback)
    def levenshtein(a, b):
        if a == b:
            return 0
        la, lb = len(a), len(b)
        if la == 0:
            return lb
        if lb == 0:
            return la
        prev = list(range(lb + 1))
        for i, ca in enumerate(a, start=1):
            curr = [i] + [0] * lb
            for j, cb in enumerate(b, start=1):
                insertions = prev[j] + 1
                deletions = curr[j - 1] + 1
                substitutions = prev[j - 1] + (0 if ca == cb else 1)
                curr[j] = min(insertions, deletions, substitutions)
            prev = curr
        return prev[lb]

    # Solo aplicar fuzzy para mensajes cortos (<= 40 chars) para evitar costes
    if len(message) <= 40 and message:
        best = (None, 999)
        for key in responses.keys():
            d = levenshtein(message, key)
            if d < best[1]:
                best = (key, d)
        # Umbral: si la distancia es pequeña relativa al tamaño
        if best[0] and best[1] <= max(1, len(best[0]) // 4):
            return responses[best[0]]
    
    # Respuestas por defecto
    if any(word in message for word in ['como', 'donde', 'cuando', 'que', 'cual']):
        return 'Para obtener información más específica, te recomiendo contactar directamente con nuestro equipo de atención al cliente al 01-123-4567 o por email a soporte@electroplus.com.pe'
    
    if any(word in message for word in ['problema', 'error', 'no funciona', 'defecto']):
        return 'Lamento escuchar que tienes un problema. Por favor, contacta a nuestro equipo técnico al 01-123-4567 para recibir asistencia especializada.'
    
    # Respuesta por defecto
    return 'Disculpa, no entendí tu consulta. ¿Podrías reformularla? Estoy aquí para ayudarte con información sobre productos, pedidos, envíos y atención al cliente.'

def cart_detail(request):
    """Vista para mostrar el detalle del carrito de compras."""
    cart = Cart(request)
    return render(request, 'storefront/cart_detail.html', {'cart': cart})

def cart_add(request, slug):
    """Vista para agregar productos al carrito."""
    cart = Cart(request)
    product = get_object_or_404(Product, slug=slug, is_active=True)

    if request.method == 'POST':
        # Soportar tanto form-encoded como application/json
        content_type = request.META.get('CONTENT_TYPE', '')
        quantity = 1
        if content_type.startswith('application/json'):
            try:
                payload = json.loads(request.body.decode('utf-8') or '{}')
                quantity = int(payload.get('quantity', 1))
            except Exception:
                quantity = 1
        else:
            try:
                quantity = int(request.POST.get('quantity', 1))
            except (ValueError, TypeError):
                quantity = 1

        cart.add(product=product, quantity=quantity, update_quantity=False)
        messages.success(request, f'{product.name} agregado al carrito.')

        # Detectar petición AJAX / fetch
        xrw = request.META.get('HTTP_X_REQUESTED_WITH', '') or request.headers.get('X-Requested-With', '')
        is_ajax = (xrw == 'XMLHttpRequest') or content_type.startswith('application/x-www-form-urlencoded') or content_type.startswith('application/json')

        if is_ajax:
            try:
                total_price = cart.get_total_price()
            except Exception:
                total_price = 0
            return JsonResponse({
                'success': True,
                'message': f'{product.name} agregado al carrito.',
                'cart_total': len(cart),
                'total_price': f"{total_price:.2f}" if hasattr(total_price, 'quantize') or isinstance(total_price, (int, float)) or isinstance(total_price, Decimal) else str(total_price),
            })

        return redirect('storefront:cart_detail')

    return redirect('storefront:product_detail', slug=slug)

def cart_update(request, product_id):
    """Vista para actualizar la cantidad de un producto en el carrito."""
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id, is_active=True)

    if request.method == 'POST':
        try:
            quantity = int(request.POST.get('quantity', 1))
        except (ValueError, TypeError):
            quantity = 1

        cart.add(product=product, quantity=quantity, update_quantity=True)

        # Calcular totales
        pid = str(product.id)
        item = cart.cart.get(pid)
        if item:
            item_total = Decimal(item.get('price', '0')) * item.get('quantity', 0)
        else:
            item_total = Decimal('0')

        total_price = cart.get_total_price()

        # Detectar petición AJAX / fetch: preferir headers
        content_type = request.META.get('CONTENT_TYPE', '')
        xrw = request.META.get('HTTP_X_REQUESTED_WITH', '') or request.headers.get('X-Requested-With', '')
        is_ajax = (xrw == 'XMLHttpRequest') or content_type.startswith('application/x-www-form-urlencoded') or content_type.startswith('application/json')

        if is_ajax:
            return JsonResponse({
                'success': True,
                'item_total': f"{item_total:.2f}",
                'total_price': f"{total_price:.2f}",
            })

        messages.success(request, f'Cantidad de {product.name} actualizada.')

    return redirect('storefront:cart_detail')

def cart_remove(request, product_id):
    """Vista para remover un producto del carrito."""
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id, is_active=True)
    cart.remove(product)
    messages.success(request, f'{product.name} removido del carrito.')
    return redirect('storefront:cart_detail')

@login_required
def checkout(request):
    """Vista para el proceso de checkout."""
    cart = Cart(request)

    if not cart:
        messages.error(request, 'Tu carrito está vacío.')
        return redirect('storefront:product_list')

    if request.method == 'POST':
        # Crear el pedido
        order = Order.objects.create(
            user=request.user,
            total=cart.get_total_price(),
            status='pending'
        )

        # Agregar items del carrito al pedido
        for item in cart:
            product = Product.objects.get(id=item['id'])
            order.items.create(
                product=product,
                quantity=item['quantity'],
                price=product.price
            )

        # Limpiar el carrito
        cart.clear()

        messages.success(request, f'Pedido #{order.id} creado exitosamente.')
        return redirect('storefront:order_history')

    return render(request, 'storefront/checkout.html', {'cart': cart})

@login_required
def order_history(request):
    """Vista para mostrar el historial de pedidos del usuario."""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'storefront/order_history.html', {'orders': orders})

@login_required
def cancel_order(request, order_id):
    """Vista para cancelar un pedido."""
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.status == 'pending':
        order.status = 'cancelled'
        order.save()
        messages.success(request, f'Pedido #{order.id} cancelado exitosamente.')
    else:
        messages.error(request, 'No se puede cancelar este pedido.')

    return redirect('storefront:order_history')

@login_required
def wishlist(request):
    """Vista para mostrar la lista de deseos del usuario."""
    # Asumiendo que hay un modelo Wishlist
    # wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product')
    # return render(request, 'storefront/wishlist.html', {'wishlist_items': wishlist_items})
    return render(request, 'storefront/wishlist.html')

@login_required
def toggle_wishlist(request, product_id):
    """Vista para agregar/remover productos de la lista de deseos."""
    product = get_object_or_404(Product, id=product_id, is_active=True)

    # Asumiendo que hay un modelo Wishlist
    # wishlist_item, created = Wishlist.objects.get_or_create(
    #     user=request.user,
    #     product=product
    # )
    #
    # if not created:
    #     wishlist_item.delete()
    #     messages.success(request, f'{product.name} removido de tu lista de deseos.')
    # else:
    #     messages.success(request, f'{product.name} agregado a tu lista de deseos.')

    return JsonResponse({'success': True})

@login_required
def profile(request):
    """Vista para mostrar y editar el perfil del usuario."""
    if request.method == 'POST':
        # Lógica para actualizar el perfil
        pass

    return render(request, 'storefront/profile.html')

def chatbot(request):
    """Vista principal del chatbot."""
    return render(request, 'storefront/chatbot.html')
