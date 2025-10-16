from django.test import Client
from accounts.models import CustomUser
from storefront.models import Product, Order

c = Client()
# Use existing non-staff user
user = CustomUser.objects.filter(is_staff=False).first()
if not user:
    raise SystemExit('No customer user found')

# Find a product with stock > 0
product = Product.objects.filter(is_active=True).exclude(stock__lte=0).first()
if not product:
    raise SystemExit('No product with stock found')

# Choose quantity 1 or up to available stock
qty = 1 if product.stock >= 1 else product.stock
orig_stock = product.stock
print('Using user:', user.id, user.email)
print('Using product:', product.id, product.name, 'stock=', orig_stock)

# Force login the client
c.force_login(user)

# Prepare session cart format matching Cart.add
session = c.session
session['cart'] = {
    str(product.id): {
        'quantity': qty,
        'price': str(product.price),
        'name': product.name,
        'image': product.image,
        'id': str(product.id)
    }
}
session.save()
print('Session cart set:', c.session.get('cart'))

# Count orders before
from storefront.models import Order as _Order
before_cnt = _Order.objects.filter(user=user).count()
print('Orders before:', before_cnt)

# POST to checkout - include minimal required fields (payment_method) and set HTTP_HOST
post_data = {
    'payment_method': 'CASH',
    'shipping_address': 'Av. Test 123',
    'contact_phone': '+51123456789',
    'notes': 'Simulación de compra'
}
resp = c.post('/tienda/checkout/', post_data, HTTP_HOST='localhost', follow=True)

print('Response status code:', resp.status_code)
print('Response URL:', resp.redirect_chain)
print('Response content snippet:', resp.content[:500])
after_cnt = _Order.objects.filter(user=user).count()
print('Orders after:', after_cnt)

# Print messages from context if available
msgs = []
if hasattr(resp, 'context') and resp.context:
    for m in resp.context.get('messages') or []:
        msgs.append(str(m))
print('Messages in response context:', msgs)

# Refresh product
product.refresh_from_db()
print('Stock after checkout:', product.stock)

# Find latest order for user
latest_order = Order.objects.filter(user=user).order_by('-created_at').first()
if latest_order:
    print('Latest order id:', latest_order.id, 'status:', latest_order.status, 'total:', latest_order.total)
    print('Order items:')
    for it in latest_order.items.all():
        print(' -', it.product_name, 'qty', it.quantity, 'price', it.product_price)
else:
    print('No order created')
