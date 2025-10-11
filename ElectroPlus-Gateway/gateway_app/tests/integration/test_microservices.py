import unittest
from django.test import TestCase
from django.conf import settings
import requests
import responses
from unittest.mock import patch

class MicroservicesConnectionTest(TestCase):
    """Pruebas de integración para la conexión con microservicios."""
    
    def setUp(self):
        """Configuración inicial para las pruebas."""
        self.inventario_url = settings.MICROSERVICES['INVENTARIO']['BASE_URL']
        self.ventas_url = settings.MICROSERVICES['VENTAS']['BASE_URL']
        
    def test_inventario_connection(self):
        """Prueba la conexión al microservicio de Inventario."""
        try:
            response = requests.get(
                f"{self.inventario_url}health/",
                headers={'X-API-Key': settings.MICROSERVICES['INVENTARIO']['API_KEY']},
                timeout=5
            )
            self.assertEqual(response.status_code, 200)
            self.assertIn('status', response.json())
        except requests.RequestException as e:
            self.fail(f"Error de conexión con Inventario: {str(e)}")
            
    def test_ventas_connection(self):
        """Prueba la conexión al microservicio de Ventas."""
        try:
            response = requests.get(
                f"{self.ventas_url}health/",
                headers={'X-API-Key': settings.MICROSERVICES['VENTAS']['API_KEY']},
                timeout=5
            )
            self.assertEqual(response.status_code, 200)
            self.assertIn('status', response.json())
        except requests.RequestException as e:
            self.fail(f"Error de conexión con Ventas: {str(e)}")
            
    @responses.activate
    def test_inventario_error_handling(self):
        """Prueba el manejo de errores en la conexión con Inventario."""
        # Simular error 500
        responses.add(
            responses.GET,
            f"{self.inventario_url}products/",
            json={"error": "Internal Server Error"},
            status=500
        )
        
        with self.assertRaises(requests.exceptions.HTTPError):
            response = requests.get(
                f"{self.inventario_url}products/",
                headers={'X-API-Key': settings.MICROSERVICES['INVENTARIO']['API_KEY']}
            )
            response.raise_for_status()
            
    @patch('requests.get')
    def test_timeout_handling(self, mock_get):
        """Prueba el manejo de timeouts en las conexiones."""
        mock_get.side_effect = requests.exceptions.Timeout
        
        with self.assertRaises(requests.exceptions.Timeout):
            requests.get(
                f"{self.inventario_url}products/",
                headers={'X-API-Key': settings.MICROSERVICES['INVENTARIO']['API_KEY']},
                timeout=5
            )