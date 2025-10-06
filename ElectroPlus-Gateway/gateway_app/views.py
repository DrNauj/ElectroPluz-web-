"""
Views for gateway app - ElectroPlus implementation
"""

import requests
import logging
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.paginator import Paginator
from django.http import JsonResponse
from .forms import LoginForm, RegisterForm

logger = logging.getLogger(__name__)

def home(request):
    """
    Vista principal de la tienda que muestra productos y categorías
    """
    try:
        # Obtener productos del servicio de inventario
        products_response = requests.get(
            f"{settings.MICROSERVICES['INVENTARIO']['BASE_URL']}api/productos/",
            headers={'X-API-Key': settings.MICROSERVICES['INVENTARIO']['API_KEY']}
        )
        products_data = products_response.json()
        
        # Obtener categorías
        categories_response = requests.get(
            f"{settings.MICROSERVICES['INVENTARIO']['BASE_URL']}api/categorias/",
            headers={'X-API-Key': settings.MICROSERVICES['INVENTARIO']['API_KEY']}
        )
        categories = categories_response.json()
        
        # Aplicar filtros
        category = request.GET.get('category')
        sort = request.GET.get('sort')
        search = request.GET.get('search')
        
        if category:
        
        'user': user_data
    })
 
def cart_view(request):
    """Mostrar el carrito almacenado en la sesión"""
    cart = request.session.get('cart', {})
    cart_count = request.session.get('cart_count', 0)
    return render(request, 'shop/cart.html', {'cart': cart, 'cart_count': cart_count})


@require_http_methods(["POST"])
    except requests.RequestException as e:
        if not category:
            headers={'X-API-Key': settings.MICROSERVICES['INVENTARIO']['API_KEY']}
        
                products_data = sorted(products_data, key=lambda x: x['nombre'])
        products = paginator.get_page(page)
        return render(request, 'base/dashboard.html', {})
"""
Cleaned views for gateway_app. Restores public views and API proxies.
"""

import logging
import requests
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


def home(request):
    try:
        products_response = requests.get(
            f"{settings.MICROSERVICES['INVENTARIO']['BASE_URL']}api/productos/",
            headers={'X-API-Key': settings.MICROSERVICES['INVENTARIO']['API_KEY']}
        )
        products_data = products_response.json()

        categories_response = requests.get(
            f"{settings.MICROSERVICES['INVENTARIO']['BASE_URL']}api/categorias/",
            headers={'X-API-Key': settings.MICROSERVICES['INVENTARIO']['API_KEY']}
        )
        categories = categories_response.json()

        category = request.GET.get('category')
        sort = request.GET.get('sort')
        search = request.GET.get('search')

        if category:
            try:
                cid = int(category)
                products_data = [p for p in products_data if p.get('categoria') == cid]
            except Exception:
                pass

        if search:
            s = search.lower()
            products_data = [p for p in products_data if s in p.get('nombre', '').lower() or s in p.get('descripcion', '').lower()]

        if sort:
            if sort == 'price_low':
                products_data = sorted(products_data, key=lambda x: float(x.get('precio', 0)))
            elif sort == 'price_high':
                products_data = sorted(products_data, key=lambda x: float(x.get('precio', 0)), reverse=True)
            elif sort == 'name':
                products_data = sorted(products_data, key=lambda x: x.get('nombre', ''))
            else:
                products_data = sorted(products_data, key=lambda x: x.get('id', 0), reverse=True)

        paginator = Paginator(products_data, 12)
        page = request.GET.get('page')
        products = paginator.get_page(page)

        special_offers = [p for p in products_data if p.get('descuento', 0) > 0][:4]

        context = {
            'products': products,
            'categories': categories,
            'special_offers': special_offers,
            'active_category': category,
            'active_sort': sort,
            'search_query': search,
            'cart_count': request.session.get('cart_count', 0),
        }
        return render(request, 'shop/home.html', context)
    except requests.RequestException as e:
        logger.error(f"Error al obtener datos de productos: {e}")
        messages.error(request, "Error al cargar los productos. Por favor, intente más tarde.")
        return render(request, 'shop/home.html', {'error': True, 'categories': [], 'products': [], 'special_offers': []})


def category_products(request, slug):
    try:
        categories_response = requests.get(
            f"{settings.MICROSERVICES['INVENTARIO']['BASE_URL']}api/categorias/",
            headers={'X-API-Key': settings.MICROSERVICES['INVENTARIO']['API_KEY']}
        )
        categories = categories_response.json()
        category = next((c for c in categories if c.get('slug') == slug), None)
        if not category:
            messages.error(request, "Categoría no encontrada")
            return redirect('home')

        products_response = requests.get(
            f"{settings.MICROSERVICES['INVENTARIO']['BASE_URL']}api/productos/?categoria={category.get('id')}",
            headers={'X-API-Key': settings.MICROSERVICES['INVENTARIO']['API_KEY']}
        )
        products_data = products_response.json()

        sort = request.GET.get('sort')
        search = request.GET.get('search')
        if search:
            s = search.lower()
            products_data = [p for p in products_data if s in p.get('nombre', '').lower() or s in p.get('descripcion', '').lower()]
        if sort:
            if sort == 'price_low':
                products_data = sorted(products_data, key=lambda x: float(x.get('precio', 0)))
            elif sort == 'price_high':
                products_data = sorted(products_data, key=lambda x: float(x.get('precio', 0)), reverse=True)
            elif sort == 'name':
                products_data = sorted(products_data, key=lambda x: x.get('nombre', ''))
            else:
                products_data = sorted(products_data, key=lambda x: x.get('id', 0), reverse=True)

        paginator = Paginator(products_data, 12)
        page = request.GET.get('page')
        products = paginator.get_page(page)

        context = {
            'category': category,
            'products': products,
            'categories': categories,
            'active_sort': sort,
            'search_query': search,
            'cart_count': request.session.get('cart_count', 0),
        }
        return render(request, 'shop/category.html', context)
    except requests.RequestException as e:
        logger.error(f"Error al obtener productos de la categoría: {e}")
        messages.error(request, "Error de conexión. Por favor, intente más tarde.")
        return redirect('home')


def check_auth(request):
    return JsonResponse({'is_authenticated': request.session.get('is_authenticated', False), 'user': request.session.get('user', {})})


def cart_view(request):
    cart = request.session.get('cart', {})
    cart_count = request.session.get('cart_count', 0)
    return render(request, 'shop/cart.html', {'cart': cart, 'cart_count': cart_count})


@require_http_methods(["POST"])
def add_to_cart(request, product_id):
    cart = request.session.get('cart', {})
    item = cart.get(str(product_id), {'product_id': product_id, 'cantidad': 0})
    item['cantidad'] = item.get('cantidad', 0) + 1
    cart[str(product_id)] = item
    request.session['cart'] = cart
    request.session['cart_count'] = sum(i.get('cantidad', 0) for i in cart.values())
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or getattr(request, 'is_ajax', lambda: False)():
        return JsonResponse({'success': True, 'cart_count': request.session['cart_count']})
    return redirect('catalog')


def profile_view(request):
    if request.session.get('is_authenticated'):
        return redirect('dashboard')
    return redirect('login')


@require_http_methods(["POST"])
def create_venta(request):
    if not request.session.get('is_authenticated'):
        return Response({"error": "Usuario no autenticado"}, status=status.HTTP_401_UNAUTHORIZED)
    productos_validos = True
    error_message = ""
    for producto in request.data.get('productos', []):
        stock_response = requests.get(
            f"{settings.MICROSERVICES['INVENTARIO']['BASE_URL']}productos/{producto['id']}/stock/",
            headers={'X-API-Key': settings.MICROSERVICES['INVENTARIO']['API_KEY']}
        )
        if stock_response.status_code != 200:
            productos_validos = False
            error_message = f"Error al verificar stock del producto {producto['id']}"
            break
        stock_data = stock_response.json()
        if stock_data.get('stock', 0) < producto.get('cantidad', 0):
            productos_validos = False
            error_message = f"Stock insuficiente para el producto {producto['id']}"
            break
    if not productos_validos:
        return Response({"error": error_message}, status=status.HTTP_400_BAD_REQUEST)
    venta_response = requests.post(
        f"{settings.MICROSERVICES['VENTAS']['BASE_URL']}ventas/",
        json=request.data,
        headers={
            'X-API-Key': settings.MICROSERVICES['VENTAS']['API_KEY'],
            'Authorization': f"Token {request.session.get('user',{}).get('token','')}"
        }
    )
    if venta_response.status_code != 201:
        return Response(venta_response.json(), status=venta_response.status_code)
    venta_data = venta_response.json()
    for producto in request.data.get('productos', []):
        stock_update_response = requests.patch(
            f"{settings.MICROSERVICES['INVENTARIO']['BASE_URL']}productos/{producto['id']}/stock/",
            json={'cantidad': -producto['cantidad']},
            headers={'X-API-Key': settings.MICROSERVICES['INVENTARIO']['API_KEY']}
        )
        if stock_update_response.status_code != 200:
            logger.error(f"Error al actualizar stock del producto {producto['id']}")
    return Response(venta_data, status=status.HTTP_201_CREATED)


def get_ventas(request):
    if not request.session.get('is_authenticated'):
        return Response({"error": "Usuario no autenticado"}, status=status.HTTP_401_UNAUTHORIZED)
    ventas_response = requests.get(
        f"{settings.MICROSERVICES['VENTAS']['BASE_URL']}ventas/",
        headers={
            'X-API-Key': settings.MICROSERVICES['VENTAS']['API_KEY'],
            'Authorization': f"Token {request.session.get('user',{}).get('token','')}"
        }
    )
    if ventas_response.status_code != 200:
        return Response(ventas_response.json(), status=ventas_response.status_code)
    ventas_data = ventas_response.json()
    for venta in ventas_data:
        for producto in venta.get('productos', []):
            producto_response = requests.get(
                f"{settings.MICROSERVICES['INVENTARIO']['BASE_URL']}productos/{producto.get('producto_id')}/",
                headers={'X-API-Key': settings.MICROSERVICES['INVENTARIO']['API_KEY']}
            )
            if producto_response.status_code == 200:
                producto.update(producto_response.json())
    return Response({'ventas': ventas_data})


class ProductosAPIView(APIView):
    def get(self, request):
        try:
            response = requests.get(
                f"{settings.MICROSERVICES['INVENTARIO']['BASE_URL']}productos/",
                headers={'X-API-Key': settings.MICROSERVICES['INVENTARIO']['API_KEY']}
            )
            return Response(response.json(), status=response.status_code)
        except requests.RequestException as e:
            logger.error(f"Error al conectar con el servicio de inventario: {e}")
            return Response({"error": f"Error al conectar con el servicio de inventario: {e}"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    def post(self, request):
        try:
            response = requests.post(
                f"{settings.MICROSERVICES['INVENTARIO']['BASE_URL']}productos/",
                json=request.data,
                headers={'X-API-Key': settings.MICROSERVICES['INVENTARIO']['API_KEY']}
            )
            return Response(response.json(), status=response.status_code)
        except requests.RequestException as e:
            logger.error(f"Error al crear producto: {e}")
            return Response({"error": "Error al crear el producto"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class VentasAPIView(APIView):
    def get(self, request):
        try:
            response = requests.get(
                f"{settings.MICROSERVICES['VENTAS']['BASE_URL']}ventas/",
                headers={
                    'X-API-Key': settings.MICROSERVICES['VENTAS']['API_KEY'],
                    'Authorization': f"Token {request.session.get('user',{}).get('token','')}"
                }
            )
            return Response(response.json(), status=response.status_code)
        except requests.RequestException as e:
            logger.error(f"Error al conectar con el servicio de ventas: {e}")
            return Response({"error": f"Error al conectar con el servicio de ventas: {e}"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    def post(self, request):
        try:
            for producto in request.data.get('productos', []):
                stock_response = requests.get(
                    f"{settings.MICROSERVICES['INVENTARIO']['BASE_URL']}productos/{producto['id']}/stock/",
                    headers={'X-API-Key': settings.MICROSERVICES['INVENTARIO']['API_KEY']}
                )
                if stock_response.status_code != 200:
                    return Response({"error": "Error al validar stock"}, status=status.HTTP_400_BAD_REQUEST)
                stock_data = stock_response.json()
                if stock_data.get('stock', 0) < producto.get('cantidad', 0):
                    return Response({"error": f"Stock insuficiente para el producto {producto['id']}"}, status=status.HTTP_400_BAD_REQUEST)

            venta_response = requests.post(
                f"{settings.MICROSERVICES['VENTAS']['BASE_URL']}ventas/",
                json=request.data,
                headers={
                    'X-API-Key': settings.MICROSERVICES['VENTAS']['API_KEY'],
                    'Authorization': f"Token {request.session.get('user',{}).get('token','')}"
                }
            )

            if venta_response.status_code != 201:
                return Response(venta_response.json(), status=venta_response.status_code)

            venta_data = venta_response.json()
            for producto in request.data.get('productos', []):
                stock_update_response = requests.patch(
                    f"{settings.MICROSERVICES['INVENTARIO']['BASE_URL']}productos/{producto['id']}/stock/",
                    json={'cantidad': -producto['cantidad']},
                    headers={'X-API-Key': settings.MICROSERVICES['INVENTARIO']['API_KEY']}
                )
                if stock_update_response.status_code != 200:
                    logger.error(f"Error al actualizar stock del producto {producto['id']}")

            return Response(venta_data, status=status.HTTP_201_CREATED)
        except requests.RequestException as e:
            logger.error(f"Error al realizar la venta: {e}")
            return Response({"error": "Error al procesar la venta"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

            return Response(venta_data, status=status.HTTP_201_CREATED)

        except requests.RequestException as e:
            logger.error(f"Error al realizar la venta: {str(e)}")
            return Response(
                {"error": "Error al procesar la venta"}, 
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

            # Devolver la estructura esperada por los tests
            return Response({'ventas': ventas_data})

        except requests.exceptions.RequestException as e:
            logger.error(f"Error al comunicarse con los microservicios: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Error al obtener datos de los microservicios',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


