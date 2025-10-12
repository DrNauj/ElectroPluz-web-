from django.db import models
from django.utils import timezone

class Cupon(models.Model):
    TIPO_CHOICES = [
        ('Porcentaje', 'Porcentaje'),
        ('Cantidad Fija', 'Cantidad Fija')
    ]
    
    id = models.AutoField(primary_key=True)
    codigo = models.CharField(max_length=20, unique=True)
    tipo_descuento = models.CharField(max_length=20, choices=TIPO_CHOICES)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    valido_para_producto = models.ForeignKey(
        'Producto',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_column='valido_para_producto_id'
    )

    class Meta:
        db_table = 'Cupones'
        managed = False

    def __str__(self):
        return f"{self.codigo} - {self.tipo_descuento} ({self.valor})"

    @property
    def esta_activo(self):
        ahora = timezone.now()
        return self.fecha_inicio <= ahora <= self.fecha_fin

    def aplicar_descuento(self, precio):
        if not self.esta_activo:
            return precio
            
        if self.tipo_descuento == 'Porcentaje':
            descuento = precio * (self.valor / 100)
        else:  # Cantidad Fija
            descuento = min(self.valor, precio)  # No descontar más que el precio
            
        return max(precio - descuento, 0)  # No permitir precios negativos

class UsoCupon(models.Model):
    id = models.AutoField(primary_key=True)
    cupon = models.ForeignKey(
        Cupon,
        on_delete=models.PROTECT,
        db_column='id_cupon'
    )
    id_venta = models.IntegerField()  # FK a Ventas en microservicio de ventas
    fecha_uso = models.DateTimeField()

    class Meta:
        db_table = 'UsoCupones'
        managed = False

    def __str__(self):
        return f"Cupón {self.cupon.codigo} usado en venta {self.id_venta}"