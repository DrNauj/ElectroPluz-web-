import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventario_core.settings')
django.setup()

from productos.models import Categoria
from django.db import connection

print('Model loaded successfully')
c = Categoria.objects.first()
print('First categoria:', c.__dict__ if c else 'None')

cursor = connection.cursor()
cursor.execute('DESCRIBE Categorias')
columns = cursor.fetchall()
print('Columns in Categorias table:')
for col in columns:
    print(col)
