from django.db import models
from .models_cupones import Cupon, UsoCupon

class Categoria(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=45)
    descripcion = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'Categorias'
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        managed = False

    def __str__(self):
        return self.nombre

class Proveedor(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=255, null=True, blank=True)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(max_length=100, null=True, blank=True)

    class Meta:
        db_table = 'Proveedores'
        verbose_name = 'Proveedor'
        verbose_name_plural = 'Proveedores'
        managed = False

    def __str__(self):
        return self.nombre

class Producto(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(null=True, blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
    categoria = models.ForeignKey(
        Categoria, 
        on_delete=models.PROTECT,
        db_column='id_categoria'
    )
    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.PROTECT,
        db_column='id_proveedor'
    )

    class Meta:
        db_table = 'Productos'
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        managed = False

    def __str__(self):
        return self.nombre

class HistorialInventario(models.Model):
    id = models.AutoField(primary_key=True)
    TIPO_MOVIMIENTO_CHOICES = [
        ('Entrada', 'Entrada'),
        ('Salida por Venta', 'Salida por Venta'),
        ('Salida por Devolución', 'Salida por Devolución'),
        ('Ajuste', 'Ajuste')
    ]

    producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT,
        db_column='id_producto'
    )
    tipo_movimiento = models.CharField(
        max_length=25,
        choices=TIPO_MOVIMIENTO_CHOICES
    )
    cantidad = models.IntegerField()
    fecha = models.DateTimeField()
    usuario = models.IntegerField(null=True)  # ID del usuario en el microservicio de ventas
    request_id = models.CharField(max_length=50, null=True)  # Para correlación de logs y trazabilidad

    class Meta:
        db_table = 'HistorialInventario'
        verbose_name = 'Historial de Inventario'
        verbose_name_plural = 'Historiales de Inventario'
        managed = False
        indexes = [
            models.Index(fields=['producto', '-fecha']),  # Para optimizar consultas del dashboard
            models.Index(fields=['request_id']),  # Para trazabilidad
        ]

    def __str__(self):
        return f"{self.tipo_movimiento} - {self.producto.nombre} ({self.cantidad})"
