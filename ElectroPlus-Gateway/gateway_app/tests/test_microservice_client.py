"""
Tests para el cliente de microservicios.
"""
from django.test import TestCase
from django.conf import settings
from unittest.mock import patch, Mock
import requests
from ..services.microservice_client import (
    MicroserviceClient,
    MicroserviceConnectionError,
    with_retry
)

class MicroserviceClientTest(TestCase):
    """Pruebas para el cliente de microservicios."""
    
    def setUp(self):
        self.client = MicroserviceClient('INVENTARIO')
        
    def test_invalid_service_name(self):
        """Prueba que se lance error con nombre de servicio inválido."""
        with self.assertRaises(ValueError):
            MicroserviceClient('INVALID_SERVICE')
            
    @patch('requests.get')
    def test_successful_get(self, mock_get):
        """Prueba una petición GET exitosa."""
        expected_data = {'status': 'ok'}
        mock_get.return_value = Mock(
            status_code=200,
            json=lambda: expected_data
        )
        
        result = self.client.get('test-endpoint')
        self.assertEqual(result, expected_data)
        
        # Verificar que se llamó con los headers correctos
        mock_get.assert_called_once()
        headers = mock_get.call_args[1]['headers']
        self.assertEqual(headers['X-API-Key'], settings.MICROSERVICES['INVENTARIO']['API_KEY'])
        
    @patch('requests.get')
    def test_retry_on_timeout(self, mock_get):
        """Prueba que se reintente en caso de timeout."""
        mock_get.side_effect = [
            requests.exceptions.Timeout(),  # Primer intento
            requests.exceptions.Timeout(),  # Segundo intento
            Mock(status_code=200, json=lambda: {'status': 'ok'})  # Tercer intento exitoso
        ]
        
        result = self.client.get('test-endpoint')
        self.assertEqual(result, {'status': 'ok'})
        self.assertEqual(mock_get.call_count, 3)
        
    @patch('requests.post')
    def test_post_with_data(self, mock_post):
        """Prueba una petición POST con datos."""
        test_data = {'key': 'value'}
        expected_response = {'id': 1}
        
        mock_post.return_value = Mock(
            status_code=201,
            json=lambda: expected_response
        )
        
        result = self.client.post('test-endpoint', test_data)
        self.assertEqual(result, expected_response)
        
        # Verificar que se envió el payload correcto
        mock_post.assert_called_once()
        self.assertEqual(mock_post.call_args[1]['json'], test_data)
        
    @patch('requests.get')
    def test_http_error_handling(self, mock_get):
        """Prueba el manejo de errores HTTP."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_get.side_effect = requests.exceptions.HTTPError(response=mock_response)
        
        with self.assertRaises(MicroserviceConnectionError):
            self.client.get('test-endpoint')
            
    def test_retry_decorator(self):
        """Prueba el decorador with_retry."""
        counter = {'attempts': 0}
        
        @with_retry(max_retries=3)
        def test_function():
            counter['attempts'] += 1
            if counter['attempts'] < 3:
                raise requests.exceptions.Timeout()
            return 'success'
            
        result = test_function()
        self.assertEqual(result, 'success')
        self.assertEqual(counter['attempts'], 3)  # Verificar que se intentó 3 veces