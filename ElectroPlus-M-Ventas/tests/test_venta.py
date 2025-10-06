import os
import sys
import django
import requests
import json
from datetime import datetime

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ventas_core.settings")
django.setup()

from ventas.models import Cliente, Usuario, Venta, DetalleVenta

def test_realizar_venta():
    print("\n=== Iniciando prueba de venta ===")
    
    try:
        # 1. Verificar cliente existente o crear uno nuevo
        try:
            cliente = Cliente.objects.get(email='juan.perez@test.com')
            print("Cliente encontrado:", cliente)
        except Cliente.DoesNotExist:
            cliente = Cliente.objects.create(
                nombres="Juan",
                apellidos="Pérez",
                email="juan.perez@test.com",
                telefono="987654321"
            )
            print("Cliente creado:", cliente)

        # 2. Verificar usuario vendedor
        try:
            vendedor = Usuario.objects.get(rol='Vendedor')
            print("Vendedor encontrado:", vendedor)
        except Usuario.DoesNotExist:
            vendedor = Usuario.objects.create(
                nombre_usuario="vendedor1",
                contrasena="hashed_password",  # En producción usar hash
                rol="Vendedor"
            )
            print("Vendedor creado:", vendedor)

        # 3. Verificar stock de productos (consultando al M-Inventario)
        INVENTARIO_API = 'http://127.0.0.1:8001/api'
        headers = {'SECRET_KEY_MICRO': 'tu_clave_secreta'}

        # Obtener información del producto (Laptop HP 15)
        response = requests.get(f"{INVENTARIO_API}/productos/1/", headers=headers)
        if response.status_code != 200:
            raise Exception("Error al obtener información del producto")
        
        producto = response.json()
        print(f"\nProducto a vender: {producto['nombre']}")
        print(f"Stock actual: {producto['stock']}")
        
        if producto['stock'] < 2:
            raise Exception("Stock insuficiente para la prueba")

        # 4. Crear la venta
        venta = Venta.objects.create(
            cliente=cliente,
            usuario=vendedor,
            fecha_venta=datetime.now(),
            total=float(producto['precio']) * 2,  # Compramos 2 unidades
            estado='Pendiente'
        )
        print(f"\nVenta creada: #{venta.id}")

        # 5. Crear detalle de venta
        detalle = DetalleVenta.objects.create(
            venta=venta,
            id_producto=producto['id'],
            cantidad=2,
            precio_unitario=float(producto['precio'])
        )
        print(f"Detalle de venta creado: {detalle.cantidad} unidades a ${detalle.precio_unitario} c/u")

        # 6. Actualizar stock en inventario
        update_url = f"{INVENTARIO_API}/productos/1/actualizar_stock/"
        update_data = {
            'cantidad': 2,
            'tipo_movimiento': 'Salida por Venta',
            'id_usuario': vendedor.id
        }
        print(f"\nActualizando stock en: {update_url}")
        print(f"Datos: {json.dumps(update_data, indent=2)}")
        print(f"Headers: {json.dumps(headers, indent=2)}")
        
        response = requests.patch(
            update_url,
            json=update_data,
            headers=headers
        )
        
        if response.status_code != 200:
            print(f"\nError HTTP {response.status_code}")
            print(f"Respuesta: {response.text}")
            raise Exception(f"Error al actualizar stock: {response.text}")

        resultado = response.json()
        print(f"\nStock actualizado: {resultado['nuevo_stock']} unidades")

        # 7. Actualizar estado de la venta
        venta.estado = 'En Proceso'
        venta.save()
        print(f"Estado de venta actualizado a: {venta.estado}")

        print("\n=== Prueba completada exitosamente ===")
        return True

    except Exception as e:
        print(f"\n❌ Error durante la prueba: {str(e)}")
        return False

if __name__ == "__main__":
    test_realizar_venta()