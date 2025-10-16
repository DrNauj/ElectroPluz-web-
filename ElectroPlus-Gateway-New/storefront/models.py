from django.db import models
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stock = models.IntegerField()
    min_stock = models.IntegerField(default=5)
    is_active = models.BooleanField(default=True)
    image = models.CharField(max_length=500, blank=True)  # URL de imagen para datos mock
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    avg_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    review_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name

    def update_rating_stats(self):
        reviews = self.reviews.all()
        if reviews:
            self.avg_rating = sum(r.rating for r in reviews) / len(reviews)
            self.review_count = len(reviews)
        else:
            self.avg_rating = 0
            self.review_count = 0
        self.save()


class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/%Y/%m', blank=True, null=True)
    alt_text = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f'Imagen de {self.product.name} ({self.id})'


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('processing', 'En Proceso'),
        ('shipped', 'Enviado'),
        ('delivered', 'Entregado'),
        ('cancelled', 'Cancelado'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('credit_card', 'Tarjeta de Crédito'),
        ('debit_card', 'Tarjeta de Débito'),
        ('transfer', 'Transferencia Bancaria'),
        ('cash', 'Efectivo'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    # Información de envío
    shipping_address = models.CharField(max_length=200, blank=True, null=True)
    shipping_city = models.CharField(max_length=100, blank=True, null=True)
    shipping_state = models.CharField(max_length=100, blank=True, null=True)
    shipping_postal_code = models.CharField(max_length=10, blank=True, null=True)
    shipping_phone = models.CharField(max_length=20, blank=True, null=True)
    
    # Información de pago
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    external_sale_id = models.CharField(max_length=100, blank=True, null=True, help_text="ID de la venta en el microservicio de Ventas")
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)

    def get_subtotal(self):
        return sum(item.get_total() for item in self.items.all())

    def calculate_tax(self):
        """Calcula el IVA basado en el subtotal"""
        return self.get_subtotal() * Decimal('0.19')  # 19% IVA

    def calculate_total(self):
        """Calcula el total basado en subtotal, impuestos y descuento"""
        return self.get_subtotal() + self.calculate_tax() - self.discount

    def update_totals(self):
        """Actualiza los campos tax y total basado en los cálculos"""
        self.tax = self.calculate_tax()
        self.total = self.calculate_total()

    def save(self, *args, **kwargs):
        """Sobrescribe save para actualizar totales automáticamente"""
        if self.pk:  # Solo si ya existe (para evitar error en creación)
            self.update_totals()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Orden #{self.id} - {self.user.username}'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='order_items', null=True, on_delete=models.PROTECT)
    product_name = models.CharField(max_length=200)
    product_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()

    def get_total(self):
        return Decimal(self.product_price) * self.quantity

    def save(self, *args, **kwargs):
        if self.product and not self.product_name:
            self.product_name = self.product.name
        if self.product and not self.product_price:
            self.product_price = self.product.price
        super().save(*args, **kwargs)


class Review(models.Model):
    product = models.ForeignKey(Product, related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('product', 'user')

    def __str__(self):
        return f'Reseña de {self.user.username} para {self.product.name}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.product.update_rating_stats()


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    default_shipping_address = models.TextField(blank=True)
    default_phone = models.CharField(max_length=20, blank=True)
    wishlist = models.ManyToManyField(Product, blank=True, related_name='wishlists')

    def __str__(self):
        return f'Perfil de {self.user.username}'


class Claim(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('in_progress', 'En Proceso'),
        ('resolved', 'Resuelto'),
        ('rejected', 'Rechazado'),
    ]

    TYPE_CHOICES = [
        ('product_issue', 'Problema con producto'),
        ('shipping_issue', 'Problema de envío'),
        ('wrong_product', 'Producto equivocado'),
        ('other', 'Otro'),
    ]

    order = models.ForeignKey(Order, related_name='claims', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolution_notes = models.TextField(blank=True)

    def __str__(self):
        return f'Reclamo #{self.id} - Pedido #{self.order.id}'


class ClaimUpdate(models.Model):
    claim = models.ForeignKey(Claim, related_name='updates', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=Claim.STATUS_CHOICES)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Actualización de Reclamo #{self.claim.id} - {self.status}'
