from django.shortcuts import redirect
from django.urls import reverse
from django.core.cache import cache
from django.conf import settings

class AuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # Cache de rutas públicas para evitar reconstruir la lista en cada petición
        self.public_paths = [
            '/',  # Página principal
            '/login/',
            '/static/',
            '/media/',
            '/catalog/',
            '/api/',
            '/favicon.ico'
        ]

    def __call__(self, request):
        # Optimización: Verificación rápida para rutas estáticas y API
        path = request.path
        if path.startswith('/static/') or path.startswith('/media/') or path.startswith('/api/'):
            return self.get_response(request)
        
        # Verificar si la URL actual es pública usando una comprobación optimizada
        is_public = any(path.startswith(p) for p in self.public_paths)
        
        # Si no está autenticado y la URL no es pública, redirigir a login
        if not is_public and not request.session.get('is_authenticated', False):
            return redirect('login')
            
        response = self.get_response(request)
        return response

class UserDataMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Agregar datos del usuario al request para uso en templates
        if request.session.get('is_authenticated', False):
            request.user = type('User', (), {
                'is_authenticated': True,
                'username': request.session['user']['nombre_usuario'],
                'rol': request.session['user']['rol'],
                'id': request.session['user']['id']
            })
        else:
            request.user = type('AnonymousUser', (), {
                'is_authenticated': False,
                'username': None,
                'rol': None,
                'id': None
            })
            
        response = self.get_response(request)
        return response