import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ventas_core.settings')
django.setup()

from ventas.models import Venta, DetalleVenta

print("Limpiando datos de ventas...")
DetalleVenta.objects.all().delete()
Venta.objects.all().delete()

print("¡Datos de ventas eliminados!")