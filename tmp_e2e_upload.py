from django.test import Client
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from storefront.models import ProductImage, Category

User = get_user_model()

# Crear categoría si no existe
cat = None
if not Category.objects.exists():
    cat = Category.objects.create(name='Prueba', slug='prueba')
else:
    cat = Category.objects.first()

# Crear superusuario de prueba
if not User.objects.filter(username='testadmin').exists():
    u = User.objects.create_superuser('testadmin', 'test@local', 'pass')
else:
    u = User.objects.get(username='testadmin')

c = Client()
logged_in = c.login(username='testadmin', password='pass')
print('logged_in', logged_in)

img1 = SimpleUploadedFile('a.jpg', b'filecontent1', content_type='image/jpeg')
img2 = SimpleUploadedFile('b.jpg', b'filecontent2', content_type='image/jpeg')

data = {
    'name': 'E2E Test Product',
    'category': str(cat.id),
    'price': '10.00',
    'stock': '5',
    'min_stock': '1',
    'images': [img1, img2]
}

resp = c.post('/dashboard/productos/crear/', data, HTTP_HOST='localhost')
print('status', resp.status_code)
try:
    print('resp json:', resp.json())
    pid = resp.json().get('id')
    if pid:
        print('images for product', pid, ProductImage.objects.filter(product_id=pid).count())
except Exception as e:
    print('no json or parse error', e)

print('total images overall', ProductImage.objects.count())
