# Generated migration for Pedido, DetallePedido, and MovimientoOperador models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('gestion', '0004_notificacionstock'),
    ]

    operations = [
        migrations.CreateModel(
            name='Pedido',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('folio', models.CharField(blank=True, max_length=20, unique=True)),
                ('tipo_servicio', models.CharField(max_length=50)),
                ('peso', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('cantidad_prendas', models.IntegerField(default=0)),
                ('observaciones', models.TextField(blank=True, null=True)),
                ('cobija_tipo', models.CharField(blank=True, max_length=50, null=True)),
                ('lavado_especial', models.BooleanField(default=False)),
                ('total', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('metodo_pago', models.CharField(default='efectivo', max_length=20)),
                ('estado', models.CharField(choices=[('pendiente', 'Pendiente'), ('en_proceso', 'En Proceso'), ('listo', 'Listo para entrega'), ('entregado', 'Entregado'), ('cancelado', 'Cancelado')], default='pendiente', max_length=20)),
                ('estado_pago', models.CharField(choices=[('pendiente', 'Pendiente'), ('pagado', 'Pagado')], default='pendiente', max_length=20)),
                ('origen', models.CharField(choices=[('cliente', 'Solicitado por cliente'), ('operador', 'Registrado por operador')], default='cliente', max_length=20)),
                ('fecha_recepcion', models.DateTimeField(default=django.utils.timezone.now)),
                ('fecha_entrega_estimada', models.DateField(blank=True, null=True)),
                ('fecha_entrega_real', models.DateTimeField(blank=True, null=True)),
                ('cliente', models.ForeignKey(limit_choices_to={'rol': 'cliente'}, on_delete=django.db.models.deletion.CASCADE, related_name='pedidos', to=settings.AUTH_USER_MODEL)),
                ('operador', models.ForeignKey(blank=True, limit_choices_to={'rol__in': ['operador', 'admin']}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pedidos_registrados', to=settings.AUTH_USER_MODEL)),
                ('servicio', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='gestion.servicio')),
            ],
            options={
                'verbose_name': 'Pedido',
                'verbose_name_plural': 'Pedidos',
                'ordering': ['-fecha_recepcion'],
            },
        ),
        migrations.CreateModel(
            name='DetallePedido',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cantidad', models.IntegerField(default=1)),
                ('peso', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('precio_unitario', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('subtotal', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('pedido', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='detalles', to='gestion.pedido')),
                ('prenda', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='gestion.prenda')),
            ],
        ),
        migrations.CreateModel(
            name='MovimientoOperador',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('accion', models.CharField(choices=[('creo_ticket', 'Creo ticket'), ('entrego', 'Entrego'), ('cambio_precio', 'Cambio precio'), ('elimino', 'Elimino'), ('actualizo', 'Actualizo'), ('registro_servicio', 'Registro servicio')], max_length=30)),
                ('detalles', models.CharField(max_length=255)),
                ('fecha', models.DateTimeField(default=django.utils.timezone.now)),
                ('operador', models.ForeignKey(limit_choices_to={'rol__in': ['operador', 'admin']}, on_delete=django.db.models.deletion.CASCADE, related_name='movimientos', to=settings.AUTH_USER_MODEL)),
                ('pedido', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='movimientos', to='gestion.pedido')),
            ],
            options={
                'verbose_name': 'Movimiento de Operador',
                'verbose_name_plural': 'Movimientos de Operadores',
                'ordering': ['-fecha'],
            },
        ),
    ]
