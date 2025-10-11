from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch
import json
import requests
from rest_framework import status

class AuthenticationIntegrationTest(TestCase):
    """Pruebas de integración para el flujo de autenticación."""
    
    def setUp(self):
        self.client = Client()
        self.login_url = reverse('auth:login')
        self.register_url = reverse('auth:register')
        
    @patch('gateway_app.views.requests.post')
    def test_successful_login(self, mock_post):
        """Prueba un login exitoso."""
        # Simular respuesta exitosa del microservicio
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'id': 1,
            'nombre_usuario': 'test_user',
            'token': 'test_token',
            'rol': 'cliente'
        }
        
        response = self.client.post(
            self.login_url,
            {'username': 'test_user', 'password': 'test_pass'},
            follow=True
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.client.session.get('is_authenticated', False))
        self.assertIsNotNone(self.client.session.get('user'))
        
    @patch('gateway_app.views.requests.post')
    def test_failed_login(self, mock_post):
        """Prueba un login fallido."""
        # Simular respuesta de error del microservicio
        mock_post.return_value.status_code = 401
        mock_post.return_value.json.return_value = {
            'error': 'Credenciales inválidas'
        }
        
        response = self.client.post(
            self.login_url,
            {'username': 'bad_user', 'password': 'bad_pass'},
            follow=True
        )
        
        self.assertEqual(response.status_code, 200)  # La vista siempre retorna 200
        self.assertFalse(self.client.session.get('is_authenticated', False))
        
    @patch('gateway_app.views.requests.post')
    def test_register_flow(self, mock_post):
        """Prueba el flujo completo de registro."""
        # Simular respuesta exitosa del microservicio
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {
            'id': 1,
            'nombre_usuario': 'new_user'
        }
        
        response = self.client.post(
            self.register_url,
            {
                'username': 'new_user',
                'password1': 'secure_pass123',
                'password2': 'secure_pass123',
                'email': 'new@user.com'
            },
            follow=True
        )
        
        self.assertEqual(response.status_code, 200)
        # Verificar redirección a login después de registro exitoso
        self.assertRedirects(response, reverse('auth:login'))
        
    @patch('gateway_app.views.requests.post')
    def test_microservice_timeout(self, mock_post):
        """Prueba el manejo de timeout del microservicio."""
        # Simular timeout
        mock_post.side_effect = requests.exceptions.Timeout
        
        response = self.client.post(
            self.login_url,
            {'username': 'test_user', 'password': 'test_pass'},
            follow=True
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.client.session.get('is_authenticated', False))
        # Verificar mensaje de error
        messages = list(response.context['messages'])
        self.assertTrue(any('Error de conexión' in str(m) for m in messages))