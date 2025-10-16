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
    logger.info(f"Intentando autenticar usuario: {username_or_id}")
    
    if not settings.MICROSERVICES.get('VENTAS'):
        logger.error("Configuración de microservicio VENTAS no encontrada")
        return None, "Error de configuración del servicio"
    try:
        # Construir la URL del endpoint de autenticación
        base_url = settings.MICROSERVICES['VENTAS']['BASE_URL'].rstrip('/')
        auth_url = f"{base_url}/api/auth/login/"
        logger.debug(f"URL de autenticación: {auth_url}")
        
        # Preparar los datos de la solicitud - mapear a los nombres esperados por el servicio
        auth_data = {
            'nombre_usuario': username_or_id,
            'contrasena': password
        }
        
        # Enviar solicitud al microservicio
        response = requests.post(
            auth_url, 
            json=auth_data,
            headers={'X-API-Key': settings.MICROSERVICES['VENTAS']['API_KEY']},
            timeout=5
        )
        
        # Verificar la respuesta
        logger.info(f"Respuesta del servicio: Status {response.status_code}")
        try:
            response_data = response.json()
            logger.debug(f"Datos de respuesta: {response_data}")
        except ValueError:
            logger.error("Respuesta no es JSON válido")
            return None, "Respuesta inválida del servidor"

        if response.status_code == 200:
            user_data = {
                'id': response_data.get('id'),
                'nombre_usuario': response_data.get('nombre_usuario'),
                'rol': response_data.get('rol')
            }
            
            # Verificar que los datos requeridos estén presentes
            if not all(user_data.values()):
                logger.error(f"Datos de usuario incompletos: {user_data}")
                return None, "Datos de usuario incompletos"
            
            logger.info(f"Autenticación exitosa para usuario: {user_data['nombre_usuario']}")
            return user_data, None
            
        elif response.status_code in [401, 403]:
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