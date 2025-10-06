from django.test import TestCase
from django.utils import timezone
from .models import Producto, Categoria, HistorialInventario, Proveedor
from .models_reporting import Auditoria, ReporteMensualProductos, Cupon


class TestInventario(TestCase):
    """Tests para el módulo de inventario"""
    
    def setUp(self):
        """Configura el ambiente de pruebas"""
        # Crear categoría de prueba
        self.categoria = Categoria.objects.create(
            nombre="Electrodomésticos",
            descripcion="Electrodomésticos para el hogar"
        )
        
        # Crear proveedor de prueba
        self.proveedor = Proveedor.objects.create(
            nombre="ElectroImport",
            direccion="Av. Industrial 123",
            telefono="987654321",
            email="contacto@electroimport.com"
        )
        
        # Crear producto de prueba
        self.producto = Producto.objects.create(
            nombre="Refrigerador",
            descripcion="Refrigerador de dos puertas",
            precio=599.99,
            stock=10,
            categoria=self.categoria,
            proveedor=self.proveedor
        )

    def test_actualizar_stock(self):
        """Prueba la actualización de stock y registro en historial"""
        historial = HistorialInventario.objects.create(
            producto=self.producto,
            tipo_movimiento='Entrada',
            cantidad=5,
            fecha=timezone.now(),
            usuario=1,
            request_id='test-123'
        )
        self.producto.refresh_from_db()
        self.assertEqual(historial.cantidad, 5)
        self.assertEqual(historial.request_id, 'test-123')

    def test_auditoria(self):
        """Prueba el registro de auditoría"""
        auditoria = Auditoria.objects.create(
            tabla_afectada='Productos',
            id_registro=self.producto.id,
            tipo_accion='UPDATE',
            fecha_accion=timezone.now(),
            id_usuario=1,
            detalles='Actualización de stock'
        )
        self.assertEqual(auditoria.tipo_accion, 'UPDATE')
        self.assertEqual(auditoria.tabla_afectada, 'Productos')

    def test_reporte_mensual(self):
        """Prueba la creación de reportes mensuales"""
        reporte = ReporteMensualProductos.objects.create(
            anio=2025,
            mes=10,
            producto=self.producto,
            cantidad_vendida=100
        )
        self.assertEqual(reporte.cantidad_vendida, 100)
        self.assertEqual(reporte.anio, 2025)
        self.assertEqual(reporte.mes, 10)

    def test_cupon(self):
        """Prueba la creación y validación de cupones"""
        cupon = Cupon.objects.create(
            codigo='TEST10',
            tipo_descuento='Porcentaje',
            valor=10.00,
            fecha_inicio=timezone.now(),
            fecha_fin=timezone.now() + timezone.timedelta(days=30),
            valido_para_producto=self.producto
        )
        self.assertEqual(cupon.codigo, 'TEST10')
        self.assertEqual(cupon.tipo_descuento, 'Porcentaje')
        self.assertEqual(float(cupon.valor), 10.00)

    def test_filtros_historial(self):
        """Prueba los filtros del historial de inventario"""
        fecha_base = timezone.now()
        
        # Crear registros de prueba
        HistorialInventario.objects.create(
            producto=self.producto,
            tipo_movimiento='Entrada',
            cantidad=5,
            fecha=fecha_base,
            usuario=1
        )
        HistorialInventario.objects.create(
            producto=self.producto,
            tipo_movimiento='Salida por Venta',
            cantidad=3,
            fecha=fecha_base + timezone.timedelta(days=1),
            usuario=1
        )
        
        # Probar filtros
        self.assertEqual(
            HistorialInventario.objects.filter(tipo_movimiento='Entrada').count(),
            1
        )
        self.assertEqual(
            HistorialInventario.objects.filter(tipo_movimiento='Salida por Venta').count(),
            1
        )