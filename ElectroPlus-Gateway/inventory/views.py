from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
from django.db.models import Sum, F
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from gateway_app.models import Product, Category, Order
import requests
import json
import logging
import csv
import io

logger = logging.getLogger(__name__)

def is_staff_user(user):
    return user.is_staff

@login_required
@user_passes_test(is_staff_user)
def dashboard_home(request):
    """Vista del panel de control"""
    total_products = Product.objects.count()
    low_stock_products = Product.objects.filter(stock__lte=F('min_stock')).count()
    total_categories = Category.objects.count()
    
    # Obtener ventas del día y mes actuales
    today = timezone.now().date()
    month_start = today.replace(day=1)
    daily_sales = Order.objects.filter(
        created_at__date=today
    ).aggregate(total=Sum('total'))['total'] or 0
    monthly_sales = Order.objects.filter(
        created_at__date__gte=month_start
    ).aggregate(total=Sum('total'))['total'] or 0
    
    # Obtener órdenes pendientes
    pending_orders = Order.objects.filter(status='pending').count()
    
    context = {
        'total_products': total_products,
        'low_stock_products': low_stock_products,
        'total_categories': total_categories,
        'daily_sales': daily_sales,
        'monthly_sales': monthly_sales,
        'pending_orders': pending_orders,
    }
    
    return render(request, 'inventory/dashboard/admin_dashboard.html', context)

@login_required
@user_passes_test(is_staff_user)
def product_management(request):
    """Vista de gestión de productos"""
    products = Product.objects.select_related('category').all()
    categories = Category.objects.all()
    
    # Paginación
    page = request.GET.get('page', 1)
    paginator = Paginator(products, 20)
    
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)
    
    context = {
        'products': products,
        'categories': categories,
    }
    return render(request, 'inventory/product_management.html', context)

@login_required
@user_passes_test(is_staff_user)
def order_list(request):
    """Vista de listado de órdenes"""
    orders = Order.objects.select_related('customer').all().order_by('-created_at')
    return render(request, 'inventory/orders_list.html', {'orders': orders})

@login_required
@user_passes_test(is_staff_user)
def product_list_create(request):
    """API endpoint para listar y crear productos"""
    if request.method == 'GET':
        products = Product.objects.select_related('category').all()
        data = []
        for product in products:
            data.append({
                'id': product.id,
                'name': product.name,
                'sku': product.sku,
                'category': {
                    'id': product.category.id,
                    'name': product.category.name
                },
                'price': str(product.price),
                'stock': product.stock,
                'min_stock': product.min_stock,
                'active': product.active,
                'image_url': product.image.url if product.image else None
            })
        return JsonResponse(data, safe=False)
        
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            category = get_object_or_404(Category, id=data['category'])
            
            product = Product.objects.create(
                name=data['name'],
                sku=data['sku'],
                category=category,
                price=data['price'],
                stock=data['stock'],
                min_stock=data.get('min_stock', 5),
                description=data.get('description', ''),
                active=data.get('active', True)
            )
            
            return JsonResponse({
                'id': product.id,
                'name': product.name,
                'sku': product.sku
            }, status=201)
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

@login_required
@user_passes_test(is_staff_user)
def product_detail(request, pk):
    """API endpoint para ver, actualizar o eliminar un producto"""
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'GET':
        data = {
            'id': product.id,
            'name': product.name,
            'sku': product.sku,
            'category': {
                'id': product.category.id,
                'name': product.category.name
            },
            'price': str(product.price),
            'stock': product.stock,
            'min_stock': product.min_stock,
            'description': product.description,
            'active': product.active,
            'image_url': product.image.url if product.image else None
        }
        return JsonResponse(data)
        
    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            
            if 'category' in data:
                category = get_object_or_404(Category, id=data['category'])
                product.category = category
            
            if 'name' in data:
                product.name = data['name']
            if 'sku' in data:
                product.sku = data['sku']
            if 'price' in data:
                product.price = data['price']
            if 'stock' in data:
                product.stock = data['stock']
            if 'min_stock' in data:
                product.min_stock = data['min_stock']
            if 'description' in data:
                product.description = data['description']
            if 'active' in data:
                product.active = data['active']
            
            product.save()
            return JsonResponse({'status': 'success'})
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
            
    elif request.method == 'DELETE':
        product.delete()
        return JsonResponse({'status': 'success'})

@login_required
@user_passes_test(is_staff_user)
def product_import(request):
    """API endpoint para importar productos desde CSV"""
    if request.method == 'POST' and request.FILES.get('file'):
        csv_file = request.FILES['file']
        decoded_file = csv_file.read().decode('utf-8')
        io_string = io.StringIO(decoded_file)
        reader = csv.DictReader(io_string)
        
        products_created = 0
        errors = []
        
        for row in reader:
            try:
                category = Category.objects.get(name=row['category'])
                Product.objects.create(
                    name=row['name'],
                    sku=row['sku'],
                    category=category,
                    price=float(row['price']),
                    stock=int(row['stock']),
                    min_stock=int(row.get('min_stock', 5)),
                    description=row.get('description', ''),
                    active=row.get('active', 'true').lower() == 'true'
                )
                products_created += 1
            except Exception as e:
                errors.append(f"Error en la línea {reader.line_num}: {str(e)}")
        
        return JsonResponse({
            'success': True,
            'products_created': products_created,
            'errors': errors
        })
        
    return JsonResponse({
        'success': False,
        'error': 'No file uploaded or invalid request method'
    }, status=400)

    def post(self, request):
        try:
            response = requests.post(
                f"{settings.MICROSERVICES['INVENTARIO']['BASE_URL']}productos/",
                json=request.data,
                headers={'X-API-Key': settings.MICROSERVICES['INVENTARIO']['API_KEY']},
                timeout=5,
            )
            return Response(response.json(), status=response.status_code)
        except requests.RequestException as e:
            logger.error(f"Error al crear producto: {e}")
            return Response(
                {"error": "Error al crear el producto"}, 
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

@login_required
@user_passes_test(is_staff_user)
def dashboard_home(request):
    """Vista principal del dashboard"""
    return render(request, 'inventory/dashboard/admin_dashboard.html')

@login_required
@user_passes_test(is_staff_user)
def product_management(request):
    """Gestión de productos"""
    return render(request, 'inventory/dashboard/product_management.html')

@login_required
@user_passes_test(is_staff_user)
def order_list(request):
    """Lista de órdenes"""
    return render(request, 'inventory/dashboard/order_list.html')