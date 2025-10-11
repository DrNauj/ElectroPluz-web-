from decimal import Decimal
from gateway_app.models import Product

class Cart:
    """Clase para gestionar el carrito de compras"""
    
    def __init__(self, request):
        """Inicializa el carrito"""
        self.session = request.session
        cart = self.session.get('cart')
        if not cart:
            cart = self.session['cart'] = {}
        self.cart = cart

    def add(self, product, quantity=1, override_quantity=False):
        """
        Agrega un producto al carrito o actualiza su cantidad
        """
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {'quantity': 0, 'price': str(product.price)}
        
        if override_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] = self.cart[product_id]['quantity'] + quantity
        
        # Asegurar que la cantidad no exceda el stock disponible
        if self.cart[product_id]['quantity'] > product.stock:
            self.cart[product_id]['quantity'] = product.stock
        
        self.save()

    def save(self):
        """Marca la sesión como modificada para guardar cambios"""
        self.session.modified = True

    def remove(self, product):
        """Elimina un producto del carrito"""
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def get_total_price(self):
        """Calcula el total del carrito"""
        total = Decimal('0.0')
        for item in self.cart.values():
            total += Decimal(item['price']) * item['quantity']
        return total

    def clear(self):
        """Vacía el carrito"""
        del self.session['cart']
        self.save()

    def __iter__(self):
        """
        Itera sobre los items en el carrito y obtiene los productos de la base de datos
        """
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        cart = self.cart.copy()

        for product in products:
            cart[str(product.id)]['product'] = product

        for item in cart.values():
            item['price'] = Decimal(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            yield item

    def __len__(self):
        """
        Cuenta todos los items en el carrito
        """
        return sum(item['quantity'] for item in self.cart.values())

    @property
    def total_items(self):
        """
        Devuelve el número total de items en el carrito
        """
        return self.__len__()