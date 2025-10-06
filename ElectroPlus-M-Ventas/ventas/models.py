from django.db import models

class Usuario(models.Model):
    id = models.AutoField(primary_key=True)
    ROLES = [
        ('Administrador', 'Administrador'),
        ('Vendedor', 'Vendedor'),
        ('Almacén', 'Almacén'),
        ('Gerente', 'Gerente')
    ]

    nombre_usuario = models.CharField(max_length=50, unique=True)
    contrasena = models.CharField(max_length=255)
    rol = models.CharField(max_length=20, choices=ROLES)

    class Meta:
        db_table = 'Usuarios'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        managed = False

    def __str__(self):
        return f"{self.nombre_usuario} ({self.rol})"

class Cliente(models.Model):
    id = models.AutoField(primary_key=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    email = models.EmailField(max_length=100, unique=True)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    direccion = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'Clientes'
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        managed = False

    def __str__(self):
        return f"{self.nombres} {self.apellidos}"

class Venta(models.Model):
    id = models.AutoField(primary_key=True)
    ESTADOS = [
        ('Pendiente', 'Pendiente'),
        ('En Proceso', 'En Proceso'),
        ('Enviado', 'Enviado'),
        ('Entregado', 'Entregado'),
        ('Cancelado', 'Cancelado'),
        ('Reembolsado', 'Reembolsado')
    ]

    fecha_venta = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=20, choices=ESTADOS)
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        db_column='id_cliente'
    )
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        db_column='id_usuario'
    )

    class Meta:
        db_table = 'Ventas'
        verbose_name = 'Venta'
        verbose_name_plural = 'Ventas'
        managed = False

    def __str__(self):
        return f"Venta #{self.id} - {self.cliente}"

class DetalleVenta(models.Model):
    id = models.AutoField(primary_key=True)
    venta = models.ForeignKey(
        Venta,
        on_delete=models.CASCADE,
        db_column='id_venta'
    )
    id_producto = models.IntegerField()  # ID del producto en el microservicio de inventario
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'DetalleVenta'
        verbose_name = 'Detalle de Venta'
        verbose_name_plural = 'Detalles de Venta'
        managed = False

    def __str__(self):
        return f"Detalle de Venta #{self.venta.id}"

class Devolucion(models.Model):
    id = models.AutoField(primary_key=True)
    venta = models.ForeignKey(
        Venta,
        on_delete=models.PROTECT,
        db_column='id_venta'
    )
    fecha_devolucion = models.DateTimeField(auto_now_add=True)
    motivo = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'Devoluciones'
        verbose_name = 'Devolución'
        verbose_name_plural = 'Devoluciones'
        managed = False

    def __str__(self):
        return f"Devolución de Venta #{self.venta.id}"

class DetalleDevolucion(models.Model):
    devolucion = models.ForeignKey(
        Devolucion,
        on_delete=models.CASCADE,
        db_column='id_devolucion'
    )
    # id_producto se manejará a través del API Gateway
    cantidad_devuelta = models.IntegerField()

    class Meta:
        db_table = 'DetalleDevolucion'
        verbose_name = 'Detalle de Devolución'
        verbose_name_plural = 'Detalles de Devolución'
        managed = False

    def __str__(self):
        return f"Detalle de Devolución #{self.devolucion.id}"

class Cupon(models.Model):
    id = models.AutoField(primary_key=True)
    TIPO_DESCUENTO = [
        ('Porcentaje', 'Porcentaje'),
        ('Cantidad Fija', 'Cantidad Fija')
    ]

    codigo = models.CharField(max_length=20, unique=True)
    tipo_descuento = models.CharField(max_length=20, choices=TIPO_DESCUENTO)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    valido_para_producto_id = models.IntegerField(null=True, blank=True)  # ID del producto en M-Inventario

    class Meta:
        db_table = 'Cupones'
        verbose_name = 'Cupón'
        verbose_name_plural = 'Cupones'
        managed = False

    def __str__(self):
        return f"{self.codigo} - {self.tipo_descuento} ({self.valor})"

class UsoCupon(models.Model):
    id = models.AutoField(primary_key=True)
    cupon = models.ForeignKey(
        Cupon,
        on_delete=models.PROTECT,
        db_column='id_cupon'
    )
    venta = models.ForeignKey(
        Venta,
        on_delete=models.PROTECT,
        db_column='id_venta'
    )
    fecha_uso = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'UsoCupones'
        verbose_name = 'Uso de Cupón'
        verbose_name_plural = 'Usos de Cupones'
        managed = False

    def __str__(self):
        return f"Cupón {self.cupon.codigo} usado en venta #{self.venta.id}"

class ReporteMensualVentas(models.Model):
    id = models.AutoField(primary_key=True)
    anio = models.IntegerField()
    mes = models.IntegerField()
    total_ventas = models.DecimalField(max_digits=12, decimal_places=2)
    total_productos_vendidos = models.IntegerField()
    total_transacciones = models.IntegerField()

    class Meta:
        db_table = 'ReporteMensualVentas'
        verbose_name = 'Reporte Mensual de Ventas'
        verbose_name_plural = 'Reportes Mensuales de Ventas'
        managed = False
        unique_together = ('anio', 'mes')

    def __str__(self):
        return f"Reporte {self.mes}/{self.anio}"

class ReporteMensualProductos(models.Model):
    id = models.AutoField(primary_key=True)
    anio = models.IntegerField()
    mes = models.IntegerField()
    id_producto = models.IntegerField()  # ID del producto en M-Inventario
    cantidad_vendida = models.IntegerField()

    class Meta:
        db_table = 'ReporteMensualProductos'
        verbose_name = 'Reporte Mensual por Producto'
        verbose_name_plural = 'Reportes Mensuales por Producto'
        managed = False

    def __str__(self):
        return f"Reporte Producto {self.id_producto} - {self.mes}/{self.anio}"

class MetasVentas(models.Model):
    id = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        db_column='id_usuario'
    )
    anio = models.IntegerField()
    mes = models.IntegerField()
    monto_meta = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'MetasVentas'
        verbose_name = 'Meta de Ventas'
        verbose_name_plural = 'Metas de Ventas'
        managed = False
        unique_together = ('usuario', 'anio', 'mes')

    def __str__(self):
        return f"Meta {self.usuario.nombre_usuario} - {self.mes}/{self.anio}: ${self.monto_meta}"

class SeguimientoVenta(models.Model):
    id = models.AutoField(primary_key=True)
    venta = models.ForeignKey(
        Venta,
        on_delete=models.PROTECT,
        db_column='id_venta'
    )
    estado_anterior = models.CharField(max_length=50, null=True, blank=True)
    estado_nuevo = models.CharField(max_length=50)
    fecha_cambio = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        db_column='id_usuario'
    )

    class Meta:
        db_table = 'SeguimientoVentas'
        verbose_name = 'Seguimiento de Venta'
        verbose_name_plural = 'Seguimientos de Ventas'
        managed = False

    def __str__(self):
        return f"Seguimiento Venta #{self.venta.id}: {self.estado_anterior} -> {self.estado_nuevo}"

class Notificacion(models.Model):
    id = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        db_column='id_usuario'
    )
    mensaje = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    leido = models.BooleanField(default=False)

    class Meta:
        db_table = 'Notificaciones'
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
        managed = False

    def __str__(self):
        return f"Notificación para {self.usuario.nombre_usuario}: {self.mensaje[:50]}..."
