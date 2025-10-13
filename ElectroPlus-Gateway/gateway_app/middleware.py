from django.shortcuts import redirect
from django.urls import reverse
from django.core.cache import cache
from django.conf import settings

class AuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Cache de rutas públicas usando un set para O(1) lookup
        self.public_paths = {
            '/',  # Página principal
            '/auth/login/',
            '/auth/register/',
            '/static/',
            '/media/',
            '/catalog/',
            '/api/auth/',
            '/favicon.ico'
        }
        
        # Cache de prefijos comunes para evitar splits
        self.public_prefixes = frozenset([
            '/static/',
            '/media/',
            '/api/auth/',
            '/catalog/',
            '/auth/'
        ])
        
        # Compilar una vez las rutas base
        self.auth_url = '/auth/login/'

    def __call__(self, request):
        path = request.path.rstrip('/')
        
        # Fast path: verificar prefijos comunes primero usando frozenset
        if any(path.startswith(prefix) for prefix in self.public_prefixes):
            return self.get_response(request)
            
        # Second fast path: verificar rutas exactas con set
        if path in self.public_paths:
            return self.get_response(request)
            
        # Si no está autenticado, continuar (el modal de login se mostrará en el frontend)
        if not request.session.get('is_authenticated', False):
            return self.get_response(request)
            
        return self.get_response(request)

class UserDataMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # Crear una instancia de usuario anónimo una sola vez
        self.anonymous_user = type('AnonymousUser', (), {
            'is_authenticated': False,
            'username': None,
            'rol': None,
            'id': None,
            '__bool__': lambda self: False  # Para que if user sea False
        })

    def __call__(self, request):
        # Fast path: si no está autenticado, usar usuario anónimo pre-creado
        if not request.session.get('is_authenticated', False):
            request.user = self.anonymous_user
            return self.get_response(request)
        
        # Solo crear objeto de usuario si está autenticado
        user_data = request.session.get('user', {})
        request.user = type('User', (), {
            'is_authenticated': True,
            'username': user_data.get('nombre_usuario'),
            'rol': user_data.get('rol'),
            'id': user_data.get('id'),
            '__bool__': lambda self: True  # Para que if user sea True
        })
            
        return self.get_response(request)