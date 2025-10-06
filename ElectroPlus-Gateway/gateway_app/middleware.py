from django.shortcuts import redirect
from django.urls import reverse

class AuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # URLs que no requieren autenticación
        public_paths = [
            '/',  # Página principal
            '/login/',
            '/static/',
            '/media/',
            '/catalog/',
            '/api/',
            '/favicon.ico'
        ]
        
        # Verificar si la URL actual es pública
        is_public = any(request.path.startswith(path) for path in public_paths)
        
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