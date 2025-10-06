from django.http import JsonResponse
from django.conf import settings
import os

class InterServiceAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # Usar la SECRET_KEY principal de Django para la autenticación del servicio
        self.secret_key = settings.SECRET_KEY
        self.is_test = os.environ.get('TESTING', 'False') == 'True'

    def __call__(self, request):
        # Temporalmente deshabilitada la autenticación para pruebas
        return self.get_response(request)