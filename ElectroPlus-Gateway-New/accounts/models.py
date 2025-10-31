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
    phone = models.CharField(_("Teléfono"), max_length=20, blank=True)
    address = models.CharField(_("Dirección"), max_length=255, blank=True)
    city = models.CharField(_("Ciudad"), max_length=100, blank=True)
    state = models.CharField(_("Estado/Provincia"), max_length=100, blank=True)
    zip_code = models.CharField(_("Código Postal"), max_length=10, blank=True)
    country = models.CharField(_("País"), max_length=100, blank=True)
    
    class Meta:
        verbose_name = _('usuario')
        verbose_name_plural = _('usuarios')

    def __str__(self):
        return f"{self.get_full_name()} ({self.username})"


