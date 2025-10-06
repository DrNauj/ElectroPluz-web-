from rest_framework import serializers

class ProductoStockSerializer(serializers.Serializer):
    """Serializer para la vista de productos con stock."""
    id = serializers.IntegerField()
    nombre = serializers.CharField()
    descripcion = serializers.CharField(allow_null=True)
    precio = serializers.DecimalField(max_digits=10, decimal_places=2)
    stock = serializers.IntegerField()
    categoria = serializers.IntegerField()
    categoria_nombre = serializers.CharField()
    estadisticas_ventas = serializers.DictField(required=False)

class DetalleVentaSerializer(serializers.Serializer):
    """Serializer para los detalles de venta."""
    producto_id = serializers.IntegerField()
    cantidad = serializers.IntegerField()
    precio_unitario = serializers.DecimalField(max_digits=10, decimal_places=2)
    producto = serializers.DictField(required=False)

class VentaSerializer(serializers.Serializer):
    """Serializer para las ventas."""
    id = serializers.IntegerField()
    fecha_venta = serializers.DateTimeField()
    total = serializers.DecimalField(max_digits=10, decimal_places=2)
    estado = serializers.CharField()
    cliente = serializers.IntegerField()
    detalles = DetalleVentaSerializer(many=True)