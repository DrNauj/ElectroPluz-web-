"""
Procesadores de contexto para la aplicación storefront
"""

from django.conf import settings
import requests
import logging

logger = logging.getLogger(__name__)

def categories(request):
    """
    Agrega las categorías al contexto global usando caché de manera eficiente.
    """
    # No procesar para archivos estáticos o admin
    if request.path.startswith(('/static/', '/admin/', '/media/')):
        return {'categories': []}
        
    from django.core.cache import cache
    from storefront.views import _call_inventario_service
    
    CACHE_KEY = 'global_categories'
    CACHE_TIMEOUT = 3600  # 1 hora
    
    try:
        # Intentar obtener del caché
        categories_data = cache.get(CACHE_KEY)
        
        if categories_data is None:
            # No está en caché, obtener usando el helper optimizado
            categories_data = _call_inventario_service(
                'categorias/',
                cache_timeout=CACHE_TIMEOUT
            )
            
            # Procesar respuesta
            if isinstance(categories_data, list):
                categories_data = categories_data
            elif isinstance(categories_data, dict) and 'results' in categories_data:
                categories_data = categories_data['results']
            elif isinstance(categories_data, dict) and 'error' in categories_data:
                categories_data = []
            else:
                categories_data = []
        
        return {'categories': categories_data}
            
    except Exception as e:
        logger.error(f"Error al obtener categorías: {str(e)}")
        return {'categories': []}