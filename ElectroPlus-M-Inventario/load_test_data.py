from django.core.management import execute_from_command_line
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventario_core.settings')
django.setup()

from productos.models import Categoria, Proveedor, Producto

# Insertar Categorías
categorias = [
    {'nombre': 'Electrodomésticos', 'descripcion': 'Aparatos eléctricos para el hogar'},
    {'nombre': 'Computadoras', 'descripcion': 'Equipos de cómputo y accesorios'},
    {'nombre': 'Smartphones', 'descripcion': 'Teléfonos móviles inteligentes'},
    {'nombre': 'Audio y Video', 'descripcion': 'Equipos de entretenimiento'},
    {'nombre': 'Gaming', 'descripcion': 'Consolas y videojuegos'}
]

for cat_data in categorias:
    Categoria.objects.get_or_create(**cat_data)

# Insertar Proveedores
proveedores = [
    {'nombre': 'TechCorp S.A.', 'direccion': 'Av. Principal 123', 'telefono': '987654321', 'email': 'ventas@techcorp.com'},
    {'nombre': 'ElectroImport', 'direccion': 'Calle Comercio 456', 'telefono': '987654322', 'email': 'pedidos@electroimport.com'},
    {'nombre': 'Digital Solutions', 'direccion': 'Jr. Tecnología 789', 'telefono': '987654323', 'email': 'info@digisolutions.com'},
    {'nombre': 'Gaming World', 'direccion': 'Av. Gamers 321', 'telefono': '987654324', 'email': 'compras@gamingworld.com'},
    {'nombre': 'SmartTech', 'direccion': 'Calle Smart 654', 'telefono': '987654325', 'email': 'contacto@smarttech.com'}
]

for prov_data in proveedores:
    Proveedor.objects.get_or_create(**prov_data)

# Insertar Productos
productos = [
    {
        'nombre': 'Laptop HP 15',
        'descripcion': 'Laptop HP 15.6" Core i5',
        'precio': 2499.99,
        'stock': 50,
        'categoria': Categoria.objects.get(nombre='Computadoras'),
        'proveedor': Proveedor.objects.get(nombre='TechCorp S.A.')
    },
    {
        'nombre': 'Samsung Galaxy S21',
        'descripcion': 'Smartphone Samsung última generación',
        'precio': 3299.99,
        'stock': 30,
        'categoria': Categoria.objects.get(nombre='Smartphones'),
        'proveedor': Proveedor.objects.get(nombre='SmartTech')
    },
    {
        'nombre': 'Smart TV LG 55"',
        'descripcion': 'Televisor LED Smart 4K',
        'precio': 2799.99,
        'stock': 25,
        'categoria': Categoria.objects.get(nombre='Audio y Video'),
        'proveedor': Proveedor.objects.get(nombre='ElectroImport')
    },
    {
        'nombre': 'PlayStation 5',
        'descripcion': 'Consola de videojuegos',
        'precio': 2999.99,
        'stock': 20,
        'categoria': Categoria.objects.get(nombre='Gaming'),
        'proveedor': Proveedor.objects.get(nombre='Gaming World')
    },
    {
        'nombre': 'Refrigeradora Samsung',
        'descripcion': 'Refrigeradora No Frost 500L',
        'precio': 3499.99,
        'stock': 15,
        'categoria': Categoria.objects.get(nombre='Electrodomésticos'),
        'proveedor': Proveedor.objects.get(nombre='ElectroImport')
    }
]

for prod_data in productos:
    Producto.objects.get_or_create(**prod_data)

print("Datos cargados exitosamente en el servicio de Inventario")