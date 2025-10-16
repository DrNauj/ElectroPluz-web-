from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal

class Auditoria(models.Model):
    TIPO_ACCION_CHOICES = [
        ('INSERT', 'Inserción'),
        ('UPDATE', 'Actualización'),
        ('DELETE', 'Eliminación')
    ]

    id = models.AutoField(primary_key=True)
    tabla_afectada = models.CharField(max_length=50)
    id_registro = models.IntegerField()
    tipo_accion = models.CharField(max_length=6, choices=TIPO_ACCION_CHOICES)
    fecha_accion = models.DateTimeField()
    id_usuario = models.IntegerField()
    detalles = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'Auditoria'
        verbose_name = 'Auditoría'
        verbose_name_plural = 'Auditorías'
        indexes = [
            models.Index(fields=['tabla_afectada', 'id_registro']),
            models.Index(fields=['fecha_accion']),
            models.Index(fields=['id_usuario']),
        ]

    def __str__(self):
        return f"{self.tipo_accion} en {self.tabla_afectada} ({self.id_registro})"


class ReporteMensualProductos(models.Model):
    id = models.AutoField(primary_key=True)
    anio = models.IntegerField()
    mes = models.IntegerField()
    producto = models.ForeignKey(
        'Producto',
        on_delete=models.PROTECT,
        db_column='id_producto'
    )
    cantidad_vendida = models.IntegerField()

    class Meta:
        db_table = 'ReporteMensualProductos'
        verbose_name = 'Reporte Mensual de Producto'
        verbose_name_plural = 'Reportes Mensuales de Productos'
        unique_together = [['anio', 'mes', 'producto']]
        indexes = [
            models.Index(fields=['anio', 'mes']),
            models.Index(fields=['producto']),
        ]

    def __str__(self):
        return f"Reporte {self.mes}/{self.anio} - {self.producto.nombre}"


# Removed duplicate Cupon model - using the one from models_cupones.py
