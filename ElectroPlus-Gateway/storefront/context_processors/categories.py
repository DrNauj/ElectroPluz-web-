"""
Procesadores de contexto para la aplicación storefront
"""

from django.conf import settings
import requests
import logging

logger = logging.getLogger(__name__)

def categories(request):
    """
    Agrega las categorías al contexto global.
    """
    try:
        # Configuración del servicio de inventario
        base_url = settings.MICROSERVICES['INVENTARIO']['BASE_URL'].rstrip('/')
        api_key = settings.MICROSERVICES['INVENTARIO']['API_KEY']
        
        # URL para obtener categorías
        url = f"{base_url}/api/categorias/"
        
        # Headers necesarios
        headers = {
            'X-API-Key': api_key,
            'Accept': 'application/json'
        }
        
        # Realizar la petición
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        
        # Procesar la respuesta
        categories_data = response.json()
        if isinstance(categories_data, list):
            return {'categories': categories_data}
        elif isinstance(categories_data, dict) and 'results' in categories_data:
            return {'categories': categories_data['results']}
        else:
            return {'categories': []}
            
    except Exception as e:
        logger.error(f"Error al obtener categorías: {str(e)}")
        return {'categories': []}