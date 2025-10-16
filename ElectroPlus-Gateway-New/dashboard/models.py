from django.db import models
from django.conf import settings
from storefront.models import Product, Order

class Branch(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()
    phone = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

class Inventory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)
    min_stock = models.PositiveIntegerField(default=10)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('product', 'branch')
        verbose_name_plural = 'Inventories'
        indexes = [
            models.Index(fields=['quantity']),  # Para búsquedas de stock bajo
        ]

    def is_low_stock(self):
        return self.quantity <= self.min_stock

    def __str__(self):
        return f"{self.product.name} en {self.branch.name}"

# Claims model moved to storefront/models.py

class FinancialTransaction(models.Model):
    TYPE_CHOICES = [
        ('income', 'Ingreso'),
        ('expense', 'Gasto'),
        ('investment', 'Inversión')
    ]
    
    date = models.DateField(db_index=True)  # Índice para búsquedas por fecha
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    description = models.TextField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    order = models.ForeignKey(Order, null=True, blank=True, on_delete=models.SET_NULL)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['date', 'type']),  # Para reportes financieros
        ]
        ordering = ['-date', '-created_at']  # Ordenamiento predeterminado

    def __str__(self):
        return f"{self.get_type_display()} - {self.date} - {self.amount}"

    def save(self, *args, **kwargs):
        if self.type in ['expense', 'investment'] and self.amount > 0:
            self.amount = -self.amount  # Gastos e inversiones se guardan como negativos
        super().save(*args, **kwargs)

class Budget(models.Model):
    PERIOD_CHOICES = [
        ('monthly', 'Mensual'),
        ('quarterly', 'Trimestral'),
        ('yearly', 'Anual')
    ]
    
    period = models.CharField(max_length=20, choices=PERIOD_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    expected_income = models.DecimalField(max_digits=10, decimal_places=2)
    expected_expenses = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
