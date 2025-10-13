"""
Servicio para gestionar la comunicación con el microservicio de inventario
incluyendo caché para mejorar el rendimiento.
"""
from django.core.cache import cache
from django.conf import settings
import requests
import logging
import json

logger = logging.getLogger(__name__)

CACHE_TIMEOUT = 300  # 5 minutos
CACHE_PREFIX = 'products_'

def get_products(category=None, search=None, force_refresh=False):
    """
    Obtiene productos del microservicio de inventario con caché.
    
    Args:
        category: ID de categoría para filtrar (opcional)
        search: Término de búsqueda (opcional)
        force_refresh: Si es True, ignora la caché y obtiene datos frescos
    """
    # Generar key de caché basada en los parámetros
    cache_key = f"{CACHE_PREFIX}all"
    if category:
        cache_key += f"_cat_{category}"
    if search:
        cache_key += f"_search_{search}"

    # Intentar obtener del caché primero
    if not force_refresh:
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            logger.debug(f"Cache hit para productos: {cache_key}")
            return cached_data

    # Si no está en caché o force_refresh es True, obtener del servicio
    try:
        params = {}
        if category:
            params['categoria'] = category
        if search:
            params['search'] = search

        response = requests.get(
            f"{settings.MICROSERVICES['INVENTARIO']['BASE_URL']}/api/productos/",
            params=params,
            headers={'X-API-Key': settings.MICROSERVICES['INVENTARIO']['API_KEY']},
            timeout=3  # Reducido de 5 a 3 segundos
        )
        
        if response.status_code == 200:
            data = response.json()
            # Guardar en caché
            cache.set(cache_key, data, CACHE_TIMEOUT)
            logger.debug(f"Datos de productos actualizados en caché: {cache_key}")
            return data
        else:
            logger.error(f"Error obteniendo productos: {response.status_code}")
            return None

    except requests.RequestException as e:
        logger.error(f"Error de conexión con el servicio de inventario: {str(e)}")
        return None

def get_product_detail(product_id):
    """
    Obtiene el detalle de un producto específico con caché.
    """
    cache_key = f"{CACHE_PREFIX}detail_{product_id}"
    
    # Intentar obtener del caché
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        return cached_data

    try:
        response = requests.get(
            f"{settings.MICROSERVICES['INVENTARIO']['BASE_URL']}/api/productos/{product_id}/",
            headers={'X-API-Key': settings.MICROSERVICES['INVENTARIO']['API_KEY']},
            timeout=3
        )
        
        if response.status_code == 200:
            data = response.json()
            # Guardar en caché
            cache.set(cache_key, data, CACHE_TIMEOUT)
            return data
        return None

    except requests.RequestException:
        return None