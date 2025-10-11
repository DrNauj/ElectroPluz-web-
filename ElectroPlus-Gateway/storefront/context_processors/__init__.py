from gateway_app.models import Category
from .cart import Cart

def cart(request):
    """
    Context processor para agregar el carrito de compras a todos los templates
    """
    return {'cart': Cart(request)}

def categories(request):
    """
    Context processor para agregar las categorías activas a todos los templates
    """
    return {'categories': Category.objects.filter(active=True)}