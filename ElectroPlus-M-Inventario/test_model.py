import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventario_core.settings')
django.setup()

from productos.models import Categoria

print('Model loaded successfully')
c = Categoria.objects.first()
print('First categoria:', c.__dict__ if c else 'None')
