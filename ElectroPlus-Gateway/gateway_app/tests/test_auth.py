import pytest
from django.test import Client, TestCase
from django.urls import reverse
from django.contrib.auth.models import User, Group
from gateway_app.models import Employee, Customer
from unittest.mock import patch

class AuthenticationTest(TestCase):
    def setUp(self):
        self.client = Client()
        # Configurar respuestas simuladas para el servicio de ventas
        self.auth_patcher = patch('gateway_app.views.authenticate_with_service')
        self.mock_auth = self.auth_patcher.start()
        
    def tearDown(self):
        self.auth_patcher.stop()

    def test_login_employee(self):
        """Prueba de inicio de sesión como empleado"""
        # Configurar mock de autenticación
        self.mock_auth.return_value = {
            'id': 1,
            'nombre_usuario': 'EMP001',
            'rol': 'empleado',
            'token': 'test_token'
        }
        
        response = self.client.post(reverse('login'), {
            'nombre_usuario': '001',  # Se convertirá a EMP001
            'contrasena': 'Employee123!',
            'user_type': 'employee'
        })
        self.assertRedirects(response, reverse('employee_dashboard'))
        
        # Verificar datos de sesión
        self.assertTrue(self.client.session.get('is_authenticated', False))
        self.assertEqual(self.client.session['user']['rol'], 'empleado')

    def test_login_customer(self):
        """Prueba de inicio de sesión como cliente"""
        # Configurar mock de autenticación
        self.mock_auth.return_value = {
            'id': 2,
            'nombre_usuario': 'customer_test',
            'rol': 'cliente',
            'token': 'test_token'
        }
        
        response = self.client.post(reverse('login'), {
            'nombre_usuario': 'customer_test',
            'contrasena': 'Customer123!',
            'user_type': 'customer'
        })
        self.assertRedirects(response, reverse('customer_dashboard'))
        
        # Verificar datos de sesión
        self.assertTrue(self.client.session.get('is_authenticated', False))
        self.assertEqual(self.client.session['user']['rol'], 'cliente')

    def test_invalid_login(self):
        """Prueba de inicio de sesión con credenciales inválidas"""
        # Configurar mock para retornar None (fallo de autenticación)
        self.mock_auth.return_value = None
        
        response = self.client.post(reverse('login'), {
            'nombre_usuario': 'invalid_user',
            'contrasena': 'invalid_pass'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Usuario o contraseña incorrectos')
        
        # Verificar que no hay sesión
        self.assertFalse(self.client.session.get('is_authenticated', False))

    def test_employee_id_format(self):
        """Prueba del formato de ID de empleado"""
        self.mock_auth.return_value = {
            'id': 1,
            'nombre_usuario': 'EMP001',
            'rol': 'empleado',
            'token': 'test_token'
        }
        
        # Sin prefijo EMP
        response = self.client.post(reverse('login'), {
            'nombre_usuario': '001',
            'contrasena': 'pass123',
            'user_type': 'employee'
        })
        self.assertRedirects(response, reverse('employee_dashboard'))
        self.assertEqual(
            self.mock_auth.call_args[0][0], 
            'EMP001'
        )
        
        # Con prefijo EMP
        response = self.client.post(reverse('login'), {
            'nombre_usuario': 'EMP002',
            'contrasena': 'pass123',
            'user_type': 'employee'
        })
        self.assertRedirects(response, reverse('employee_dashboard'))
        self.assertEqual(
            self.mock_auth.call_args[0][0], 
            'EMP002'
        )

    def test_remember_me(self):
        """Prueba de la funcionalidad 'recordarme'"""
        self.mock_auth.return_value = {
            'id': 2,
            'nombre_usuario': 'customer_test',
            'rol': 'cliente',
            'token': 'test_token'
        }
        
        # Sin recordar sesión
        response = self.client.post(reverse('login'), {
            'nombre_usuario': 'customer_test',
            'contrasena': 'Customer123!',
            'user_type': 'customer',
            'remember': ''
        })
        self.assertEqual(self.client.session.get_expiry_age(), 0)
        
        # Con recordar sesión
        self.client.post(reverse('login'), {
            'nombre_usuario': 'customer_test',
            'contrasena': 'Customer123!',
            'user_type': 'customer',
            'remember': 'on'
        })
        self.assertGreater(self.client.session.get_expiry_age(), 0)

    def test_wrong_user_type(self):
        """Prueba de inicio de sesión con tipo de usuario incorrecto"""
        self.mock_auth.return_value = {
            'id': 2,
            'nombre_usuario': 'customer_test',
            'rol': 'cliente',  # El rol no coincide con el tipo solicitado
            'token': 'test_token'
        }
        
        response = self.client.post(reverse('login'), {
            'nombre_usuario': 'customer_test',
            'contrasena': 'Customer123!',
            'user_type': 'employee'  # Intenta acceder como empleado
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tipo de usuario incorrecto')

    def test_logout(self):
        """Prueba de cierre de sesión"""
        # Configurar mock de autenticación para el login
        self.mock_auth.return_value = {
            'id': 2,
            'nombre_usuario': 'customer_test',
            'rol': 'cliente',
            'token': 'test_token'
        }
        
        # Iniciar sesión primero
        self.client.post(reverse('login'), {
            'nombre_usuario': 'customer_test',
            'contrasena': 'Customer123!',
            'user_type': 'customer'
        })
        
        # Verificar que está autenticado
        self.assertTrue(self.client.session.get('is_authenticated', False))
        
        # Cerrar sesión
        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, reverse('login'))
        
        # Verificar que la sesión fue limpiada
        self.assertNotIn('is_authenticated', self.client.session)
        self.assertNotIn('user', self.client.session)
        self.assertRedirects(response, reverse('dashboard'))

    def test_invalid_login(self):
        """Prueba de inicio de sesión con credenciales inválidas"""
        response = self.client.post(reverse('login'), {
            'username': 'invalid_user',
            'password': 'invalid_pass'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Usuario o contraseña incorrectos')

    def test_logout(self):
        """Prueba de cierre de sesión"""
        # Iniciar sesión primero
        self.client.login(username='customer_test', password='Customer123!')
        
        # Verificar que está autenticado
        response = self.client.get(reverse('customer_dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Cerrar sesión
        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, reverse('login'))
        
        # Verificar que ya no puede acceder al dashboard
        response = self.client.get(reverse('customer_dashboard'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('customer_dashboard')}")

    def test_remember_me(self):
        """Prueba de la funcionalidad 'recordarme'"""
        # Sin recordar sesión
        response = self.client.post(reverse('login'), {
            'username': 'customer_test',
            'password': 'Customer123!',
            'remember': ''
        })
        self.assertEqual(self.client.session.get_expiry_age(), 0)
        
        # Con recordar sesión
        self.client.logout()
        response = self.client.post(reverse('login'), {
            'username': 'customer_test',
            'password': 'Customer123!',
            'remember': 'on'
        })
        self.assertGreater(self.client.session.get_expiry_age(), 0)

    def test_auth_api(self):
        """Prueba del endpoint de verificación de autenticación"""
        # Sin autenticar
        response = self.client.get(reverse('check_auth'))
        self.assertEqual(response.status_code, 302)  # Redirecciona al login
        
        # Como administrador
        self.client.login(username='admin_test', password='Admin123!')
        response = self.client.get(reverse('check_auth'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['user_type'], 'admin')
        self.assertTrue(data['is_authenticated'])