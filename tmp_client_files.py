from django.test import Client
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from storefront.models import Category

User = get_user_model()
if not User.objects.filter(username='testadmin2').exists():
    User.objects.create_superuser('testadmin2','t2@local','pass')
cat = Category.objects.first() or Category.objects.create(name='c', slug='c')

c = Client()
logged = c.login(username='testadmin2', password='pass')
print('logged', logged)
img1 = SimpleUploadedFile('a.jpg', b'filecontent1', content_type='image/jpeg')
img2 = SimpleUploadedFile('b.jpg', b'filecontent2', content_type='image/jpeg')

data = {'name':'CliTest','category':str(cat.id),'price':'1.00','stock':'1','min_stock':'0'}
files = {'images': [img1, img2]}
resp = c.post('/dashboard/productos/crear/', data, files=files, HTTP_HOST='localhost')
print('status', resp.status_code)
print('content', resp.content)
try:
    print('json', resp.json())
except Exception as e:
    print('no json', e)
