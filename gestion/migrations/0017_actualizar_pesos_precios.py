# Generated data migration file

from django.db import migrations
from decimal import Decimal


def actualizar_pesos_prendas(apps, schema_editor):
    """
    Actualiza los pesos de las prendas según la lista proporcionada.
    Los precios se calculan como: peso_kg * 23 pesos
    """
    Prenda = apps.get_model('gestion', 'Prenda')
    
    # Diccionario con los pesos de cada prenda (en KG)
    pesos_prendas = {
        # CALCETAS
        'CALCETAS': 0.050,
        
        # EDREDONES
        'EDREDON INDIVIDUAL': 2.5,
        'EDREDON MATRIMONIAL': 3.0,
        'EDREDON QUEEN': 3.5,
        'EDREDON KING': 4.5,
        
        # COBERTORES
        'COBERTOR INDIVIDUAL': 2.5,
        'COBERTOR MATRIMONIAL': 3.2,
        'COBERTOR QUEEN': 3.8,
        'COBERTOR KING': 4.7,
        
        # CUBRECOLCHON
        'CUBRECOLCHON INDIVIDUAL': 0.8,
        'CUBRECOLCHON MATRIMONIAL': 1.0,
        'CUBRECOLCHON QUEEN': 1.2,
        'CUBRECOLCHON KING': 2.4,
        
        # FRAZADAS
        'FRAZADA INDIVIDUAL': 2.5,
        'FRAZADA MATRIMONIAL': 3.0,
        'FRAZADA QUEEN': 3.5,
        'FRAZADA KING': 4.5,
        
        # JUEGO SABANAS
        'JUEGO SABANAS INDIVIDUAL': 1.2,
        'JUEGO SABANAS MATRIMONIAL': 1.5,
        'JUEGO SABANAS QUEEN': 2.4,
        'JUEGO SABANAS KING': 3.2,
        
        # PELUCHES
        'PELUCHE GRANDE': 0.800,
        'PELUCHE MEDIANO': 0.300,
        'PELUCHE CHICO': 0.200,
        
        # OTROS
        'TENIS': 1.0,
        'CORTINAS': 2.0,
    }
    
    # Precio por kilogramo
    PRECIO_POR_KG = Decimal('23.00')
    
    # Actualizar cada prenda
    for nombre_prenda, peso_kg in pesos_prendas.items():
        peso_decimal = Decimal(str(peso_kg))
        precio_calculado = peso_decimal * PRECIO_POR_KG
        
        # Intentar encontrar la prenda (sin importar mayúsculas/minúsculas)
        prenda = Prenda.objects.filter(nombre__iexact=nombre_prenda).first()
        
        if prenda:
            prenda.peso_kg = peso_decimal
            prenda.precio = precio_calculado
            prenda.save()
            print(f"✓ Actualizado: {prenda.nombre} - {peso_kg} KG - ${precio_calculado}")
        else:
            # Si no existe, crear la prenda
            Prenda.objects.create(
                nombre=nombre_prenda,
                peso_kg=peso_decimal,
                precio=precio_calculado,
                tipo_limpieza='detergente',
                activo=True
            )
            print(f"✓ Creado: {nombre_prenda} - {peso_kg} KG - ${precio_calculado}")


def revertir_cambios(apps, schema_editor):
    """
    Función para revertir los cambios si es necesario.
    No hace nada porque no queremos eliminar datos.
    """
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('gestion', '0016_agregar_peso_prendas'),
    ]

    operations = [
        migrations.RunPython(actualizar_pesos_prendas, revertir_cambios),
    ]
    