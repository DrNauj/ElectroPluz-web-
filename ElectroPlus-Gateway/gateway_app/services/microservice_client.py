"""
Módulo para manejar las conexiones a microservicios de forma robusta.
Incluye manejo de errores, retries, timeouts y logging.
"""
import requests
from requests.exceptions import RequestException, Timeout, HTTPError
from django.conf import settings
import logging
import time
from functools import wraps

logger = logging.getLogger(__name__)

class MicroserviceConnectionError(Exception):
    """Excepción personalizada para errores de conexión con microservicios."""
    pass

def with_retry(max_retries=3, backoff_factor=0.3):
    """
    Decorador que implementa retry con backoff exponencial.
    
    Args:
        max_retries (int): Número máximo de intentos
        backoff_factor (float): Factor para el tiempo de espera entre intentos
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (Timeout, ConnectionError) as e:
                    last_exception = e
                    if attempt < max_retries - 1:  # No esperar en el último intento
                        time.sleep(backoff_factor * (2 ** attempt))
                    logger.warning(
                        f"Intento {attempt + 1} de {max_retries} falló para {func.__name__}. "
                        f"Error: {str(e)}"
                    )
                except Exception as e:
                    # Para otros errores, no reintentar
                    raise MicroserviceConnectionError(f"Error en {func.__name__}: {str(e)}")
            
            # Si llegamos aquí, todos los intentos fallaron
            raise MicroserviceConnectionError(
                f"Todos los intentos fallaron para {func.__name__}. "
                f"Último error: {str(last_exception)}"
            )
        return wrapper
    return decorator

class MicroserviceClient:
    """Cliente base para conexiones a microservicios."""
    
    def __init__(self, service_name):
        """
        Inicializa el cliente para un microservicio específico.
        
        Args:
            service_name (str): Nombre del microservicio ('VENTAS' o 'INVENTARIO')
        """
        if service_name not in settings.MICROSERVICES:
            raise ValueError(f"Microservicio no configurado: {service_name}")
            
        self.base_url = settings.MICROSERVICES[service_name]['BASE_URL']
        self.api_key = settings.MICROSERVICES[service_name]['API_KEY']
        self.service_name = service_name
        
    def _get_headers(self, additional_headers=None):
        """Construye los headers de la petición."""
        headers = {
            'X-API-Key': self.api_key,
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        if additional_headers:
            headers.update(additional_headers)
        return headers
        
    @with_retry()
    def get(self, endpoint, params=None, headers=None):
        """
        Realiza una petición GET al microservicio.
        
        Args:
            endpoint (str): Endpoint a llamar (sin el base_url)
            params (dict): Parámetros de query string
            headers (dict): Headers adicionales
        
        Returns:
            dict: Respuesta del microservicio
            
        Raises:
            MicroserviceConnectionError: Si hay errores de conexión
        """
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        try:
            response = requests.get(
                url,
                headers=self._get_headers(headers),
                params=params,
                timeout=5
            )
            response.raise_for_status()
            return response.json()
            
        except Timeout:
            logger.error(f"Timeout al conectar con {self.service_name} en {endpoint}")
            raise
        except HTTPError as e:
            logger.error(
                f"Error HTTP {e.response.status_code} de {self.service_name} en {endpoint}: "
                f"{e.response.text}"
            )
            raise
        except RequestException as e:
            logger.error(f"Error al conectar con {self.service_name} en {endpoint}: {str(e)}")
            raise
            
    @with_retry()
    def post(self, endpoint, data, headers=None):
        """Realiza una petición POST al microservicio."""
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        try:
            response = requests.post(
                url,
                headers=self._get_headers(headers),
                json=data,
                timeout=5
            )
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            logger.error(f"Error en POST a {self.service_name} en {endpoint}: {str(e)}")
            raise
            
    @with_retry()
    def patch(self, endpoint, data, headers=None):
        """Realiza una petición PATCH al microservicio."""
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        try:
            response = requests.patch(
                url,
                headers=self._get_headers(headers),
                json=data,
                timeout=5
            )
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            logger.error(f"Error en PATCH a {self.service_name} en {endpoint}: {str(e)}")
            raise

# Instancias pre-configuradas para uso en las vistas
inventario_client = MicroserviceClient('INVENTARIO')
ventas_client = MicroserviceClient('VENTAS')