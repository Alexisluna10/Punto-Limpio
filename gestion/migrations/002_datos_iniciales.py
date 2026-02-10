# Migration to insert initial data for Prendas and Servicios

from django.db import migrations


def crear_datos_iniciales(apps, schema_editor):
    Prenda = apps.get_model('gestion', 'Prenda')
    Servicio = apps.get_model('gestion', 'Servicio')
    
    # Crear prendas con precios iniciales
    prendas_iniciales = [
        ('Traje completo (saco y pantalon)', 250),
        ('Saco', 150),
        ('Pantalon de vestir', 130),
        ('Vestido', 200),
        ('Vestido de gala / noche', 400),
        ('Falda', 120),
        ('Blusa de seda', 130),
        ('Blusa de satin', 120),
        ('Blusa de encaje', 125),
        ('Abrigo', 250),
        ('Camisa de vestir', 100),
        ('Gabardina', 300),
        ('Chamarra (piel / sintetica)', 250),
        ('Sueter cashmere', 200),
        ('Corbata', 80),
        ('Bufanda', 100),
        ('Guantes', 60),
        ('Gorra / sombrero', 80),
        ('Edredon individual', 250),
        ('Edredon matrimonial', 300),
        ('Edredon king size', 350),
        ('Cobija individual', 150),
        ('Cobija matrimonial', 200),
        ('Cobija king size', 250),
        ('Almohada', 100),
        ('Cortina (por metro)', 80),
        ('Tapete pequeno', 150),
        ('Tapete mediano', 250),
        ('Tapete grande', 350),
        ('Mantel', 100),
        ('Cojin decorativo', 80),
        ('Bolsa de tela', 80),
        ('Mochila', 120),
        ('Peluche pequeno', 80),
        ('Peluche mediano', 150),
        ('Peluche grande', 250),
    ]
    
    for nombre, precio in prendas_iniciales:
        Prenda.objects.create(nombre=nombre, precio=precio)
    
    # Crear servicios con precios iniciales
    servicios_iniciales = [
        ('Lavadora', 'autoservicio', 50, 'Uso de lavadora en autoservicio'),
        ('Secadora', 'autoservicio', 40, 'Uso de secadora en autoservicio'),
        ('Combo (lavadora + secadora)', 'autoservicio', 80, 'Combo completo lavadora y secadora'),
        ('Por encargo (por kg)', 'por_encargo', 30, 'Servicio de lavado por kilogramo'),
        ('A domicilio (adicional)', 'a_domicilio', 50, 'Cargo adicional por servicio a domicilio'),
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