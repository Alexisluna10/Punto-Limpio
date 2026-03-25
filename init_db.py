from apps.usuarios.models import Usuario
import os
import django

# Configurar el entorno
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()


def crear_cuentas_base():
    # --- CREAR ADMINISTRADOR ---
    if not Usuario.objects.filter(username='admin').exists():
        admin = Usuario.objects.create_superuser(
            'admin', 'admin@puntolimpio.com', 'Admin123!')
        admin.rol = 'admin'
        admin.save()
        print("Cuenta Administrador creada con éxito.")
    else:
        print("El Administrador ya existe.")

    # --- CREAR TRABAJADOR ---
    if not Usuario.objects.filter(username='trabajador1').exists():
        trabajador = Usuario.objects.create_user(
            'trabajador1', 'trabajador@puntolimpio.com', 'Trabajador123!')
        trabajador.rol = 'operador'
        trabajador.save()
        print("Cuenta Trabajador creada con éxito.")
    else:
        print("El Trabajador ya existe.")

    # --- CREAR CLIENTE ---
    if not Usuario.objects.filter(username='cliente1').exists():
        cliente = Usuario.objects.create_user(
            'cliente1', 'cliente@puntolimpio.com', 'Cliente123!')
        cliente.rol = 'cliente'
        cliente.save()
        print("Cuenta Cliente creada con éxito.")
    else:
        print("El Cliente ya existe.")


if __name__ == '__main__':
    print("Iniciando sembrado de base de datos...")
    crear_cuentas_base()
    print("Proceso finalizado.")
