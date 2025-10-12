from rest_framework import serializers
from .models_cupones import Cupon, UsoCupon

class CuponSerializer(serializers.ModelSerializer):
    esta_activo = serializers.BooleanField(read_only=True)
    producto_nombre = serializers.CharField(source='valido_para_producto.nombre', read_only=True)

    class Meta:
        model = Cupon
        fields = [
            'id', 'codigo', 'tipo_descuento', 'valor',
            'fecha_inicio', 'fecha_fin', 'valido_para_producto',
            'esta_activo', 'producto_nombre'
        ]
        read_only_fields = ['id']

    def validate(self, data):
        # Validar que fecha_fin sea posterior a fecha_inicio
        if 'fecha_fin' in data and 'fecha_inicio' in data:
            if data['fecha_fin'] <= data['fecha_inicio']:
                raise serializers.ValidationError({
                    'fecha_fin': 'La fecha de fin debe ser posterior a la fecha de inicio'
                })
                
        # Validar valor según tipo de descuento
        if 'tipo_descuento' in data and 'valor' in data:
            if data['tipo_descuento'] == 'Porcentaje' and data['valor'] > 100:
                raise serializers.ValidationError({
                    'valor': 'El porcentaje no puede ser mayor a 100%'
                })
            if data['valor'] <= 0:
                raise serializers.ValidationError({
                    'valor': 'El valor debe ser mayor que 0'
                })
                
        return data

class UsoCuponSerializer(serializers.ModelSerializer):
    codigo_cupon = serializers.CharField(source='cupon.codigo', read_only=True)
    
    class Meta:
        model = UsoCupon
        fields = ['id', 'cupon', 'id_venta', 'fecha_uso', 'codigo_cupon']
        read_only_fields = ['id', 'fecha_uso']  # fecha_uso se establece automáticamente