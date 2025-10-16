from django import template
from ..cart import Cart

register = template.Library()

@register.simple_tag(takes_context=True)
def cart_item_count(context):
    request = context['request']
    cart = Cart(request)
    return len(cart)