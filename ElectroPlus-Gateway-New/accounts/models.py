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

class Category(models.Model):
    """Modelo para representar las categorías de productos."""
    name = models.CharField(_("Nombre"), max_length=100)
    description = models.TextField(_("Descripción"), blank=True)
    slug = models.SlugField(_("Slug"), max_length=100, unique=True)
    active = models.BooleanField(_("Activo"), default=True)
    created_at = models.DateTimeField(_("Creado"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Actualizado"), auto_now=True)

    class Meta:
        verbose_name = _("Categoría")
        verbose_name_plural = _("Categorías")
        ordering = ['name']

    def __str__(self):
        return self.name

class Product(models.Model):
    """Modelo para un producto en el catálogo."""
    name = models.CharField(_("Nombre"), max_length=200)
    slug = models.SlugField(_("Slug"), max_length=200, unique=True)
    description = models.TextField(_("Descripción"))
    price = models.DecimalField(_("Precio"), max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    stock = models.IntegerField(_("Stock"), default=0)
    image = models.ImageField(_("Imagen"), upload_to='products/', null=True, blank=True)
    active = models.BooleanField(_("Activo"), default=True)
    created_at = models.DateTimeField(_("Creado"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Actualizado"), auto_now=True)

    class Meta:
        verbose_name = _("Producto")
        verbose_name_plural = _("Productos")
        ordering = ['-created_at']

    def __str__(self):
        return self.name

class Order(models.Model):
    """Modelo para una orden de compra."""
    STATUS_CHOICES = (
        ('pending', _('Pendiente')),
        ('processing', _('Procesando')),
        ('shipped', _('Enviado')),
        ('delivered', _('Entregado')),
        ('cancelled', _('Cancelado')),
    )

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(_("Estado"), max_length=20, choices=STATUS_CHOICES, default='pending')
    total = models.DecimalField(_("Total"), max_digits=10, decimal_places=2)
    shipping_address = models.TextField(_("Dirección de envío"))
    shipping_city = models.CharField(_("Ciudad de envío"), max_length=100)
    shipping_state = models.CharField(_("Estado/Provincia de envío"), max_length=100)
    shipping_zip = models.CharField(_("Código postal de envío"), max_length=10)
    shipping_country = models.CharField(_("País de envío"), max_length=100)
    created_at = models.DateTimeField(_("Creado"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Actualizado"), auto_now=True)

    class Meta:
        verbose_name = _("Orden")
        verbose_name_plural = _("Órdenes")
        ordering = ['-created_at']

    def __str__(self):
        return f"Orden #{self.id} - {self.user.username}"

class OrderItem(models.Model):
    """Modelo para un artículo dentro de una orden."""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(_("Cantidad"))
    price = models.DecimalField(_("Precio"), max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(_("Subtotal"), max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = _("Item de orden")
        verbose_name_plural = _("Items de orden")

    def __str__(self):
        return f"{self.quantity}x {self.product.name} en Orden #{self.order.id}"

    def save(self, *args, **kwargs):
        self.subtotal = self.quantity * self.price
        super().save(*args, **kwargs)