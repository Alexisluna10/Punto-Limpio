from django.db import models
from django.utils import timezone
from apps.usuarios.models import Usuario


class Prenda(models.Model):
    """Modelo para almacenar los tipos de prendas y sus precios"""

    TIPOS_LIMPIEZA = [
        ('detergente', 'Detergente'),
        ('detergente_delicado', 'Detergente (delicado)'),
        ('detergente_suave', 'Detergente (suave)'),
        ('detergente_suavizante', 'Detergente + Suavizante'),
        ('detergente_voluminosa', 'Detergente (ropa voluminosa)'),
        ('lavado_seco', 'Otros (lavado en seco)'),
        ('limpieza_general', 'Limpieza general'),
        ('limpieza_especializada', 'Otros (limpieza especializada)'),
        ('detergente_especial', 'Otros (detergente especial / lavado en seco)'),
        ('detergente_especial_otros', 'Otros (detergente especial)'),
    ]

    nombre = models.CharField(max_length=100, unique=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    peso_kg = models.DecimalField(
        max_digits=6, decimal_places=3, default=0,
        verbose_name='Peso (KG)',
        help_text='Peso de la prenda en kilogramos'
    )
    tipo_limpieza = models.CharField(
        max_length=30,
        choices=TIPOS_LIMPIEZA,
        default='detergente',
        help_text="Tipo de limpieza/insumos que requiere esta prenda"
    )
    activo = models.BooleanField(default=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = 'Prenda'
        verbose_name_plural = 'Prendas'

    def get_insumos_requeridos(self):
        mapa_insumos = {
            'detergente': ['detergente'],
            'detergente_delicado': ['detergente'],
            'detergente_suave': ['detergente'],
            'detergente_suavizante': ['detergente', 'suavizante'],
            'detergente_voluminosa': ['detergente'],
            'lavado_seco': ['limpieza_especializada'],
            'limpieza_general': ['detergente'],
            'limpieza_especializada': ['limpieza_especializada'],
            'detergente_especial': ['detergente'],
            'detergente_especial_otros': ['detergente'],
        }

        return mapa_insumos.get(self.tipo_limpieza, ['detergente'])

    def __str__(self):
        return f"{self.nombre} - {self.peso_kg} KG - ${self.precio}"


class Servicio(models.Model):
    """Modelo para almacenar los tipos de servicios y sus precios"""
    TIPO_CHOICES = [
        ('autoservicio', 'Autoservicio'),
        ('por_encargo', 'Por encargo'),
        ('a_domicilio', 'A domicilio'),
        ('tintoreria', 'Tintoreria'),
    ]
    nombre = models.CharField(max_length=100, unique=True)
    tipo = models.CharField(
        max_length=20, choices=TIPO_CHOICES, default='autoservicio')
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['tipo', 'nombre']
        verbose_name = 'Servicio'
        verbose_name_plural = 'Servicios'

    def __str__(self):
        return f"{self.nombre} - ${self.precio}"


class DudaQueja(models.Model):
    ESTADOS = (
        ('pendiente', 'Pendiente'),
        ('en_proceso', 'En Proceso'),
        ('resuelto', 'Resuelto'),
    )
    cliente = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, related_name='dudas_quejas')
    comentario = models.TextField()
    respuesta = models.TextField(blank=True, null=True)
    estado = models.CharField(
        max_length=20, choices=ESTADOS, default='pendiente')
    fecha_creacion = models.DateTimeField(default=timezone.now)
    fecha_resolucion = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = 'Duda o Queja'
        verbose_name_plural = 'Dudas y Quejas'

    def __str__(self):
        return f"{self.cliente.username} - {self.estado}"


class Pedido(models.Model):
    """Modelo para registrar los pedidos/servicios solicitados"""
    ESTADOS_PEDIDO = (
        ('pendiente', 'Pendiente'),
        ('en_proceso', 'En Proceso'),
        ('listo', 'Listo para entrega'),
        ('entregado', 'Entregado'),
        ('cancelado', 'Cancelado'),
    )
    ESTADOS_PAGO = (
        ('pendiente', 'Pendiente'),
        ('pagado', 'Pagado'),
    )
    ORIGENES = (
        ('cliente', 'Solicitado por cliente'),
        ('operador', 'Registrado por operador'),
    )

    folio = models.CharField(max_length=20, unique=True, blank=True)
    cliente = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, related_name='pedidos',
        limit_choices_to={'rol': 'cliente'}
    )
    servicio = models.ForeignKey(
        Servicio, on_delete=models.SET_NULL, null=True, blank=True
    )
    operador = models.ForeignKey(
        Usuario, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='pedidos_registrados',
        limit_choices_to={'rol__in': ['operador', 'admin']}
    )
    tipo_servicio = models.CharField(max_length=50)
    peso = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    subtotal_peso = models.DecimalField(
        max_digits=10, decimal_places=2, default=0)
    costo_servicio = models.DecimalField(
        max_digits=10, decimal_places=2, default=0)
    cantidad_prendas = models.IntegerField(default=0)
    observaciones = models.TextField(blank=True, null=True)
    cobija_tipo = models.CharField(max_length=50, blank=True, null=True)
    lavado_especial = models.BooleanField(default=False)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    metodo_pago = models.CharField(max_length=20, default='efectivo')
    estado = models.CharField(
        max_length=20, choices=ESTADOS_PEDIDO, default='pendiente')
    estado_pago = models.CharField(
        max_length=20, choices=ESTADOS_PAGO, default='pendiente')
    origen = models.CharField(
        max_length=20, choices=ORIGENES, default='cliente')
    fecha_recepcion = models.DateTimeField(default=timezone.now)
    fecha_entrega_estimada = models.DateField(blank=True, null=True)
    fecha_entrega_real = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-fecha_recepcion']
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'

    def save(self, *args, **kwargs):
        if not self.folio:
            import random
            import string
            year = timezone.now().year
            random_part = ''.join(random.choices(
                string.ascii_uppercase + string.digits, k=4))
            self.folio = f"CK-{year}-{random_part}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.folio} - {self.cliente.username}"


class DetallePedido(models.Model):
    pedido = models.ForeignKey(
        Pedido, on_delete=models.CASCADE, related_name='detalles')
    prenda = models.ForeignKey(Prenda, on_delete=models.SET_NULL, null=True)
    cantidad = models.IntegerField(default=1)
    peso = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    precio_unitario = models.DecimalField(
        max_digits=10, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        self.subtotal = self.precio_unitario * self.cantidad
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.pedido.folio} - {self.prenda.nombre if self.prenda else 'Sin prenda'}"


class MovimientoOperador(models.Model):
    ACCIONES = (
        ('creo_ticket', 'Creo ticket'),
        ('entrego', 'Entrego'),
        ('cambio_precio', 'Cambio precio'),
        ('elimino', 'Elimino'),
        ('actualizo', 'Actualizo'),
        ('registro_servicio', 'Registro servicio'),
    )
    operador = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, related_name='movimientos',
        limit_choices_to={'rol__in': ['operador', 'admin']}
    )
    accion = models.CharField(max_length=30, choices=ACCIONES)
    detalles = models.CharField(max_length=255)
    pedido = models.ForeignKey(
        Pedido, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='movimientos'
    )
    fecha = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Movimiento de Operador'
        verbose_name_plural = 'Movimientos de Operadores'

    def __str__(self):
        return f"{self.operador.username} - {self.accion}"


class Incidencia(models.Model):
    PRIORIDADES = (
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    )
    ESTADOS = (
        ('pendiente', 'Pendiente'),
        ('en_proceso', 'En Proceso'),
        ('resuelto', 'Resuelto'),
    )
    trabajador = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, related_name='incidencias')
    asunto = models.CharField(
        max_length=200, verbose_name="Asunto del Problema")
    descripcion = models.TextField(verbose_name="Descripción Detallada")
    prioridad = models.CharField(
        max_length=20, choices=PRIORIDADES, default='media')
    estado = models.CharField(
        max_length=20, choices=ESTADOS, default='pendiente')
    evidencia = models.FileField(
        upload_to='incidencias/', blank=True, null=True, verbose_name="Evidencia")
    fecha_reporte = models.DateTimeField(default=timezone.now)
    fecha_resolucion = models.DateTimeField(blank=True, null=True)
    respuesta = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-fecha_reporte']
        verbose_name = 'Incidencia'
        verbose_name_plural = 'Incidencias'

    def __str__(self):
        return f"{self.asunto} - {self.trabajador.username}"
