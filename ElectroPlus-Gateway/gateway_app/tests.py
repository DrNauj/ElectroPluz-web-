from django.test import TestCase, override_settings
from django.conf import settings
import requests
import json
import os
import logging # Importar el módulo logging

logger = logging.getLogger(__name__)

# Definir una clase de prueba de integración que el script espera
# Debe contener un método que intente conectar con los microservicios.
class IntegrationTests(TestCase):
    """
    Pruebas de integración para verificar la conectividad del Gateway
    con los microservicios M-Inventario y M-Ventas.

    El script 'start_services.ps1' busca esta clase o un método 'integration'.
    """

    # Sobreescribimos las settings para asegurarnos de que estamos usando localhost
    # y los puertos definidos en el script, para que la prueba sea realista.
    @override_settings(MICROSERVICES={
        'INVENTARIO': {'BASE_URL': 'http://localhost:8001/', 'API_KEY': os.getenv('INVENTARIO_API_KEY', 'dev-key')},
        'VENTAS': {'BASE_URL': 'http://localhost:8002/', 'API_KEY': os.getenv('VENTAS_API_KEY', 'dev-key')},
    })
    def test_service_status(self):
        """
        Verifica que los microservicios estén activos y respondan a una solicitud GET simple.
        
        IMPORTANTE: Se asume que /api/status/ es una ruta válida en ambos MS. 
        Si no es así, esta ruta debe ser la más simple y disponible que responda 200 OK.
        """
        # 1. Prueba de conexión a M-Inventario (Puerto 8001)
        inventario_url = f"{settings.MICROSERVICES['INVENTARIO']['BASE_URL']}api/status/"
        logger.info(f"Intentando conectar con M-Inventario en: {inventario_url}")
        try:
            # Usar un endpoint simple para checkear que el servicio está levantado.
            # Se usa el tiempo de espera (timeout) para no colgar la prueba si el servicio no responde.
            response = requests.get(inventario_url, timeout=2)
            # Esperamos que el servicio esté corriendo (código 200)
            self.assertEqual(response.status_code, 200, f"M-Inventario no respondió OK (Status: {response.status_code}) en {inventario_url}")
            print("\n[OK] M-Inventario está activo.")
        except requests.exceptions.RequestException as e:
            self.fail(f"FALLO la conexión con M-Inventario en {inventario_url}. Asegúrese de que el MS está corriendo y tiene el endpoint /api/status/ definido: {e}")

        # 2. Prueba de conexión a M-Ventas (Puerto 8002)
        ventas_url = f"{settings.MICROSERVICES['VENTAS']['BASE_URL']}api/status/"
        logger.info(f"Intentando conectar con M-Ventas en: {ventas_url}")
        try:
            # Usar un endpoint simple para checkear que el servicio está levantado.
            response = requests.get(ventas_url, timeout=2)
            # Esperamos que el servicio esté corriendo (código 200)
            self.assertEqual(response.status_code, 200, f"M-Ventas no respondió OK (Status: {response.status_code}) en {ventas_url}")
            print("[OK] M-Ventas está activo.")
        except requests.exceptions.RequestException as e:
            self.fail(f"FALLO la conexión con M-Ventas en {ventas_url}. Asegúrese de que el MS está corriendo y tiene el endpoint /api/status/ definido: {e}")

# Clase 'mock' para satisfacer la llamada explícita del script de inicio
# 'manage.py test gateway_app.tests.integration'.
class integration(IntegrationTests):
    """Clase para satisfacer la estructura de llamada del script de inicio."""
    def runTest(self):
        """Método dummy para ejecutar la prueba real."""
        self.test_service_status()

# NOTA: Si el error persiste, debe verificar que sus microservicios M-Inventario y M-Ventas
# tienen un endpoint configurado en /api/status/ que devuelve un código 200 OK.
