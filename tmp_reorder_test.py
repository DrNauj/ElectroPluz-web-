from django.test import Client
from django.contrib.auth import get_user_model
User = get_user_model()

c = Client()
admin = User.objects.filter(is_superuser=True).first()
if not admin:
    admin = User.objects.create_superuser('tmpadmin','tmp@local','pass')

c.login(username=admin.username, password='pass')
resp = c.get('/dashboard/inventario/reorden/', HTTP_HOST='localhost')
print('status', resp.status_code)
print(resp.content.decode('utf-8')[:1000])
