from django.core.management import execute_from_command_line
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ventas_core.settings')
django.setup()

from ventas.models import Cliente, Usuario

# Insertar Usuarios
usuarios = [
    {'nombre_usuario': 'admin', 'contrasena': 'admin123', 'rol': 'Administrador'},
    {'nombre_usuario': 'vendedor1', 'contrasena': 'vend123', 'rol': 'Vendedor'},
    {'nombre_usuario': 'almacen1', 'contrasena': 'alm123', 'rol': 'Almacén'},
    {'nombre_usuario': 'gerente1', 'contrasena': 'ger123', 'rol': 'Gerente'}
]

for user_data in usuarios:
    Usuario.objects.get_or_create(**user_data)

# Insertar Clientes
clientes = [
    {
        'nombres': 'Juan',
        'apellidos': 'Pérez',
        'email': 'juan@email.com',
        'telefono': '923456789',
        'direccion': 'Av. Lima 123'
    },
    {
        'nombres': 'María',
        'apellidos': 'García',
        'email': 'maria@email.com',
        'telefono': '934567890',
        'direccion': 'Jr. Arequipa 456'
    },
    {
        'nombres': 'Carlos',
        'apellidos': 'López',
        'email': 'carlos@email.com',
        'telefono': '945678901',
        'direccion': 'Calle Tacna 789'
    },
    {
        'nombres': 'Ana',
        'apellidos': 'Martínez',
        'email': 'ana@email.com',
        'telefono': '956789012',
        'direccion': 'Av. Cusco 321'
    },
    {
        'nombres': 'Pedro',
        'apellidos': 'Sánchez',
        'email': 'pedro@email.com',
        'telefono': '967890123',
        'direccion': 'Jr. Puno 654'
    }
]

for client_data in clientes:
    Cliente.objects.get_or_create(**client_data)

print("Datos cargados exitosamente en el servicio de Ventas")