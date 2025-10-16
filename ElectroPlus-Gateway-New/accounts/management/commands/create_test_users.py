from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

class Command(BaseCommand):
    help = 'Crea usuarios de prueba para cada rol'

    def handle(self, *args, **kwargs):
        test_users = [
            {
                'username': 'admin',
                'email': 'admin@ejemplo.com',
                'password': 'admin12345',
                'role': 'ADMIN',
                'is_staff': True,
                'is_superuser': True
            },
            {
                'username': 'gerente',
                'email': 'gerente@ejemplo.com',
                'password': 'gerente12345',
                'role': 'MANAGER',
                'is_staff': True
            },
            {
                'username': 'ventas',
                'email': 'ventas@ejemplo.com',
                'password': 'ventas12345',
                'role': 'SALES',
                'is_staff': True
            },
            {
                'username': 'inventario',
                'email': 'inventario@ejemplo.com',
                'password': 'inventario12345',
                'role': 'INVENTORY',
                'is_staff': True
            },
            {
                'username': 'soporte',
                'email': 'soporte@ejemplo.com',
                'password': 'soporte12345',
                'role': 'SUPPORT',
                'is_staff': True
            },
            {
                'username': 'cliente',
                'email': 'cliente@ejemplo.com',
                'password': 'cliente12345',
                'role': 'CUSTOMER',
                'is_staff': False
            }
        ]

        with transaction.atomic():
            for user_data in test_users:
                username = user_data.pop('username')
                password = user_data.pop('password')
                
                if not User.objects.filter(username=username).exists():
                    user = User.objects.create_user(
                        username=username,
                        **user_data
                    )
                    user.set_password(password)
                    user.save()
                    self.stdout.write(
                        self.style.SUCCESS(f'Usuario "{username}" creado exitosamente')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'Usuario "{username}" ya existe')
                    )