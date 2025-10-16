from accounts.models import CustomUser
from storefront.models import Claim, ClaimUpdate, Order
import random

u = CustomUser.objects.get(pk=2)
orders = list(Order.objects.filter(user=u)[:6])
types = ['product_issue','shipping_issue','wrong_product','other']
created = []
for i,o in enumerate(orders):
    c = Claim.objects.create(order=o, user=u, type=random.choice(types), description=f'Reclamo de prueba {i+1} para orden {o.id}')
    created.append(c)
    ClaimUpdate.objects.create(claim=c, user=u, status='pending', comment='Cliente reportó inicial')
    if i%2==0:
        ClaimUpdate.objects.create(claim=c, user=u, status='in_progress', comment='Soporte revisando')
    if i%3==0:
        c.status='resolved'
        c.save()
        ClaimUpdate.objects.create(claim=c, user=u, status='resolved', comment='Resuelto automáticamente (test)')

print('Created claims:', [(c.id, c.code, c.status) for c in created])
