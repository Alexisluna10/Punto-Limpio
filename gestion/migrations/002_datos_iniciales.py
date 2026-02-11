# Migration to insert initial data for Prendas and Servicios

from django.db import migrations


def crear_datos_iniciales(apps, schema_editor):
    Prenda = apps.get_model('gestion', 'Prenda')
    Servicio = apps.get_model('gestion', 'Servicio')
    
    prendas_iniciales = [
        # Cobertores
        ('Cobertor Individual', 55),
        ('Cobertor Matrimonial', 65),
        ('Cobertor Queen / King', 75),
        # Edredones
        ('Edredon Individual', 65),
        ('Edredon Matrimonial', 75),
        ('Edredon Queen / King', 85),
        # Frazadas
        ('Frazada Individual', 40),
        ('Frazada Matrimonial / Queen / King', 50),
        # Juego de sabanas
        ('Juego de sabanas', 50),
        # Otros
        ('Tenis', 60),
        ('Cortinas', 60),
        ('Cubre colchon', 60),
        ('Peluche chico', 20),
        ('Peluche mediano y grande', 40),
    ]
    
    for nombre, precio in prendas_iniciales:
        Prenda.objects.create(nombre=nombre, precio=precio)
    
    servicios_iniciales = [
        ('1 kg de ropa', 'por_encargo', 23, 'Lavado por kilogramo de ropa'),
        ('Ropa de trabajo o muy sucia', 'por_encargo', 30, 'Lavado de ropa de trabajo o muy sucia'),
        ('Lavadora', 'autoservicio', 60, 'Uso de lavadora en autoservicio'),
        ('Secadora', 'autoservicio', 40, 'Uso de secadora en autoservicio'),
        ('Lavadora + Secadora', 'autoservicio', 100, 'Combo completo lavadora y secadora'),
    ]
    
    for nombre, tipo, precio, descripcion in servicios_iniciales:
        Servicio.objects.create(nombre=nombre, tipo=tipo, precio=precio, descripcion=descripcion)


def eliminar_datos_iniciales(apps, schema_editor):
    Prenda = apps.get_model('gestion', 'Prenda')
    Servicio = apps.get_model('gestion', 'Servicio')
    Prenda.objects.all().delete()
    Servicio.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('gestion', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(crear_datos_iniciales, eliminar_datos_iniciales),
    ]