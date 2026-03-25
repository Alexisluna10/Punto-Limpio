from django.contrib.auth.models import Group
from apps.usuarios.models import Usuario
import os
import django

# Configurar el entorno
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()


def crear_cuentas_base():
    # --- 1. CREAR LOS GRUPOS DE AUTENTICACIÓN ---
    nombres_grupos = ['Administrador', 'Operador', 'Cliente']
    grupos = {}
    for nombre in nombres_grupos:
        grupo, created = Group.objects.get_or_create(name=nombre)
        grupos[nombre] = grupo
        if created:
            print(f"✅ Grupo '{nombre}' creado en la base de datos.")

    # --- 2. CREAR SUPERUSUARIO (Para control total y panel /admin/ de Django) ---
    if not Usuario.objects.filter(username='superadmin').exists():
        superadmin = Usuario.objects.create_superuser(
            'superadmin', 'super@puntolimpio.com', 'Super123!')
        superadmin.rol = 'admin'
        superadmin.save()
        superadmin.groups.add(grupos['Administrador'])
        print("✅ Cuenta Superusuario (superadmin) creada.")
    else:
        superadmin = Usuario.objects.get(username='superadmin')
        superadmin.groups.add(grupos['Administrador'])
        print("⚡ Superusuario ya existía (Grupos actualizados).")

    # --- 3. CREAR ADMINISTRADOR (Usuario normal pero con rol de jefe para la App) ---
    if not Usuario.objects.filter(username='admin').exists():
        admin = Usuario.objects.create_user(
            'admin', 'admin@puntolimpio.com', 'Admin123!')
        admin.rol = 'admin'
        admin.is_staff = True  # Le damos acceso a ciertas áreas internas si es necesario
        admin.save()
        admin.groups.add(grupos['Administrador'])
        print("✅ Cuenta Administrador (admin) creada.")
    else:
        admin = Usuario.objects.get(username='admin')
        admin.rol = 'admin'
        admin.save()
        admin.groups.add(grupos['Administrador'])
        print("⚡ Administrador ya existía (Grupos y Rol actualizados).")

    # --- 4. CREAR TRABAJADOR / OPERADOR ---
    if not Usuario.objects.filter(username='trabajador1').exists():
        trabajador = Usuario.objects.create_user(
            'trabajador1', 'trabajador@puntolimpio.com', 'Trabajador123!')
        trabajador.rol = 'operador'
        trabajador.save()
        trabajador.groups.add(grupos['Operador'])
        print("✅ Cuenta Trabajador creada.")
    else:
        trabajador = Usuario.objects.get(username='trabajador1')
        trabajador.rol = 'operador'
        trabajador.save()
        trabajador.groups.add(grupos['Operador'])
        print("⚡ Trabajador ya existía (Grupos y Rol actualizados).")

    # --- 5. CREAR CLIENTE ---
    if not Usuario.objects.filter(username='cliente1').exists():
        cliente = Usuario.objects.create_user(
            'cliente1', 'cliente@puntolimpio.com', 'Cliente123!')
        cliente.rol = 'cliente'
        cliente.save()
        cliente.groups.add(grupos['Cliente'])
        print("✅ Cuenta Cliente creada.")
    else:
        cliente = Usuario.objects.get(username='cliente1')
        cliente.rol = 'cliente'
        cliente.save()
        cliente.groups.add(grupos['Cliente'])
        print("⚡ Cliente ya existía (Grupos y Rol actualizados).")


if __name__ == '__main__':
    print("Iniciando sembrado y configuración de base de datos...")
    crear_cuentas_base()
    print("🚀 Proceso finalizado con éxito.")
