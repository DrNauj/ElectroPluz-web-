from rest_framework import serializers
from .models import Usuario, Cliente, Venta, DetalleVenta, Devolucion, DetalleDevolucion

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['id', 'nombre_usuario', 'rol']
        extra_kwargs = {
            'contrasena': {'write_only': True}
        }

class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = ['id', 'nombres', 'apellidos', 'email', 'telefono', 'direccion']

class DetalleVentaSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetalleVenta
        fields = ['id', 'venta', 'cantidad', 'precio_unitario']

class VentaSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.CharField(source='cliente.nombres', read_only=True)
    usuario_nombre = serializers.CharField(source='usuario.nombre_usuario', read_only=True)
    detalles = DetalleVentaSerializer(many=True, read_only=True, source='detalleventa_set')

    class Meta:
        model = Venta
        fields = [
            'id', 'fecha_venta', 'total', 'estado',
            'cliente', 'cliente_nombre',
            'usuario', 'usuario_nombre',
            'detalles'
        ]

class DetalleDevolucionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetalleDevolucion
        fields = ['id', 'devolucion', 'cantidad_devuelta']

class DevolucionSerializer(serializers.ModelSerializer):
    detalles = DetalleDevolucionSerializer(many=True, read_only=True, source='detalledevolucion_set')

    class Meta:
        model = Devolucion
        fields = ['id', 'venta', 'fecha_devolucion', 'motivo', 'detalles']

# Serializers para crear nuevas ventas
class DetalleVentaCreateSerializer(serializers.ModelSerializer):
    id_producto = serializers.IntegerField(write_only=True)

    class Meta:
        model = DetalleVenta
        fields = ['id_producto', 'cantidad', 'precio_unitario']

class VentaCreateSerializer(serializers.ModelSerializer):
    detalles = DetalleVentaCreateSerializer(many=True, write_only=True)

    class Meta:
        model = Venta
        fields = ['cliente', 'estado', 'detalles']

    def create(self, validated_data):
        detalles_data = validated_data.pop('detalles')
        venta = Venta.objects.create(**validated_data)
        
        for detalle_data in detalles_data:
            DetalleVenta.objects.create(venta=venta, **detalle_data)
        
        return venta