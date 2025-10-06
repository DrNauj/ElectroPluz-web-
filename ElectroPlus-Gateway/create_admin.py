from django.contrib.auth.models import User

# Crear superusuario
admin = User.objects.create_superuser(
    username='admin',
    email='admin@electroplus.com',
    password='Admin123!'
)

print("Usuario administrador creado:")
print(f"Usuario: admin")
print(f"Contraseña: Admin123!")