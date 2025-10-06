import pytest
from django.test.client import RequestFactory
from gateway_app.views import GatewayViewSet
from rest_framework.test import APITestCase
import responses

class TestGatewayAPI(APITestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.gateway_viewset = GatewayViewSet()

    @responses.activate
    def test_get_productos_stock(self):
        """Prueba la obtención de productos con su stock."""
        # Simular respuesta del servicio de inventario
        responses.add(
            responses.GET,
            'http://localhost:8001/api/productos/',
            json=[{
                'id': 1,
                'nombre': 'Producto Test',
                'stock': 10,
                'precio': 100.00
            }],
            status=200
        )

        # Ejecutar prueba
        request = self.factory.get('/api/gateway/productos-stock/')
        response = self.gateway_viewset.productos_stock(request)

        # Verificar respuesta
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['nombre'], 'Producto Test')

    @responses.activate
    def test_resumen_cliente(self):
        """Prueba la obtención del resumen de un cliente."""
        # Simular respuesta del servicio de ventas
        responses.add(
            responses.GET,
            'http://localhost:8002/api/ventas/cliente/1/',
            json=[{
                'id': 1,
                'fecha': '2025-10-06',
                'total': 200.00,
                'detalle': [{'producto': 1, 'cantidad': 2}]
            }],
            status=200
        )

        # Simular respuesta del servicio de inventario
        responses.add(
            responses.GET,
            'http://localhost:8001/api/productos/1/',
            json={
                'id': 1,
                'nombre': 'Producto Test',
                'precio': 100.00
            },
            status=200
        )

        # Ejecutar prueba
        request = self.factory.get('/api/gateway/1/resumen-cliente/')
        response = self.gateway_viewset.resumen_cliente(request, id=1)

        # Verificar respuesta
        self.assertEqual(response.status_code, 200)
        self.assertIn('ventas', response.data)
        self.assertEqual(len(response.data['ventas']), 1)
        self.assertEqual(response.data['ventas'][0]['total'], 200.00)

    @responses.activate
    def test_error_handling(self):
        """Prueba el manejo de errores del gateway."""
        # Simular error 500 del servicio de inventario
        responses.add(
            responses.GET,
            'http://localhost:8001/api/productos/',
            json={'error': 'Error interno del servidor'},
            status=500
        )

        # Ejecutar prueba
        request = self.factory.get('/api/gateway/productos-stock/')
        response = self.gateway_viewset.productos_stock(request)

        # Verificar manejo del error
        self.assertEqual(response.status_code, 500)
        self.assertIn('error', response.data)