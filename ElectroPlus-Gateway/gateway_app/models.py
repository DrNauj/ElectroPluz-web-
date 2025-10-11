from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User # Importamos el modelo User

# --- Modelos de Catálogo ---

class Category(models.Model):
    """Modelo para representar las categorías de productos."""
    name = models.CharField(_("Nombre"), max_length=100)
    description = models.TextField(_("Descripción"), blank=True)
    # Slug con max_length por consistencia, y se asegura que sea único
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
    description = models.TextField(_("Descripción"))
    sku = models.CharField(_("SKU"), max_length=100, unique=True, help_text=_("Stock Keeping Unit - Código de identificación único."))
    
    # PROTECT: Evita que se elimine la categoría si tiene productos asociados.
    category = models.ForeignKey(
        Category,
        verbose_name=_("Categoría"),
        on_delete=models.PROTECT,
        related_name='products'
    )
    price = models.DecimalField(_("Precio"), max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(_("Stock"))
    min_stock = models.PositiveIntegerField(_("Stock Mínimo"), default=5)
    image = models.ImageField(_("Imagen"), upload_to='products/', blank=True, null=True)
    featured = models.BooleanField(_("Destacado"), default=False)
    active = models.BooleanField(_("Activo"), default=True)
    created_at = models.DateTimeField(_("Creado"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Actualizado"), auto_now=True)

    class Meta:
        verbose_name = _("Producto")
        verbose_name_plural = _("Productos")
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def low_stock(self):
        """Propiedad para verificar si el stock está por debajo del mínimo."""
        return self.stock <= self.min_stock

# --- Modelos de Órdenes y Perfil ---

class Order(models.Model):
    """Modelo para una orden de compra."""
    STATUS_CHOICES = (
        ('pending', _('Pendiente')),
        ('processing', _('En Proceso')),
        ('shipped', _('Enviado')),
        ('delivered', _('Entregado')),
        ('cancelled', _('Cancelado')),
    )

    # VINCULACIÓN: Se añade el vínculo con el usuario. 
    # SET_NULL permite órdenes de invitados (blank=True, null=True) o que 
    # la orden se mantenga si el usuario es eliminado.
    user = models.ForeignKey(
        User,
        verbose_name=_("Usuario"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )
    
    number = models.CharField(_("Número de Orden"), max_length=50, unique=True)
    status = models.CharField(_("Estado"), max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Información de Envío
    shipping_name = models.CharField(_("Nombre de Envío"), max_length=200)
    shipping_address = models.TextField(_("Dirección de Envío"))
    shipping_city = models.CharField(_("Ciudad"), max_length=100)
    shipping_state = models.CharField(_("Estado/Provincia"), max_length=100)
    shipping_zip = models.CharField(_("Código Postal"), max_length=20)
    shipping_country = models.CharField(_("País"), max_length=100)
    
    # Contacto
    email = models.EmailField(_("Email"))
    phone = models.CharField(_("Teléfono"), max_length=50, blank=True)
    
    # Totales Financieros
    subtotal = models.DecimalField(_("Subtotal"), max_digits=10, decimal_places=2)
    shipping_cost = models.DecimalField(_("Costo de Envío"), max_digits=10, decimal_places=2)
    tax = models.DecimalField(_("IVA"), max_digits=10, decimal_places=2)
    total = models.DecimalField(_("Total"), max_digits=10, decimal_places=2)
    
    payment_method = models.CharField(_("Método de Pago"), max_length=50)
    created_at = models.DateTimeField(_("Creado"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Actualizado"), auto_now=True)

    class Meta:
        verbose_name = _("Orden")
        verbose_name_plural = _("Órdenes")
        ordering = ['-created_at']

    def __str__(self):
        return self.number

class OrderItem(models.Model):
    """Modelo para un artículo dentro de una orden."""
    # CASCADE: Si se borra la orden, se borran sus ítems.
    order = models.ForeignKey(
        Order,
        verbose_name=_("Orden"),
        on_delete=models.CASCADE,
        related_name='items'
    )
    # PROTECT: Evita borrar el producto si está en el historial de órdenes.
    product = models.ForeignKey(
        Product,
        verbose_name=_("Producto"),
        on_delete=models.PROTECT
    )
    quantity = models.PositiveIntegerField(_("Cantidad"))
    unit_price = models.DecimalField(_("Precio Unitario"), max_digits=10, decimal_places=2)
    total_price = models.DecimalField(_("Precio Total"), max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = _("Item de Orden")
        verbose_name_plural = _("Items de Orden")

    def __str__(self):
        return f"{self.quantity}x {self.product.name} en Orden #{self.order.number}"

    def save(self, *args, **kwargs):
        """Calcula el precio total del item antes de guardar si no está definido."""
        # Se asegura de calcular el precio total basado en la cantidad y precio unitario
        if not self.total_price or self.pk is None: # Se añade self.pk is None para forzar el cálculo en la creación
            self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)

class Profile(models.Model):
    """Modelo para extender la información del usuario de Django."""
    # OneToOneField es el método estándar para extender el modelo User.
    user = models.OneToOneField(
        User,
        verbose_name=_("Usuario"),
        on_delete=models.CASCADE,
        related_name='profile'
    )
    phone = models.CharField(_("Teléfono"), max_length=50, blank=True)
    address = models.TextField(_("Dirección"), blank=True)
    city = models.CharField(_("Ciudad"), max_length=100, blank=True)
    state = models.CharField(_("Estado/Provincia"), max_length=100, blank=True)
    zip_code = models.CharField(_("Código Postal"), max_length=20, blank=True)
    country = models.CharField(_("País"), max_length=100, blank=True)
    avatar = models.ImageField(_("Avatar"), upload_to='avatars/', blank=True, null=True)
    created_at = models.DateTimeField(_("Creado"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Actualizado"), auto_now=True)

    class Meta:
        verbose_name = _("Perfil")
        verbose_name_plural = _("Perfiles")

    def __str__(self):
        return self.user.username
