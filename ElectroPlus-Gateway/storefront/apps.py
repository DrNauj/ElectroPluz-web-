from django.apps import AppConfig


class StorefrontConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'storefront'
    verbose_name = 'Frontend Público'  # Nombre legible en el admin
    
    def ready(self):
        """
        Método llamado cuando la app está lista.
        Aquí podemos registrar signals u otras configuraciones.
        """
        pass  # Por ahora no necesitamos nada aquí
