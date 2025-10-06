import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "inventario_core.settings")
django.setup()

from productos.models import Categoria, Proveedor, Producto

print("\nCategorías:")
for categoria in Categoria.objects.all():
    print(f"ID: {categoria.id} - {categoria.nombre} - {categoria.descripcion}")

print("\nProveedores:")
for proveedor in Proveedor.objects.all():
    print(f"ID: {proveedor.id} - {proveedor.nombre} - {proveedor.telefono}")

print("\nProductos:")
for producto in Producto.objects.all():
    print(f"ID: {producto.id} - {producto.nombre} - Precio: ${producto.precio} - Stock: {producto.stock}")
    print(f"   Categoría: {producto.categoria.nombre}")
    print(f"   Proveedor: {producto.proveedor.nombre}")