from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import reverse
from django.conf import settings
from gateway_app.models import Product, Order, OrderItem
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import requests
import json
import logging

logger = logging.getLogger(__name__)

class VentasAPIView(APIView):
    def get(self, request):
        try:
            response = requests.get(
                f"{settings.MICROSERVICES['VENTAS']['BASE_URL']}ventas/",
                headers={
                    'X-API-Key': settings.MICROSERVICES['VENTAS']['API_KEY'],
                    'Authorization': f"Token {request.session.get('user',{}).get('token','')}"
                },
                timeout=5,
            )
            return Response(response.json(), status=response.status_code)
        except requests.RequestException as e:
            logger.error(f"Error al conectar con el servicio de ventas: {e}")
            return Response(
                {"error": f"Error al conectar con el servicio de ventas: {e}"}, 
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

    def post(self, request):
        try:
            # Validar stock primero
            for producto in request.data.get('productos', []):
                stock_response = requests.get(
                    f"{settings.MICROSERVICES['INVENTARIO']['BASE_URL']}productos/{producto['id']}/stock/",
                    headers={'X-API-Key': settings.MICROSERVICES['INVENTARIO']['API_KEY']},
                    timeout=5,
                )
                if stock_response.status_code != 200:
                    return Response(
                        {"error": "Error al validar stock"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                stock_data = stock_response.json()
                if stock_data.get('stock', 0) < producto.get('cantidad', 0):
                    return Response(
                        {"error": f"Stock insuficiente para el producto {producto['id']}"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Crear venta
            venta_response = requests.post(
                f"{settings.MICROSERVICES['VENTAS']['BASE_URL']}ventas/",
                json=request.data,
                headers={
                    'X-API-Key': settings.MICROSERVICES['VENTAS']['API_KEY'],
                    'Authorization': f"Token {request.session.get('user',{}).get('token','')}"
                },
                timeout=5,
            )

            if venta_response.status_code != 201:
                return Response(venta_response.json(), status=venta_response.status_code)

            venta_data = venta_response.json()
            
            # Actualizar stock
            for producto in request.data.get('productos', []):
                stock_update_response = requests.patch(
                    f"{settings.MICROSERVICES['INVENTARIO']['BASE_URL']}productos/{producto['id']}/stock/",
                    json={'cantidad': -producto['cantidad']},
                    headers={'X-API-Key': settings.MICROSERVICES['INVENTARIO']['API_KEY']},
                    timeout=5,
                )
                if stock_update_response.status_code != 200:
                    logger.error(f"Error al actualizar stock del producto {producto['id']}")

            return Response(venta_data, status=status.HTTP_201_CREATED)
            
        except requests.RequestException as e:
            logger.error(f"Error al realizar la venta: {e}")
            return Response(
                {"error": "Error al procesar la venta"}, 
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

def shop_home(request):
    """Vista principal de la tienda"""
    return render(request, 'sales/shop_home.html')

@login_required
def cart_view(request):
    """Vista del carrito de compras"""
    # Obtener el carrito de la sesión o crear uno nuevo
    cart_items = request.session.get('cart', {})
    context = {'cart_items': []}
    total = 0
    
    # Si hay items en el carrito, obtener los productos
    if cart_items:
        for item_id, item_data in cart_items.items():
            product = get_object_or_404(Product, id=item_id)
            subtotal = product.price * item_data['quantity']
            total += subtotal
            context['cart_items'].append({
                'id': item_id,
                'product': product,
                'quantity': item_data['quantity'],
                'subtotal': subtotal
            })
    
    context['cart_total'] = total
    return render(request, 'sales/cart.html', context)

@login_required
def checkout(request):
    """Vista del proceso de checkout"""
    # Obtener items del carrito
    cart_items = request.session.get('cart', {})
    if not cart_items:
        return redirect('sales:cart')
        
    # Calcular totales
    subtotal = 0
    for item_id, item_data in cart_items.items():
        product = get_object_or_404(Product, id=item_id)
        subtotal += product.price * item_data['quantity']
    
    shipping_cost = 100  # Coste fijo de envío
    tax = subtotal * 0.16  # IVA 16%
    total = subtotal + shipping_cost + tax
    
    context = {
        'cart_items': [],
        'subtotal': subtotal,
        'shipping_cost': shipping_cost,
        'tax': tax,
        'total': total
    }
    
    for item_id, item_data in cart_items.items():
        product = get_object_or_404(Product, id=item_id)
        context['cart_items'].append({
            'product': product,
            'quantity': item_data['quantity'],
            'total_price': product.price * item_data['quantity']
        })
    
    return render(request, 'sales/checkout.html', context)

@login_required
def order_confirmation(request, order_number):
    """Vista de confirmación de pedido"""
    order = get_object_or_404(Order, number=order_number)
    return render(request, 'sales/order_confirmation.html', {'order': order})

@login_required
def cart_add(request):
    """Añadir un producto al carrito"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')
            quantity = data.get('quantity', 1)
            
            # Validar que el producto existe y hay stock suficiente
            product = get_object_or_404(Product, id=product_id, active=True)
            if product.stock < quantity:
                return JsonResponse({
                    'success': False,
                    'error': 'No hay suficiente stock disponible'
                })
            
            # Obtener o inicializar el carrito
            cart = request.session.get('cart', {})
            
            # Añadir o actualizar el producto en el carrito
            if str(product_id) in cart:
                cart[str(product_id)]['quantity'] += quantity
            else:
                cart[str(product_id)] = {'quantity': quantity}
            
            request.session['cart'] = cart
            request.session.modified = True
            
            return JsonResponse({'success': True})
            
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'})
            
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def cart_update(request, item_id):
    """Actualizar la cantidad de un producto en el carrito"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            quantity = data.get('quantity')
            
            if quantity < 1:
                return JsonResponse({
                    'success': False,
                    'error': 'La cantidad debe ser mayor a 0'
                })
            
            # Validar que el producto existe y hay stock suficiente
            product = get_object_or_404(Product, id=item_id, active=True)
            if product.stock < quantity:
                return JsonResponse({
                    'success': False,
                    'error': 'No hay suficiente stock disponible'
                })
            
            # Actualizar la cantidad en el carrito
            cart = request.session.get('cart', {})
            if str(item_id) in cart:
                cart[str(item_id)]['quantity'] = quantity
                request.session['cart'] = cart
                request.session.modified = True
                return JsonResponse({'success': True})
            
            return JsonResponse({
                'success': False,
                'error': 'Producto no encontrado en el carrito'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'})
            
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def cart_remove(request, item_id):
    """Eliminar un producto del carrito"""
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        if str(item_id) in cart:
            del cart[str(item_id)]
            request.session['cart'] = cart
            request.session.modified = True
            return JsonResponse({'success': True})
        
        return JsonResponse({
            'success': False,
            'error': 'Producto no encontrado en el carrito'
        })
            
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def process_order(request):
    """Procesar una orden de compra"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            cart = request.session.get('cart', {})
            
            if not cart:
                return JsonResponse({
                    'success': False,
                    'error': 'El carrito está vacío'
                })
            
            # Crear la orden
            order = Order.objects.create(
                number=f'ORD-{Order.objects.count() + 1:06d}',
                shipping_name=f"{data['shipping']['firstName']} {data['shipping']['lastName']}",
                shipping_address=data['shipping']['address'],
                shipping_city=data['shipping']['city'],
                shipping_state=data['shipping']['state'],
                shipping_zip=data['shipping']['zip'],
                shipping_country=data['shipping']['country'],
                email=data['shipping']['email'],
                payment_method=data['payment']['method'],
                subtotal=0,
                shipping_cost=100,  # Coste fijo de envío
                tax=0,
                total=0
            )
            
            subtotal = 0
            for item_id, item_data in cart.items():
                product = get_object_or_404(Product, id=item_id)
                quantity = item_data['quantity']
                
                # Validar stock nuevamente
                if product.stock < quantity:
                    order.delete()
                    return JsonResponse({
                        'success': False,
                        'error': f'No hay suficiente stock de {product.name}'
                    })
                
                # Crear el item de la orden
                item_total = product.price * quantity
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    unit_price=product.price,
                    total_price=item_total
                )
                
                # Actualizar el stock
                product.stock -= quantity
                product.save()
                
                subtotal += item_total
            
            # Actualizar totales de la orden
            order.subtotal = subtotal
            order.tax = subtotal * 0.16  # IVA 16%
            order.total = order.subtotal + order.shipping_cost + order.tax
            order.save()
            
            # Limpiar el carrito
            request.session['cart'] = {}
            request.session.modified = True
            
            return JsonResponse({
                'success': True,
                'redirect_url': reverse('sales:order_confirmation', args=[order.number])
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
            
    return JsonResponse({'success': False, 'error': 'Invalid request method'})