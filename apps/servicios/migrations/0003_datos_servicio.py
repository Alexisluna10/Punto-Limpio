# apps/servicios/migrations/0002_semilla_datos_servicios.py

from django.db import migrations
from decimal import Decimal

def cargar_datos_maestros(apps, schema_editor):
    # Obtenemos los modelos históricos de la app 'servicios'
    # NOTA: Si cambiaste el nombre de la app, ajusta 'servicios'
    try:
        Prenda = apps.get_model('servicios', 'Prenda')
        Servicio = apps.get_model('servicios', 'Servicio')
    except LookupError:
        print("No se encontraron los modelos. Verifica el nombre de la app.")
        return

    # ---------------------------------------------------------
    # 1. CREACIÓN DE SERVICIOS (Basado en 002_datos_iniciales)
    # ---------------------------------------------------------
    servicios_data = [
        # (Nombre, Tipo, Precio, Descripción)
        ('Lavado por Encargo (Kg)', 'por_encargo', 23.00, 'Lavado general por kilogramo de ropa'),
        ('Ropa de trabajo / Muy sucia', 'por_encargo', 30.00, 'Lavado especial para ropa con grasa o suciedad difícil'),
        ('Autoservicio (Lavadora)', 'autoservicio', 60.00, 'Renta de lavadora por ciclo'),
        ('Autoservicio (Secadora)', 'autoservicio', 40.00, 'Renta de secadora por ciclo'),
        ('Planchado por Docena', 'planchado', 100.00, 'Servicio de planchado'),
        ('Tintorería (Pieza)', 'tintoreria', 0.00, 'Servicio especializado (precio variable)'),
        ('Servicio a Domicilio', 'a_domicilio', 50.00, 'Costo extra por recolección y entrega'),
    ]

    print("\n--- Cargando Servicios ---")
    for nombre, tipo, precio, descripcion in servicios_data:
        # Usamos get_or_create para no duplicar si se corre dos veces
        obj, created = Servicio.objects.get_or_create(
            nombre=nombre,
            defaults={
                'tipo': tipo,
                'precio': Decimal(str(precio)),
                'descripcion': descripcion
            }
        )
        if created:
            print(f"✅ Servicio creado: {nombre}")

    # ---------------------------------------------------------
    # 2. CREACIÓN DE PRENDAS (Basado en 0017_actualizar_pesos)
    # ---------------------------------------------------------
    # Precio base para cálculo: $23.00 por Kg (según tu lógica anterior)
    PRECIO_BASE_KG = Decimal('23.00')

    # Diccionario: 'Nombre': Peso_en_KG
    prendas_pesos = {
        # Ropa Común
        'Calcetas / Ropa Interior': 0.050,
        'Playera / Camisa': 0.200,
        'Pantalón de Mezclilla': 0.500,
        
        # Edredones
        'Edredón Individual': 2.5,
        'Edredón Matrimonial': 3.0,
        'Edredón Queen': 3.5,
        'Edredón King': 4.5,
        
        # Cobertores
        'Cobertor Individual': 2.5,
        'Cobertor Matrimonial': 3.2,
        'Cobertor Queen': 3.8,
        'Cobertor King': 4.7,
        
        # Blancos
        'Juego Sábanas Individual': 1.2,
        'Juego Sábanas Matrimonial': 1.5,
        'Juego Sábanas Queen': 2.4,
        'Juego Sábanas King': 3.2,
        'Cubrecolchón Individual': 0.8,
        'Cubrecolchón Matrimonial': 1.0,
        'Cortinas (Kg)': 1.0,
        
        # Especiales
        'Tenis (Par)': 1.0, # Precio fijo aproximado de 1kg
        'Peluche Chico': 0.2,
        'Peluche Mediano': 0.5,
        'Peluche Grande': 1.0,
    }

    print("\n--- Cargando Prendas ---")
    for nombre, peso in prendas_pesos.items():
        peso_decimal = Decimal(str(peso))
        
        # Lógica de precio: Si es muy ligero (calcetas), precio mínimo o proporcional?
        # Aquí usamos tu lógica: peso * 23. 
        # NOTA: Para edredones el precio sube mucho con esta fórmula.
        # Si prefieres precios fijos del archivo 0015, puedes sobreescribirlos.
        
        precio_calculado = peso_decimal * PRECIO_BASE_KG
        
        # Ajuste: Redondear a números amigables (opcional)
        # precio_calculado = round(precio_calculado)

        Prenda.objects.get_or_create(
            nombre=nombre,
            defaults={
                'peso_kg': peso_decimal, # Asegúrate de tener este campo en tu modelo
                'precio': precio_calculado,
            }
        )
        print(f"✅ Prenda creada: {nombre} (${precio_calculado:.2f})")


class Migration(migrations.Migration):

    dependencies = [
        # Asegúrate de que esto apunte a tu última migración de 'servicios'
        ('servicios', '0002_initial'), 
    ]

    operations = [
        migrations.RunPython(cargar_datos_maestros),
    ]