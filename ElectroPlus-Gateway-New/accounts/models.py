from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('CUSTOMER', 'Cliente'),
        ('ADMIN', 'Administrador'),
        ('MANAGER', 'Gerente'),
        ('SALES', 'Ventas'),
        ('INVENTORY', 'Inventario'),
        ('SUPPORT', 'Soporte'),
    ]
    
    role = models.CharField(
        _('rol'),
        max_length=10,
        choices=ROLE_CHOICES,
        default='CUSTOMER'
    )
    profile_picture = models.URLField(blank=True)
    
    class Meta:
        verbose_name = _('usuario')
        verbose_name_plural = _('usuarios')