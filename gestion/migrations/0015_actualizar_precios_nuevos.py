# Migration to update all Prendas and Servicios with new price list

from django.db import migrations


def actualizar_precios(apps, schema_editor):
    Prenda = apps.get_model('gestion', 'Prenda')
    Servicio = apps.get_model('gestion', 'Servicio')

    Prenda.objects.all().update(activo=False)
    Servicio.objects.all().update(activo=False)

    nuevas_prendas = [
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

    for nombre, precio in nuevas_prendas:
        obj, created = Prenda.objects.update_or_create(
            nombre=nombre,
            defaults={'precio': precio, 'activo': True}
        )
        if not created:
            obj.precio = precio
            obj.activo = True
            obj.save()

    nuevos_servicios = [
        ('1 kg de ropa', 'por_encargo', 23, 'Lavado por kilogramo de ropa'),
        ('Ropa de trabajo o muy sucia', 'por_encargo', 30, 'Lavado de ropa de trabajo o muy sucia'),
        ('Lavadora', 'autoservicio', 60, 'Uso de lavadora en autoservicio'),
        ('Secadora', 'autoservicio', 40, 'Uso de secadora en autoservicio'),
        ('Lavadora + Secadora', 'autoservicio', 100, 'Combo completo lavadora y secadora'),
    ]

    for nombre, tipo, precio, descripcion in nuevos_servicios:
        obj, created = Servicio.objects.update_or_create(
            nombre=nombre,
            defaults={
                'tipo': tipo,
                'precio': precio,
                'descripcion': descripcion,
                'activo': True,
            }
        )
        if not created:
            obj.tipo = tipo
            obj.precio = precio
            obj.descripcion = descripcion
            obj.activo = True
            obj.save()


def revertir_precios(apps, schema_editor):
    Prenda = apps.get_model('gestion', 'Prenda')
    Servicio = apps.get_model('gestion', 'Servicio')
    Prenda.objects.all().update(activo=True)
    Servicio.objects.all().update(activo=True)


class Migration(migrations.Migration):

    dependencies = [
        ('gestion', '0014_movimientoinsumo_insumo_nombre_and_more'),
    ]

    operations = [
        migrations.RunPython(actualizar_precios, revertir_precios),
    ]