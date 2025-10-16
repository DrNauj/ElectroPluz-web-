from django.test import TestCase, Client
from django.test.utils import override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from storefront.models import ProductImage, Category


class ProductMediaUploadTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_superuser('testadmin', 'test@local', 'pass')
        if not Category.objects.exists():
            self.category = Category.objects.create(name='TestCat', slug='testcat')
        else:
            self.category = Category.objects.first()

    @override_settings(ALLOWED_HOSTS=['localhost', 'testserver'])
    def test_create_product_with_images(self):
        c = Client()
        logged = c.login(username='testadmin', password='pass')
        self.assertTrue(logged)

        img1 = SimpleUploadedFile('a.jpg', b'filecontent1', content_type='image/jpeg')
        img2 = SimpleUploadedFile('b.jpg', b'filecontent2', content_type='image/jpeg')

        data = {
            'name': 'TST Product',
            'category': str(self.category.id),
            'price': '5.00',
            'stock': '3',
            'min_stock': '1',
        }

        files = [
            ('images', img1),
            ('images', img2),
        ]

        # Use FILES kwarg (uppercase) to mimic the working manual test
        resp = c.post('/dashboard/productos/crear/', data, FILES=files, HTTP_HOST='localhost')
        if resp.status_code != 200:
            print('RESPONSE CONTENT:', resp.content)
            print('CONTENT-TYPE:', resp.get('Content-Type'))
        self.assertEqual(resp.status_code, 200)
        j = resp.json()
        self.assertTrue(j.get('success'))
        # Debug field should report number created
        debug = j.get('debug', {})
        self.assertEqual(debug.get('files_received'), 2)
        self.assertEqual(debug.get('files_created'), 2)

        pid = j.get('id')
        self.assertIsNotNone(pid)
        self.assertEqual(ProductImage.objects.filter(product_id=pid).count(), 2)
