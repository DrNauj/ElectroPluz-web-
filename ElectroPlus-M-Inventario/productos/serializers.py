from rest_framework import serializers
from .models import Categoria, Proveedor, Producto, HistorialInventario


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ['id', 'nombre', 'descripcion']


class ProveedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proveedor
        fields = ['id', 'nombre', 'direccion', 'telefono', 'email']


class HistorialInventarioSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)

    class Meta:
        model = HistorialInventario
        fields = [
            'id', 'producto', 'producto_nombre',
            'tipo_movimiento', 'cantidad', 'fecha', 'usuario', 'request_id'
        ]


class ProductoSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)
    proveedor_nombre = serializers.CharField(source='proveedor.nombre', read_only=True)

    class Meta:
        model = Producto
        fields = [
            'id', 'nombre', 'descripcion', 'precio', 'stock',
            'categoria', 'categoria_nombre',
            'proveedor', 'proveedor_nombre'
        ]

    def validate(self, data):
        # Validación del precio
        if 'precio' in data and data['precio'] is not None and data['precio'] <= 0:
            raise serializers.ValidationError({
                'precio': 'El precio debe ser mayor que 0.'
            })

        # Validación del stock
        if 'stock' in data and data['stock'] is not None and data['stock'] < 0:
            raise serializers.ValidationError({
                'stock': 'El stock no puede ser negativo.'
            })

        # Validación de categoría (data puede contener PK o instancia)
        categoria = data.get('categoria')
        if categoria is not None:
            cat_id = getattr(categoria, 'id', categoria)
            if not Categoria.objects.filter(id=cat_id).exists():
                raise serializers.ValidationError({'categoria': 'La categoría especificada no existe.'})

        # Validación de proveedor
        proveedor = data.get('proveedor')
        if proveedor is not None:
            prov_id = getattr(proveedor, 'id', proveedor)
            if not Proveedor.objects.filter(id=prov_id).exists():
                raise serializers.ValidationError({'proveedor': 'El proveedor especificado no existe.'})

        return data


class ProductoDetalladoSerializer(ProductoSerializer):
    categoria = CategoriaSerializer(read_only=True)
    proveedor = ProveedorSerializer(read_only=True)
    historial = serializers.SerializerMethodField()

    class Meta(ProductoSerializer.Meta):
        fields = ProductoSerializer.Meta.fields + ['categoria', 'proveedor', 'historial']

    def get_historial(self, obj):
        # Usar el campo correcto 'fecha' del modelo HistorialInventario
        historial = HistorialInventario.objects.filter(producto=obj).order_by('-fecha')[:10]
        return HistorialInventarioSerializer(historial, many=True).data