"""
Clase Cart refactorizada para gestionar el carrito de compras
a través de llamadas al Microservicio de VENTAS (puerto 8002).

El carrito ya no almacena datos de productos en la sesión local.
Solo almacena el ID de Carrito (cart_id) en la sesión, y opcionalmente
el ID del usuario autenticado para vincular el carrito.
"""
from django.conf import settings
import requests
import logging
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)

class Cart:
    """Clase para gestionar el carrito de compras a través de la API de Ventas."""
    
    def __init__(self, request):
        """Inicializa el carrito. Obtiene o crea un cart_id."""
        self.session = request.session
        self.request = request
        
        # Intentar obtener el ID de Carrito de la sesión
        cart_id = self.session.get('cart_id')
        
        # Si no hay ID de carrito, intentar crearlo en el microservicio
        if not cart_id:
            try:
                # El microservicio debe responder con un nuevo ID de carrito
                new_cart = self._make_request('post', 'api/carrito/crear_anonimo/')
                if new_cart and 'cart_id' in new_cart:
                    self.cart_id = new_cart['cart_id']
                    self.session['cart_id'] = self.cart_id
                    self.session.modified = True
                else:
                    self.cart_id = None
                    logger.error("Microservicio de Ventas no devolvió un 'cart_id' válido al crear.")
            except RequestException:
                self.cart_id = None
        else:
            self.cart_id = cart_id

    def _get_auth_headers(self):
        """Devuelve los encabezados de autenticación si el usuario está logueado."""
        headers = {
            'X-API-Key': settings.MICROSERVICES['VENTAS']['API_KEY'],
            'Content-Type': 'application/json'
        }
        
        # Si el usuario está autenticado, incluir el token
        if self.request.session.get('is_authenticated'):
            # Asume que el token está almacenado en request.session['user']['token']
            user_token = self.request.session['user']['token']
            headers['Authorization'] = f'Token {user_token}'
            
        return headers

    def _make_request(self, method, endpoint, data=None):
        """
        Función genérica para realizar peticiones al Microservicio de Ventas.
        Asegura la inclusión del API Key y el token de usuario si está disponible.
        """
        base_url = settings.MICROSERVICES['VENTAS']['BASE_URL']
        url = f"{base_url}{endpoint}"
        
        try:
            headers = self._get_auth_headers()
            
            if method == 'get':
                response = requests.get(url, headers=headers, timeout=5)
            elif method == 'post':
                response = requests.post(url, headers=headers, json=data, timeout=5)
            elif method == 'put':
                response = requests.put(url, headers=headers, json=data, timeout=5)
            elif method == 'delete':
                response = requests.delete(url, headers=headers, json=data, timeout=5)
            else:
                raise ValueError("Método HTTP no soportado.")
                
            response.raise_for_status()  # Lanza excepción para errores 4xx/5xx
            
            if response.status_code == 204: # No Content
                return {} 
                
            return response.json()
        
        except RequestException as e:
            logger.error(f"Error de conexión con Microservicio VENTAS en {url} ({method}): {e}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado al procesar la respuesta de VENTAS: {e}")
            return None


    # --- Métodos de Interacción del Carrito ---

    def add(self, product_id, quantity=1, override_quantity=False):
        """Agrega un producto al carrito o actualiza su cantidad a través del microservicio."""
        if not self.cart_id:
            logger.error("No hay ID de carrito disponible para agregar producto.")
            return False
        
        data = {
            'product_id': product_id,
            'quantity': quantity,
            'cart_id': self.cart_id,
            'override_quantity': override_quantity
        }
        
        # Endpoint: /api/carrito/items/agregar/ (debe manejar la lógica de sumar/reemplazar)
        result = self._make_request('post', 'api/carrito/items/agregar/', data=data)
        
        return result is not None

    def remove(self, product_id):
        """Elimina un producto del carrito a través del microservicio."""
        if not self.cart_id:
            return False
            
        data = {
            'product_id': product_id,
            'cart_id': self.cart_id,
        }
        
        # Endpoint: /api/carrito/items/eliminar/
        result = self._make_request('delete', 'api/carrito/items/eliminar/', data=data)
        
        return result is not None

    def update_quantity(self, product_id, quantity):
        """Actualiza la cantidad de un producto en el carrito."""
        if not self.cart_id:
            return False
            
        data = {
            'product_id': product_id,
            'quantity': quantity,
            'cart_id': self.cart_id,
        }
        
        # Endpoint: /api/carrito/items/actualizar/
        result = self._make_request('put', 'api/carrito/items/actualizar/', data=data)
        
        return result is not None

    def get_data(self):
        """
        Obtiene el estado completo del carrito (items, totales) desde el microservicio.
        Este es el único método que se llamará desde las vistas para obtener la información.
        """
        if not self.cart_id:
            return {'items': [], 'total_items': 0, 'subtotal': '0.00', 'total': '0.00'}

        # Endpoint: /api/carrito/{cart_id}/
        data = self._make_request('get', f'api/carrito/{self.cart_id}/')

        # Si hay un error, devuelve datos vacíos
        if data is None:
            return {'items': [], 'total_items': 0, 'subtotal': '0.00', 'total': '0.00'}
            
        # El microservicio debe devolver un diccionario que contenga 'items' (lista de productos en el carrito)
        # 'total_items', 'subtotal', 'total', etc.
        return data

    def clear(self):
        """Vacía el carrito en el microservicio y elimina el ID de la sesión local."""
        if not self.cart_id:
            return
            
        # Endpoint: /api/carrito/{cart_id}/vaciar/
        self._make_request('post', f'api/carrito/{self.cart_id}/vaciar/')
        
        # Eliminar el ID de la sesión
        if 'cart_id' in self.session:
            del self.session['cart_id']
        self.session.modified = True
        self.cart_id = None
        
    # Eliminamos __iter__ y __len__ ya que get_data() devuelve toda la información.
    # Los templates de Django ahora iterarán sobre cart.get_data().items
    
