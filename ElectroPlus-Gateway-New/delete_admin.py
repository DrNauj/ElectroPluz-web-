import os
import django
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ElectroPlus_Gateway_New.settings')
django.setup()

from accounts.models import CustomUser

# Eliminar superusuario
try:
    admin_user = CustomUser.objects.get(username='admin')
    admin_user.delete()
    print("Usuario administrador eliminado exitosamente.")
except CustomUser.DoesNotExist:
    print("Usuario administrador no encontrado.")
except Exception as e:
    print(f"Error al eliminar el usuario: {e}")
