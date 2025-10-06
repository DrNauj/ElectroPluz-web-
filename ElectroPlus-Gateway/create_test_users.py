from django.contrib.auth.models import User, Group
from gateway_app.models import Employee, Customer

def create_test_users():
    # Crear grupos si no existen
    admin_group, _ = Group.objects.get_or_create(name='Administradores')
    employee_group, _ = Group.objects.get_or_create(name='Empleados')
    customer_group, _ = Group.objects.get_or_create(name='Clientes')

    # Admin user
    admin_user = User.objects.create_superuser(
        username='admin',
        email='admin@electroplus.com',
        password='Admin123!',
        first_name='Admin',
        last_name='Principal'
    )
    admin_user.groups.add(admin_group)

    # Employee users
    employee1 = User.objects.create_user(
        username='vendedor1',
        email='vendedor1@electroplus.com',
        password='Vendedor123!',
        first_name='Juan',
        last_name='Pérez'
    )
    employee1.groups.add(employee_group)
    Employee.objects.create(
        user=employee1,
        employee_id='EMP001',
        department='Ventas',
        position='Vendedor'
    )

    employee2 = User.objects.create_user(
        username='inventario1',
        email='inventario1@electroplus.com',
        password='Inventario123!',
        first_name='María',
        last_name='González'
    )
    employee2.groups.add(employee_group)
    Employee.objects.create(
        user=employee2,
        employee_id='EMP002',
        department='Inventario',
        position='Supervisor'
    )

    # Customer users
    customer1 = User.objects.create_user(
        username='cliente1',
        email='cliente1@email.com',
        password='Cliente123!',
        first_name='Pedro',
        last_name='Sánchez'
    )
    customer1.groups.add(customer_group)
    Customer.objects.create(
        user=customer1,
        phone='555-0101',
        address='Calle Principal 123'
    )

    customer2 = User.objects.create_user(
        username='cliente2',
        email='cliente2@email.com',
        password='Cliente123!',
        first_name='Ana',
        last_name='Martínez'
    )
    customer2.groups.add(customer_group)
    Customer.objects.create(
        user=customer2,
        phone='555-0202',
        address='Avenida Central 456'
    )

if __name__ == '__main__':
    import os
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gateway_core.settings')
    django.setup()
    create_test_users()
    print("Usuarios de prueba creados exitosamente!")