import unittest
import requests
import responses
from django.conf import settings

class IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Configuración inicial de los mocks."""
        super().setUpClass()
        responses.start()
        
    @classmethod
    def tearDownClass(cls):
        """Limpieza de los mocks."""
        super().tearDownClass()
        responses.stop()
    def setUp(self):
        """Configura las URLs, datos de prueba y limpia los mocks."""
        responses.reset()
        self.gateway_url = "http://localhost:8000/api"
        self.inventario_url = "http://localhost:8001/api"
        self.ventas_url = "http://localhost:8002/api"
        
        # Datos de prueba
        self.producto_test = {
            "nombre": "Producto Test",
            "descripcion": "Producto para pruebas de integración",
            "precio": 100.00,
            "stock": 10
        }
        
        self.venta_test = {
            "cliente": 1,
            "productos": [{"id": 1, "cantidad": 2}]
        }
        
        # Configurar respuestas mock por defecto
        responses.add(
            responses.GET,
            f"{self.gateway_url}/swagger/",
            json={"status": "ok"},
            status=200
        )
        responses.add(
            responses.GET,
            f"{self.inventario_url}/productos/",
            json=[],
            status=200
        )
        responses.add(
            responses.GET,
            f"{self.ventas_url}/ventas/",
            json=[],
            status=200
        )

    def test_conexion_servicios(self):
        """Verifica que todos los servicios estén en línea."""
        # Las respuestas ya están configuradas en setUp()
        gateway = requests.get(f"{self.gateway_url}/swagger/")
        self.assertEqual(gateway.status_code, 200)
        
        inventario = requests.get(f"{self.inventario_url}/productos/")
        self.assertEqual(inventario.status_code, 200)
        
        ventas = requests.get(f"{self.ventas_url}/ventas/")
        self.assertEqual(ventas.status_code, 200)

    def test_flujo_venta(self):
        """Prueba el flujo completo de una venta usando mocks."""
        # Configurar respuestas mock para el flujo de venta
        stock_inicial = 10
        responses.add(
            responses.GET,
            f"{self.inventario_url}/productos/1/",
            json={"id": 1, "nombre": "Producto Test", "stock": stock_inicial},
            status=200
        )
        
        responses.add(
            responses.POST,
            f"{self.gateway_url}/realizar-venta/",
            json={"id": 1, "estado": "completada"},
            status=201
        )
        
        responses.add(
            responses.GET,
            f"{self.inventario_url}/productos/1/",
            json={"id": 1, "nombre": "Producto Test", "stock": stock_inicial - 2},
            status=200
        )
        
        # 1. Verificar stock inicial
        resp = requests.get(f"{self.inventario_url}/productos/1/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["stock"], stock_inicial)
        
        # 2. Realizar venta
        resp = requests.post(f"{self.gateway_url}/realizar-venta/", json=self.venta_test)
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.json()["estado"], "completada")
        
        # 3. Verificar reducción de stock
        resp = requests.get(f"{self.inventario_url}/productos/1/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["stock"], stock_inicial - 2)

    def test_manejo_errores(self):
        """Prueba el manejo de errores como stock insuficiente o producto no encontrado."""
        # 1. Escenario: Stock insuficiente
        stock_inicial = 1
        responses.add(
            responses.GET,
            f"{self.inventario_url}/productos/1/",
            json={"id": 1, "nombre": "Producto Test", "stock": stock_inicial},
            status=200
        )
        responses.add(
            responses.POST,
            f"{self.gateway_url}/realizar-venta/",
            json={"error": "Stock insuficiente"},
            status=400
        )

        # Intentar realizar venta con cantidad mayor al stock
        venta_stock_insuficiente = {
            "cliente": 1,
            "productos": [{"id": 1, "cantidad": 5}]
        }
        resp = requests.post(f"{self.gateway_url}/realizar-venta/", json=venta_stock_insuficiente)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("insuficiente", resp.json().get("error", "").lower())

        # Verificar que el stock no cambió
        resp_stock = requests.get(f"{self.inventario_url}/productos/1/")
        self.assertEqual(resp_stock.json()["stock"], stock_inicial)

        # 2. Escenario: Producto no encontrado
        responses.reset()  # Limpiar mocks anteriores
        responses.add(
            responses.POST,
            f"{self.gateway_url}/realizar-venta/",
            json={"error": "Producto no encontrado"},
            status=404
        )
        
        venta_producto_inexistente = {
            "cliente": 1,
            "productos": [{"id": 999, "cantidad": 1}]
        }
        resp = requests.post(f"{self.gateway_url}/realizar-venta/", json=venta_producto_inexistente)
        self.assertEqual(resp.status_code, 404)
        self.assertIn("no encontrado", resp.json().get("error", "").lower())

if __name__ == '__main__':
    unittest.main()