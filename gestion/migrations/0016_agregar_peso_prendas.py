# Generated migration file

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestion', '0015_actualizar_precios_nuevos'),
    ]

    operations = [
        migrations.AddField(
            model_name='prenda',
            name='peso_kg',
            field=models.DecimalField(
                decimal_places=3,
                default=0,
                help_text='Peso de la prenda en kilogramos',
                max_digits=6,
                verbose_name='Peso (KG)'
            ),
        ),
    ]