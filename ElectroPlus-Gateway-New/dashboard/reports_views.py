from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q, F, Count, Sum, Avg
from django.db import models
from django.db.models.functions import TruncDate, TruncMonth, TruncWeek
from django.utils import timezone
from datetime import timedelta
import json
from storefront.models import Category, Product, Order, Claim, OrderItem
from .decorators import staff_required

def get_date_range(period):
    today = timezone.now()
    if period == 'today':
        return today.replace(hour=0, minute=0, second=0)
    elif period == 'week':
        return today - timedelta(days=7)
    elif period == 'month':
        return today - timedelta(days=30)
    elif period == 'year':
        return today - timedelta(days=365)
    return today - timedelta(days=30)  # Por defecto, último mes

@login_required
@staff_required
def reports(request):
    # Obtener período
    period = request.GET.get('period', 'month')
    date_from = get_date_range(period)
    
    # Obtener órdenes del período
    orders = Order.objects.filter(created_at__gte=date_from)
    
    # Datos de ventas por fecha
    sales_by_date = orders.annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        total_sales=Count('id'),
        total_amount=Sum(F('items__quantity') * F('items__product__price')),
        total_items=Sum('items__quantity')
    ).order_by('date')

    # Productos más vendidos
    top_products = Product.objects.filter(
        order_items__order__created_at__gte=date_from
    ).annotate(
        total_sales=Count('order_items'),
        total_revenue=Sum(F('order_items__quantity') * F('price'))
    ).order_by('-total_sales')[:10]

    # Estadísticas del período
    period_stats = orders.aggregate(
        total_orders=Count('id'),
        total_revenue=Sum(
            F('items__quantity') * F('items__product__price'),
            output_field=models.DecimalField(max_digits=10, decimal_places=2),
            default=0
        ),
        total_items=Sum('items__quantity'),
        avg_order_value=Avg(
            F('items__quantity') * F('items__product__price'),
            output_field=models.DecimalField(max_digits=10, decimal_places=2),
            default=0
        ),
        total_tax=Sum('tax', default=0),
        total_discount=Sum('discount', default=0)
    )

    # Top categorías
    top_categories = Category.objects.filter(
        product__order_items__order__created_at__gte=date_from
    ).annotate(
        total_sales=Count('product__order_items'),
        total_revenue=Sum(F('product__order_items__quantity') * F('product__price'))
    ).order_by('-total_sales')[:5]

    # Estado de reclamos
    claims_stats = Claim.objects.filter(
        created_at__gte=date_from
    ).values('status').annotate(
        total=Count('id')
    )

    # Datos para gráficos
    chart_data = {
        'sales': {
            'labels': [entry['date'].strftime('%d/%m/%Y') for entry in sales_by_date],
            'sales': [entry['total_sales'] for entry in sales_by_date],
            'revenue': [float(entry['total_amount'] or 0) for entry in sales_by_date],
            'items': [entry['total_items'] or 0 for entry in sales_by_date],
        },
        'products': {
            'labels': [p.name for p in top_products],
            'sales': [p.total_sales for p in top_products],
            'revenue': [float(p.total_revenue or 0) for p in top_products],
        },
        'categories': {
            'labels': [c.name for c in top_categories],
            'sales': [c.total_sales for c in top_categories],
            'revenue': [float(c.total_revenue or 0) for c in top_categories],
        },
        'claims': {
            'labels': [c['status'] for c in claims_stats],
            'values': [c['total'] for c in claims_stats],
        },
    }

    # Indicadores de bajo stock
    low_stock_products = Product.objects.filter(
        stock__lt=F('min_stock')
    ).order_by('stock')[:10]

    context = {
        'period': period,
        'period_stats': period_stats,
        'chart_data': json.dumps(chart_data),
        'top_products': top_products,
        'top_categories': top_categories,
        'low_stock_products': low_stock_products,
        'claims_stats': claims_stats,
    }

    return render(request, 'dashboard/reports/index.html', context)