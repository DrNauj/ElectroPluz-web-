"""
Django settings for gateway_core project.
"""

from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
# Cargar variables de entorno desde el .env
load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = True
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Aplicaciones del Gateway
    'gateway_app', # Lógica de autenticación y base del gateway (core)
    'storefront',  # Frontend público (tienda)
    'inventory', # Frontend administrativo (dashboard)
    # NOTA: 'sales' ha sido eliminada.
    
    # Librerías externas
    'rest_framework',
    'debug_toolbar',
]

# Middleware Configuration
MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Middlewares personalizados
    'gateway_app.middleware.AuthenticationMiddleware',
    'gateway_app.middleware.UserDataMiddleware',
]

ROOT_URLCONF = 'gateway_core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'], # Directorio global de templates
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'gateway_core.wsgi.application'


# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'America/Lima' # Ajustado a la zona horaria del Perú
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
    BASE_DIR / 'storefront' / 'static',
    # Eliminada la referencia a 'sales' / 'static'
    BASE_DIR / 'inventory' / 'static', 
]

STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'


# Media files (Archivos subidos por usuarios)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Session configuration
SESSION_COOKIE_AGE = 3600  # 1 hora en segundos
SESSION_COOKIE_SECURE = not DEBUG # Usar True en producción
SESSION_SAVE_EVERY_REQUEST = True

# Microservices Configuration (URLs y API Keys)
MICROSERVICES = {
    'INVENTARIO': {
        'BASE_URL': os.getenv('INVENTARIO_URL', 'http://localhost:8001/'),
        'API_KEY': os.getenv('INVENTARIO_API_KEY', 'dev-key'),
    },
    'VENTAS': {
        'BASE_URL': os.getenv('VENTAS_URL', 'http://localhost:8002/'),
        'API_KEY': os.getenv('VENTAS_API_KEY', 'dev-key'),
    }
}

# Configuración de Django Debug Toolbar
INTERNAL_IPS = [
    "127.0.0.1",
]
