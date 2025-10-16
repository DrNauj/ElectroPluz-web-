from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.db import models
from django.db.models import Count, Sum, Avg, Q, F
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.text import slugify
from storefront.models import Product, Category, Order, Review, Claim, ClaimUpdate
from accounts.models import CustomUser
from .models import Branch, Inventory, FinancialTransaction, Budget
from .reports_views import reports
from .decorators import staff_required
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation as DecimalException
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.functions import Coalesce

ROLES = {
    'admin': ['view_all', 'edit_all'],
    'manager': ['view_all', 'edit_inventory', 'view_finances'],
    'sales': ['view_sales', 'edit_orders'],
    'inventory': ['view_inventory', 'edit_inventory'],
    'support': ['view_claims', 'edit_claims']
}

def is_staff(user):
    return user.is_staff

def has_role_permission(user, required_permission):
    if user.is_superuser:  # Los superusuarios tienen todos los permisos
        return True
    
    user_role = user.get_role_display().lower() if hasattr(user, 'get_role_display') else ''
    
    # Los administradores tienen acceso a todo
    if user_role == 'admin':
        return True
        
    return required_permission in ROLES.get(user_role, [])



# Vistas de Reclamos
@login_required
@staff_required
def claims_update_status(request, pk):
    if not has_role_permission(request.user, 'edit_all') and not has_role_permission(request.user, 'edit_claims'):
        raise PermissionDenied

    claim = get_object_or_404(Claim, pk=pk)
    if request.method == 'POST':
        data = request.POST
        claim.status = data['status']
        claim.save()

        # Crear actualización de reclamo
        ClaimUpdate.objects.create(
            claim=claim,
            user=request.user,
            status=claim.status,
            comment=data.get('comment', '')
        )
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)

@login_required
@staff_required
def dashboard_home(request):
    # Verificar que el usuario no sea cliente
    if request.user.role == 'CUSTOMER':
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Acceso denegado. Los clientes no pueden acceder al dashboard.")
    # Estadísticas generales
    total_orders = Order.objects.count()
    total_customers = CustomUser.objects.filter(is_staff=False).count()
    total_products = Product.objects.count()
    
    # Notificaciones de stock bajo
    try:
        low_stock_items = Inventory.objects.filter(
            quantity__lte=F('min_stock')
        ).select_related('product', 'branch')
    except:
        low_stock_items = []
    
    # Reclamos pendientes
    try:
        pending_claims = Claim.objects.filter(status='pending').count()
        in_process_claims = Claim.objects.filter(status='in_process').count()
    except:
        pending_claims = 0
        in_process_claims = 0
    
    # Ventas de los últimos 30 días
    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent_orders = Order.objects.filter(created_at__gte=thirty_days_ago)
    total_sales = recent_orders.aggregate(Sum('total'))['total__sum'] or 0
    
    # Balance financiero del mes actual
    current_month = datetime.now().replace(day=1)
    monthly_income = FinancialTransaction.objects.filter(
        type='income', 
        date__gte=current_month
    ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
    
    monthly_expenses = FinancialTransaction.objects.filter(
        type='expense', 
        date__gte=current_month
    ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
    
    # Productos más vendidos
    top_products = Product.objects.annotate(
        total_sales=Count('order_items')
    ).order_by('-total_sales')[:5]
    
    # Últimos pedidos
    latest_orders = Order.objects.order_by('-created_at')[:5]
    
    context = {
        'total_orders': total_orders,
        'total_customers': total_customers,
        'total_products': total_products,
        'total_sales': total_sales,
        'top_products': top_products,
        'latest_orders': latest_orders,
        'low_stock_items': low_stock_items,
        'pending_claims': pending_claims,
        'in_process_claims': in_process_claims,
        'monthly_income': monthly_income,
        'monthly_expenses': monthly_expenses,
        'monthly_balance': monthly_income - monthly_expenses,
        'can_view_finances': has_role_permission(request.user, 'view_finances'),
        'can_view_inventory': has_role_permission(request.user, 'view_inventory'),
        'can_view_claims': has_role_permission(request.user, 'view_claims')
    }
    return render(request, 'dashboard/home.html', context)

@login_required
@staff_required
def product_list(request):
    if not (request.user.is_superuser or 
            has_role_permission(request.user, 'view_all')):
        raise PermissionDenied

    # Parámetros de filtro y búsqueda
    category_id = request.GET.get('category')
    stock_status = request.GET.get('stock_status')
    search = request.GET.get('search', '').strip()
    sort_by = request.GET.get('sort', '-created_at')

    # Consulta base con optimización
    query = Q(is_active=True)
    if category_id:
        query &= Q(category_id=category_id)
    if stock_status == 'low':
        query &= Q(stock__lte=F('min_stock'))
    elif stock_status == 'out':
        query &= Q(stock=0)
    if search:
        query &= (
            Q(name__icontains=search) |
            Q(category__name__icontains=search)
        )

    # Validar y aplicar ordenamiento
    valid_sort_fields = {
        'name': 'name',
        '-name': '-name',
        'price': 'price',
        '-price': '-price',
        'stock': 'stock',
        '-stock': '-stock',
        'created_at': 'created_at',
        '-created_at': '-created_at',
    }
    sort_field = valid_sort_fields.get(sort_by, '-created_at')

    products = (Product.objects
        .select_related('category')
        .annotate(
            total_sales=Count('order_items'),
            total_revenue=Sum(F('order_items__quantity') * F('order_items__product_price'), default=0)
        )
        .filter(query)
        .order_by(sort_field))

    categories = Category.objects.all()

    return render(request, 'dashboard/products/list.html', {
        'products': products,
        'categories': categories,
        'selected_category': category_id,
        'stock_status': stock_status,
        'search': search,
        'sort_by': sort_by,
        'can_edit': has_role_permission(request.user, 'edit_all')
    })

@login_required
@staff_required
def product_create(request):
    if not (request.user.is_superuser or 
            has_role_permission(request.user, 'edit_all')):
        raise PermissionDenied

    if request.method == 'POST':
        try:
            data = request.POST.dict()
            
            # Validaciones básicas
            required_fields = ['name', 'category', 'price', 'stock', 'min_stock']
            if not all(data.get(field) for field in required_fields):
                return JsonResponse({
                    'success': False,
                    'error': 'Todos los campos marcados son requeridos'
                }, status=400)

            # Validar y convertir valores numéricos
            try:
                price = Decimal(data['price'])
                stock = int(data['stock'])
                min_stock = int(data['min_stock'])
                
                if price <= 0:
                    raise ValueError("El precio debe ser mayor que 0")
                if stock < 0:
                    raise ValueError("El stock no puede ser negativo")
                if min_stock < 0:
                    raise ValueError("El stock mínimo no puede ser negativo")
            except (ValueError, DecimalException) as e:
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=400)

            # Crear el producto
            product = Product.objects.create(
                name=data['name'],
                slug=slugify(data['name']),
                category_id=data['category'],
                description=data.get('description', ''),
                price=price,
                stock=stock,
                min_stock=min_stock,
                image=data.get('image', ''),
                is_active=True
            )

            return JsonResponse({
                'success': True,
                'id': product.id,
                'name': product.name,
                'url': reverse('dashboard:product_edit', args=[product.id])
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)

    categories = Category.objects.all()
    return render(request, 'dashboard/products/form.html', {
        'categories': categories
    })

@login_required
@staff_required
def product_edit(request, pk):
    if not (request.user.is_superuser or 
            has_role_permission(request.user, 'edit_all')):
        raise PermissionDenied

    product = get_object_or_404(Product, pk=pk)

    if request.method == 'POST':
        try:
            data = request.POST.dict()
            
            # Validaciones básicas
            required_fields = ['name', 'category', 'price']
            if not all(data.get(field) for field in required_fields):
                return JsonResponse({
                    'success': False,
                    'error': 'Nombre, categoría y precio son requeridos'
                }, status=400)

            # Validar y convertir valores numéricos
            try:
                price = Decimal(data['price'])
                stock = int(data.get('stock', product.stock))
                min_stock = int(data.get('min_stock', product.min_stock))
                
                if price <= 0:
                    raise ValueError("El precio debe ser mayor que 0")
                if stock < 0:
                    raise ValueError("El stock no puede ser negativo")
                if min_stock < 0:
                    raise ValueError("El stock mínimo no puede ser negativo")
            except (ValueError, DecimalException) as e:
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=400)

            # Actualizar el producto
            product.name = data['name']
            if product.name != data['name']:  # Solo actualizar slug si cambió el nombre
                product.slug = slugify(data['name'])
            product.category_id = data['category']
            product.description = data.get('description', '')
            product.price = price
            product.stock = stock
            product.min_stock = min_stock
            product.image = data.get('image', '')
            product.is_active = data.get('is_active', '1') == '1'
            product.save()

            return JsonResponse({
                'success': True,
                'name': product.name,
                'price': str(product.price),
                'stock': product.stock
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)

    categories = Category.objects.all()
    return render(request, 'dashboard/products/form.html', {
        'product': product,
        'categories': categories
    })

@login_required
@staff_required
def product_delete(request, pk):
    if not (request.user.is_superuser or 
            has_role_permission(request.user, 'edit_all')):
        raise PermissionDenied

    product = get_object_or_404(Product, pk=pk)

    if request.method == 'POST':
        try:
            # Verificar si hay órdenes pendientes
            pending_orders = product.order_items.filter(
                order__status__in=['pending', 'processing']
            ).exists()

            if pending_orders:
                return JsonResponse({
                    'success': False,
                    'error': 'No se puede eliminar un producto con órdenes pendientes'
                }, status=400)

            # Marcar como inactivo en lugar de eliminar
            product.is_active = False
            product.save()

            return JsonResponse({
                'success': True,
                'message': 'Producto desactivado correctamente'
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

    return JsonResponse({
        'success': False,
        'error': 'Método no permitido'
    }, status=405)

@login_required
@staff_required
def order_list(request):
    orders = Order.objects.all().order_by('-created_at')
    return render(request, 'dashboard/orders/list.html', {
        'orders': orders
    })

@login_required
@staff_required
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    return render(request, 'dashboard/orders/detail.html', {
        'order': order
    })

@login_required
@staff_required
def order_update_status(request, pk):
    if not has_role_permission(request.user, 'edit_orders'):
        raise PermissionDenied
        
    order = get_object_or_404(Order, pk=pk)
    
    if request.method == 'POST':
        status = request.POST.get('status')
        notes = request.POST.get('notes', '')
        
        if status not in dict(Order.STATUS_CHOICES):
            return JsonResponse({
                'success': False,
                'error': 'Estado no válido'
            }, status=400)
            
        try:
            old_status = order.status
            order.status = status
            order.notes = f"{order.notes}\n[{timezone.now().strftime('%Y-%m-%d %H:%M')} - {request.user.get_full_name()}] "
            order.notes += f"Cambio de estado: {old_status} → {status}\n"
            if notes:
                order.notes += f"Notas: {notes}\n"
            order.save()
            
            return JsonResponse({
                'success': True,
                'status': status,
                'updated_at': order.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
            
    return JsonResponse({'success': False}, status=405)  # Método no permitido

@login_required
@staff_required
def customer_list(request):
    customers = CustomUser.objects.filter(is_staff=False).order_by('-date_joined')
    return render(request, 'dashboard/customers/list.html', {
        'customers': customers
    })

@login_required
@staff_required
def customer_detail(request, pk):
    customer = get_object_or_404(CustomUser, pk=pk)
    orders = Order.objects.filter(user=customer).order_by('-created_at')
    return render(request, 'dashboard/customers/detail.html', {
        'customer': customer,
        'orders': orders
    })

@login_required
@staff_required
def staff_create(request):
    if not has_role_permission(request.user, 'edit_all'):
        raise PermissionDenied
        
    if request.method == 'POST':
        try:
            # Validaciones básicas
            data = request.POST.dict()
            required_fields = ['email', 'password', 'role', 'first_name', 'last_name']
            if not all(data.get(field) for field in required_fields):
                return JsonResponse({
                    'success': False,
                    'error': 'Todos los campos marcados son requeridos'
                }, status=400)
            
            # Validar email único
            email = data['email'].strip()
            if CustomUser.objects.filter(email__iexact=email).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Ya existe un usuario con este email'
                }, status=400)
            
            # Validar rol
            role = data['role']
            if role not in [choice[0] for choice in CustomUser.ROLE_CHOICES if choice[0] != 'customer']:
                return JsonResponse({
                    'success': False,
                    'error': 'Rol no válido'
                }, status=400)

            # Crear usuario
            user = CustomUser.objects.create_user(
                email=email,
                password=data['password'],
                first_name=data['first_name'].strip(),
                last_name=data['last_name'].strip(),
                is_staff=True,
                role=role
            )

            return JsonResponse({
                'success': True,
                'id': user.id,
                'email': user.email,
                'name': user.get_full_name()
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
            
    roles = [choice[0] for choice in CustomUser.ROLE_CHOICES if choice[0] != 'customer']
    return render(request, 'dashboard/users/form.html', {'roles': roles})

@login_required
@staff_required
def staff_edit(request, pk):
    if not has_role_permission(request.user, 'edit_all'):
        raise PermissionDenied
        
    user = get_object_or_404(CustomUser, pk=pk, is_staff=True)
    
    if request.method == 'POST':
        try:
            data = request.POST.dict()
            
            # Validaciones básicas
            required_fields = ['email', 'role', 'first_name', 'last_name']
            if not all(data.get(field) for field in required_fields):
                return JsonResponse({
                    'success': False,
                    'error': 'Email, rol y nombre son requeridos'
                }, status=400)
            
            # Validar email único
            email = data['email'].strip()
            if CustomUser.objects.filter(email__iexact=email).exclude(pk=pk).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Ya existe un usuario con este email'
                }, status=400)
            
            # Validar rol
            role = data['role']
            if role not in [choice[0] for choice in CustomUser.ROLE_CHOICES if choice[0] != 'customer']:
                return JsonResponse({
                    'success': False,
                    'error': 'Rol no válido'
                }, status=400)

            # Actualizar usuario
            user.email = email
            user.first_name = data['first_name'].strip()
            user.last_name = data['last_name'].strip()
            user.role = role

            # Actualizar contraseña si se proporcionó una nueva
            password = data.get('password', '').strip()
            if password:
                user.set_password(password)

            user.save()
            
            return JsonResponse({
                'success': True,
                'email': user.email,
                'name': user.get_full_name(),
                'role': user.get_role_display()
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
            
    roles = [choice[0] for choice in CustomUser.ROLE_CHOICES if choice[0] != 'customer']
    return render(request, 'dashboard/users/form.html', {
        'user': user,
        'roles': roles
    })

# Gestión de Inventario
@login_required
@staff_required
def inventory_list(request):
    if not (request.user.is_superuser or 
            has_role_permission(request.user, 'view_inventory') or 
            has_role_permission(request.user, 'view_all')):
        raise PermissionDenied
            
    # Obtener parámetros de filtro
    branch_id = request.GET.get('branch')
    stock_status = request.GET.get('stock_status')
    search = request.GET.get('search', '').strip()
    
    # Consulta base
    query = Q()
    if branch_id:
        query &= Q(branch_id=branch_id)
    if stock_status == 'low':
        query &= Q(quantity__lte=F('min_stock'))
    elif stock_status == 'normal':
        query &= Q(quantity__gt=F('min_stock'))
    if search:
        query &= (
            Q(product__name__icontains=search) | 
            Q(branch__name__icontains=search)
        )
    
    inventory_items = (Inventory.objects
        .select_related('product', 'branch')
        .filter(query)
        .order_by('branch__name', 'product__name'))
    
    branches = Branch.objects.all()
    products = Product.objects.filter(is_active=True)
    
    return render(request, 'dashboard/inventory/list.html', {
        'inventory_items': inventory_items,
        'branches': branches,
        'products': products,
        'selected_branch': branch_id,
        'stock_status': stock_status,
        'search': search,
        'can_edit': has_role_permission(request.user, 'edit_inventory')
    })

@login_required
@staff_required
def inventory_create(request):
    if not (request.user.is_superuser or 
            has_role_permission(request.user, 'edit_inventory')):
        raise PermissionDenied
        
    if request.method == 'POST':
        product_id = request.POST.get('product')
        branch_id = request.POST.get('branch')
        quantity = request.POST.get('quantity', 0)
        min_stock = request.POST.get('min_stock', 0)
        
        try:
            quantity = int(quantity)
            min_stock = int(min_stock)
            
            if quantity < 0 or min_stock < 0:
                raise ValueError("Las cantidades no pueden ser negativas")
                
            inventory = Inventory.objects.create(
                product_id=product_id,
                branch_id=branch_id,
                quantity=quantity,
                min_stock=min_stock
            )
            
            return JsonResponse({
                'success': True,
                'id': inventory.id,
                'product_name': inventory.product.name,
                'branch_name': inventory.branch.name
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
            
    branches = Branch.objects.all()
    products = Product.objects.filter(is_active=True)
    return render(request, 'dashboard/inventory/form.html', {
        'branches': branches,
        'products': products
    })

@login_required
@staff_required
def inventory_detail(request, pk):
    if not (request.user.is_superuser or 
            has_role_permission(request.user, 'view_inventory') or 
            has_role_permission(request.user, 'view_all')):
        raise PermissionDenied
        
    inventory = get_object_or_404(
        Inventory.objects.select_related('product', 'branch'),
        pk=pk
    )
    
    return JsonResponse({
        'id': inventory.id,
        'product': {
            'id': inventory.product.id,
            'name': inventory.product.name,
            'price': str(inventory.product.price)
        },
        'branch': {
            'id': inventory.branch.id,
            'name': inventory.branch.name
        },
        'quantity': inventory.quantity,
        'min_stock': inventory.min_stock,
        'last_updated': inventory.last_updated.strftime('%Y-%m-%d %H:%M:%S')
    })

@login_required
@staff_required
def inventory_edit(request, pk):
    if not (request.user.is_superuser or 
            has_role_permission(request.user, 'edit_inventory')):
        raise PermissionDenied
        
    inventory = get_object_or_404(Inventory, pk=pk)
    
    if request.method == 'POST':
        try:
            quantity = int(request.POST.get('quantity', 0))
            min_stock = int(request.POST.get('min_stock', 0))
            
            if quantity < 0 or min_stock < 0:
                raise ValueError("Las cantidades no pueden ser negativas")
            
            inventory.quantity = quantity
            inventory.min_stock = min_stock
            inventory.save()
            
            return JsonResponse({
                'success': True,
                'quantity': inventory.quantity,
                'min_stock': inventory.min_stock,
                'last_updated': inventory.last_updated.strftime('%Y-%m-%d %H:%M:%S')
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
            
    return render(request, 'dashboard/inventory/form.html', {
        'inventory': inventory,
        'branches': Branch.objects.all(),
        'products': Product.objects.filter(is_active=True)
    })

@login_required
@staff_required
def inventory_update(request):
    if not (request.user.is_superuser or
            has_role_permission(request.user, 'edit_inventory')):
        raise PermissionDenied

    if request.method == 'POST':
        inventory_id = request.POST.get('inventory_id')
        quantity = request.POST.get('quantity')
        min_stock = request.POST.get('min_stock')

        inventory = get_object_or_404(Inventory, pk=inventory_id)
        inventory.quantity = quantity
        inventory.min_stock = min_stock
        inventory.save()

        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

# Gestión de Personal
@login_required
@staff_required
def staff_list(request):
    if not (request.user.is_superuser or 
            has_role_permission(request.user, 'view_all')):
        raise PermissionDenied
        
    # Parámetros de búsqueda y filtrado
    search = request.GET.get('search', '').strip()
    role = request.GET.get('role', '')
    sort_by = request.GET.get('sort', 'email')

    # Consulta base con optimización
    query = Q(is_staff=True)
    if search:
        query &= (
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    if role:
        query &= Q(role=role)

    # Validar y aplicar ordenamiento
    valid_sort_fields = {
        'email': 'email',
        '-email': '-email',
        'name': 'first_name',
        '-name': '-first_name',
        'role': 'role',
        '-role': '-role',
        'date': 'date_joined',
        '-date': '-date_joined',
    }
    sort_field = valid_sort_fields.get(sort_by, 'email')

    staff_users = (CustomUser.objects
        .filter(query)
        .order_by(sort_field))

    # Obtener roles disponibles para el filtro
    roles = [choice[0] for choice in CustomUser.ROLE_CHOICES if choice[0] != 'customer']

    return render(request, 'dashboard/users/list.html', {
        'users': staff_users,
        'roles': roles,
        'selected_role': role,
        'search': search,
        'sort_by': sort_by,
        'can_edit': has_role_permission(request.user, 'edit_all')
    })

# Gestión de Reclamos
@login_required
@staff_required
def claims_list(request):
    if not has_role_permission(request.user, 'view_claims'):
        raise PermissionDenied
        
    status = request.GET.get('status', 'all')
    claims = Claim.objects.select_related('order', 'user').all()
    
    if status != 'all':
        claims = claims.filter(status=status)
    
    return render(request, 'dashboard/claims/list.html', {
        'claims': claims,
        'can_edit': has_role_permission(request.user, 'edit_claims')
    })

@login_required
@staff_required
def claim_detail(request, pk):
    if not has_role_permission(request.user, 'view_claims'):
        raise PermissionDenied
        
    claim = get_object_or_404(Claim, pk=pk)
    return render(request, 'dashboard/claims/detail.html', {
        'claim': claim,
        'can_edit': has_role_permission(request.user, 'edit_claims')
    })

@login_required
@staff_required
def claims_update_status(request, pk):
    if not has_role_permission(request.user, 'edit_claims'):
        raise PermissionDenied
        
    claim = get_object_or_404(Claim, pk=pk)
    if request.method == 'POST':
        status = request.POST.get('status')
        comment = request.POST.get('comment', '')
        
        if status and status in dict(Claim.STATUS_CHOICES):
            claim.status = status
            claim.save()
            
            # Crear registro de actualización
            ClaimUpdate.objects.create(
                claim=claim,
                user=request.user,
                status=status,
                comment=comment
            )
            
            return JsonResponse({
                'success': True,
                'status': status,
                'updated_at': claim.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            })
    return JsonResponse({'success': False, 'error': 'Estado inválido'}, status=400)

# Gestión Financiera
@login_required
@staff_required
def finances(request):
    if not has_role_permission(request.user, 'view_finances'):
        raise PermissionDenied
    
    # Transacciones del mes actual
    current_month = datetime.now().replace(day=1)
    transactions = FinancialTransaction.objects.filter(date__gte=current_month)
    
    # Resumen financiero
    summary = transactions.aggregate(
        total_income=Sum('amount', filter=Q(type='income')),
        total_expenses=Sum('amount', filter=Q(type='expense')),
        total_investments=Sum('amount', filter=Q(type='investment'))
    )
    
    # Presupuesto actual
    current_budget = Budget.objects.filter(
        start_date__lte=datetime.now(),
        end_date__gte=datetime.now()
    ).first()
    
    return render(request, 'dashboard/finances/overview.html', {
        'transactions': transactions,
        'summary': summary,
        'budget': current_budget
    })

@login_required
@staff_required
def budget_manage(request):
    if not has_role_permission(request.user, 'edit_all'):
        raise PermissionDenied
    
    if request.method == 'POST':
        # Lógica para crear/actualizar presupuesto
        return JsonResponse({'success': True})
    
    budgets = Budget.objects.all().order_by('-start_date')
    return render(request, 'dashboard/finances/budget.html', {
        'budgets': budgets
    })

@login_required
@staff_required
def transaction_add(request):
    if not has_role_permission(request.user, 'edit_all'):
        raise PermissionDenied
    
    if request.method == 'POST':
        # Lógica para agregar transacción
        return JsonResponse({'success': True})
    
    return render(request, 'dashboard/finances/transaction_form.html')

@login_required
@staff_required
def category_list(request):
    if not (request.user.is_superuser or 
            has_role_permission(request.user, 'view_all')):
        raise PermissionDenied

    categories = (Category.objects
        .annotate(product_count=Count('products', filter=Q(products__is_active=True)))
        .order_by('name'))

    return render(request, 'dashboard/categories/list.html', {
        'categories': categories,
        'can_edit': has_role_permission(request.user, 'edit_all')
    })

@login_required
@staff_required
def category_create(request):
    if not (request.user.is_superuser or 
            has_role_permission(request.user, 'edit_all')):
        raise PermissionDenied

    if request.method == 'POST':
        try:
            name = request.POST.get('name', '').strip()
            description = request.POST.get('description', '').strip()

            if not name:
                return JsonResponse({
                    'success': False,
                    'error': 'El nombre de la categoría es requerido'
                }, status=400)

            # Verificar nombre único
            if Category.objects.filter(name__iexact=name).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Ya existe una categoría con este nombre'
                }, status=400)

            category = Category.objects.create(
                name=name,
                description=description,
                slug=slugify(name)
            )

            return JsonResponse({
                'success': True,
                'id': category.id,
                'name': category.name
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)

    return render(request, 'dashboard/categories/form.html')

@login_required
@staff_required
def category_edit(request, pk):
    if not (request.user.is_superuser or 
            has_role_permission(request.user, 'edit_all')):
        raise PermissionDenied

    category = get_object_or_404(Category, pk=pk)

    if request.method == 'POST':
        try:
            name = request.POST.get('name', '').strip()
            description = request.POST.get('description', '').strip()

            if not name:
                return JsonResponse({
                    'success': False,
                    'error': 'El nombre de la categoría es requerido'
                }, status=400)

            # Verificar nombre único excluyendo la categoría actual
            if Category.objects.filter(name__iexact=name).exclude(pk=pk).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Ya existe una categoría con este nombre'
                }, status=400)

            category.name = name
            category.description = description
            if category.name != name:  # Solo actualizar slug si cambió el nombre
                category.slug = slugify(name)
            category.save()

            return JsonResponse({
                'success': True,
                'name': category.name
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)

    return render(request, 'dashboard/categories/form.html', {
        'category': category
    })

@login_required
@staff_required
def category_delete(request, pk):
    if not (request.user.is_superuser or 
            has_role_permission(request.user, 'edit_all')):
        raise PermissionDenied

    category = get_object_or_404(Category, pk=pk)

    if request.method == 'POST':
        try:
            # Verificar que no haya productos activos
            if category.products.filter(is_active=True).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'No se puede eliminar una categoría con productos activos'
                }, status=400)

            category.delete()
            return JsonResponse({
                'success': True,
                'message': 'Categoría eliminada correctamente'
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

    return JsonResponse({
        'success': False,
        'error': 'Método no permitido'
    }, status=405)