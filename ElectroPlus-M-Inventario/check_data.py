import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventario_core.settings')
django.setup()

from productos.models import Categoria, Proveedor, Producto

print("\nVerificando Categorías:")
print(Categoria.objects.all().count(), "categorías encontradas")
for cat in Categoria.objects.all():
    print(f"- {cat.nombre}")

print("\nVerificando Proveedores:")
print(Proveedor.objects.all().count(), "proveedores encontrados")
for prov in Proveedor.objects.all():
    print(f"- {prov.nombre}")

print("\nVerificando Productos:")
print(Producto.objects.all().count(), "productos encontrados")
for prod in Producto.objects.all():
    print(f"- {prod.nombre} (Stock: {prod.stock})")