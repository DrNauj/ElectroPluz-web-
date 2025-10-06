from django.test import TestCase


class SmokeTestInventory(TestCase):
    def test_smoke(self):
        """Prueba mínima para asegurar que el runner de tests reconoce el archivo."""
        self.assertTrue(True)
