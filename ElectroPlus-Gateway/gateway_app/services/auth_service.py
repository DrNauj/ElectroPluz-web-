"""
Servicios de autenticación para la aplicación gateway.
"""
import logging
import requests
from django.conf import settings
from .. import models

logger = logging.getLogger(__name__)

def authenticate_with_service(username_or_id, password):
    """
    Autentica un usuario contra el microservicio de usuarios.
    
    Args:
        username_or_id: Nombre de usuario o ID
        password: Contraseña del usuario
    
    Returns:
        tuple: (datos_usuario, error)
            - datos_usuario: diccionario con los datos del usuario si la autenticación es exitosa
            - error: mensaje de error si la autenticación falla
    """
    try:
        # Construir la URL del endpoint de autenticación
        auth_url = f"{settings.USER_SERVICE_URL}/auth/login/"
        
        # Preparar los datos de la solicitud
        auth_data = {
            'username': username_or_id,
            'password': password
        }
        
        # Enviar solicitud al microservicio
        response = requests.post(
            auth_url, 
            json=auth_data,
            headers={'Authorization': f'Bearer {settings.USER_SERVICE_KEY}'},
            timeout=5
        )
        
        # Verificar la respuesta
        if response.status_code == 200:
            user_data = response.json()
            
            # Verificar que los datos requeridos estén presentes
            required_fields = ['id', 'nombre_usuario', 'rol']
            if not all(field in user_data for field in required_fields):
                logger.error(f"Datos de usuario incompletos: {user_data}")
                return None, "Datos de usuario incompletos"
            
            return user_data, None
            
        elif response.status_code == 401:
            logger.warning(f"Autenticación fallida para usuario: {username_or_id}")
            return None, "Credenciales inválidas"
            
        else:
            logger.error(f"Error del servicio de usuarios: {response.status_code}")
            return None, "Error del servicio de autenticación"
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error al conectar con el servicio de usuarios: {e}")
        return None, "Error al conectar con el servicio de autenticación"
        
    except Exception as e:
        logger.error(f"Error inesperado en authenticate_with_service: {e}")
        return None, "Error interno del servidor"