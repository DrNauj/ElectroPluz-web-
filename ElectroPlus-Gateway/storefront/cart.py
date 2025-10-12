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

    def _call_inventario_service(self, endpoint):
        """Helper para llamar al servicio de inventario"""
        try:
            base_url = settings.MICROSERVICES['INVENTARIO']['BASE_URL']
            headers = {'X-API-Key': settings.MICROSERVICES['INVENTARIO']['API_KEY']}
            
            response = requests.get(f"{base_url}/api/{endpoint}", headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error calling inventario service: {e}")
            return None

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
        """Agrega un producto al carrito o actualiza su cantidad."""
        try:
            # Obtener el carrito de la sesión o crear uno nuevo
            cart = self.session.get('cart', {})
            product_id_str = str(product_id)
            
            # Validar el producto con el servicio de inventario
            product_data = self._call_inventario_service(f'productos/{product_id}/')
            
            if not product_data or 'error' in product_data:
                logger.error(f"Error al obtener producto {product_id}: {product_data.get('error', 'Unknown error')}")
                return False
            
            # Si el producto no está en el carrito, agregarlo
            if product_id_str not in cart:
                cart[product_id_str] = {
                    'quantity': 0,
                    'price': str(product_data['precio']),
                    'name': product_data['nombre'],
                    'image': product_data.get('imagen', ''),
                }
            
            # Actualizar cantidad
            if override_quantity:
                cart[product_id_str]['quantity'] = quantity
            else:
                cart[product_id_str]['quantity'] += quantity
                
            # Guardar en sesión
            self.session['cart'] = cart
            self.session.modified = True
            
            logger.debug(f"Producto {product_id} agregado al carrito. Cantidad: {quantity}")
            return True
            
        except Exception as e:
            logger.error(f"Error al agregar producto al carrito: {e}")
            return False

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
        Obtiene el estado completo del carrito desde la sesión.
        """
        cart = self.session.get('cart', {})
        
        items = []
        total = 0
        total_items = 0
        
        for product_id, item_data in cart.items():
            quantity = item_data['quantity']
            price = float(item_data['price'])
            subtotal = quantity * price
            
            items.append({
                'id': product_id,
                'nombre': item_data['name'],
                'cantidad': quantity,
                'precio': price,
                'subtotal': subtotal,
                'imagen': item_data.get('image', '')
            })
            
            total += subtotal
            total_items += quantity
        
        return {
            'items': items,
            'total_items': total_items,
            'subtotal': f"{total:.2f}",
            'total': f"{total:.2f}"
        }

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
    
