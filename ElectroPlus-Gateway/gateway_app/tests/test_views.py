import pytest
from django.test import Client, TestCase
from django.urls import reverse
from unittest.mock import patch, MagicMock
import json

class ViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        # Configurar patcher para requests
        self.requests_patcher = patch('gateway_app.views.requests')
        self.mock_requests = self.requests_patcher.start()
        
        # Configurar patcher para autenticación
        self.auth_patcher = patch('gateway_app.views.authenticate_with_service')
        self.mock_auth = self.auth_patcher.start()

    def tearDown(self):
        self.requests_patcher.stop()
        self.auth_patcher.stop()

    def test_home_view(self):
        """Prueba de la vista principal"""
        # Configurar mock para obtener productos
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                'id': 1,
                'nombre': 'Producto 1',
                'precio': 100.0,
                'categoria': 1,
                'descripcion': 'Descripción 1'
            },
            {
                'id': 2,
                'nombre': 'Producto 2',
                'precio': 200.0,
                'categoria': 2,
                'descripcion': 'Descripción 2'
            }
        ]
        self.mock_requests.get.return_value = mock_response
        
        # Probar vista principal
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'shop/home.html')
        self.assertIn('products', response.context)
        
        # Probar filtros y ordenamiento
        response = self.client.get(reverse('home') + '?category=1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['products']), 1)
        
        response = self.client.get(reverse('home') + '?sort=price_high')
        self.assertEqual(response.status_code, 200)
        products = response.context['products']
        self.assertEqual(products[0]['precio'], 200.0)
        
        # Probar error de servicio
        self.mock_requests.get.side_effect = Exception('Error de conexión')
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['error'])

    def test_dashboard_view(self):
        """Prueba de la vista del dashboard principal"""
        # Configurar autenticación
        self.mock_auth.return_value = {
            'id': 1,
            'nombre_usuario': 'EMP001',
            'rol': 'empleado',
            'token': 'test_token'
        }
        
        # Iniciar sesión
        self.client.post(reverse('login'), {
            'nombre_usuario': 'EMP001',
            'contrasena': 'pass123',
            'user_type': 'employee'
        })
        
        # Configurar mock para estadísticas
        mock_ventas = MagicMock()
        mock_ventas.status_code = 200
        mock_ventas.json.return_value = {
            'ventas_totales': 1000,
            'clientes_nuevos': 5,
            'productos_vendidos': 20
        }
        
        mock_inventario = MagicMock()
        mock_inventario.status_code = 200
        mock_inventario.json.return_value = {
            'productos_totales': 100,
            'stock_bajo': 10,
            'valor_inventario': 50000
        }
        
        def side_effect(url, **kwargs):
            if 'ventas' in url:
                return mock_ventas
            return mock_inventario
            
        self.mock_requests.get.side_effect = side_effect
        
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'base/dashboard.html')
        self.assertIn('stats_ventas', response.context)
        self.assertIn('stats_inventario', response.context)
        
        # Probar error en servicios
        self.mock_requests.get.side_effect = Exception('Error de conexión')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('error', response.context)

    def test_registration_view(self):
        """Prueba de la vista de registro"""
        # GET request
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'auth/register.html')
        
        # Configurar mock para registro exitoso
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {'id': 1}
        self.mock_requests.post.return_value = mock_response
        
        # POST request válido
        data = {
            'nombre': 'Nuevo Cliente',
            'email': 'new@customer.com',
            'username': 'new_customer',
            'password1': 'NewCustomer123!',
            'password2': 'NewCustomer123!'
        }
        response = self.client.post(reverse('register'), data)
        self.assertRedirects(response, reverse('login'))
        
        # Verificar datos enviados al servicio
        self.mock_requests.post.assert_called_once()
        call_data = self.mock_requests.post.call_args[1]['json']
        self.assertEqual(call_data['nombre'], 'Nuevo Cliente')
        self.assertEqual(call_data['email'], 'new@customer.com')
        
        # Probar error del servicio
        mock_response.status_code = 400
        mock_response.json.return_value = {'detail': 'Error en datos'}
        response = self.client.post(reverse('register'), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Error en datos')

    def test_profile_view(self):
        """Prueba de la vista de perfil"""
        # Configurar autenticación
        self.mock_auth.return_value = {
            'id': 1,
            'nombre_usuario': 'customer_test',
            'rol': 'cliente',
            'token': 'test_token'
        }
        
        # Iniciar sesión
        self.client.post(reverse('login'), {
            'nombre_usuario': 'customer_test',
            'contrasena': 'Customer123!',
            'user_type': 'customer'
        })
        
        # Configurar mock para obtener datos del perfil
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': 1,
            'nombre': 'Cliente Test',
            'email': 'customer@test.com',
            'telefono': '555-TEST',
            'direccion': 'Test Address'
        }
        self.mock_requests.get.return_value = mock_response
        
        # GET request
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profile/profile.html')
        
        # Configurar mock para actualización
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': 1,
            'nombre': 'Cliente Test',
            'email': 'updated@customer.com',
            'telefono': '555-UPDATED',
            'direccion': 'Updated Address'
        }
        self.mock_requests.put.return_value = mock_response
        
        # Actualizar perfil
        data = {
            'email': 'updated@customer.com',
            'telefono': '555-UPDATED',
            'direccion': 'Updated Address'
        }
        response = self.client.post(reverse('profile'), data)
        self.assertEqual(response.status_code, 200)
        
        # Verificar datos enviados al servicio
        self.mock_requests.put.assert_called_once()
        call_data = self.mock_requests.put.call_args[1]['json']
        self.assertEqual(call_data['email'], 'updated@customer.com')
        self.assertEqual(call_data['telefono'], '555-UPDATED')