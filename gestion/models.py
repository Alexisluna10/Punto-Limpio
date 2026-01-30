from usuarios.models import Usuario
from django.utils import timezone
from django.db import models
from django.conf import settings


# Esta función es para crear la tabla de insumos que funcionará como un inventario/vista


class Insumo(models.Model):
    CATEGORIAS = [
        ('detergente', 'Detergentes'),
        ('suavizante', 'Suavizantes'),
        ('limpieza', 'Limpieza General'),
        ('otros', 'Otros'),
    ]

    nombre = models.CharField(max_length=100)
    codigo = models.CharField(
        max_length=50, unique=True, verbose_name="Código/Lote")
    categoria = models.CharField(
        max_length=20, choices=CATEGORIAS, default='detergente')

    stock_actual = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.0)
    capacidad_maxima = models.DecimalField(
        max_digits=10, decimal_places=2, default=100.0, help_text="Capacidad total del contenedor (para calcular %)")
    unidad_medida = models.CharField(
        max_length=10, default='Lts', verbose_name="Unidad")

    precio = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def porcentaje(self):
        if self.capacidad_maxima > 0:
            return int((self.stock_actual / self.capacidad_maxima) * 100)
        return 0

    def estado_alerta(self):
        """Devuelve True si el stock es crítico (menor o igual al 10%)"""
        return self.porcentaje() <= 10

    def color_barra(self):
        p = self.porcentaje()
        if p <= 10:
            return 'nivel-bajo'
        if p <= 40:
            return 'nivel-medio'
        return 'nivel-alto'

    def __str__(self):
        return f"{self.nombre} ({self.stock_actual} {self.unidad_medida})"


# Esta funcion es para crear la tabla de notificaciones vista administrador
class NotificacionStock(models.Model):
    insumo = models.ForeignKey(Insumo, on_delete=models.CASCADE)

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    fecha = models.DateTimeField(auto_now_add=True)
    atendida = models.BooleanField(default=False)

    def __str__(self):
        return f"Alerta de {self.usuario} sobre {self.insumo.nombre}"

# Create your models here.


class Prenda(models.Model):
    """Modelo para almacenar los tipos de prendas y sus precios"""
    nombre = models.CharField(max_length=100, unique=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    activo = models.BooleanField(default=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = 'Prenda'
        verbose_name_plural = 'Prendas'

    def __str__(self):
        return f"{self.nombre} - ${self.precio}"


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
        return f"{self.cliente.username} - {self.estado} - {self.fecha_creacion.strftime('%d/%m/%Y')}"


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

    # Generar folio automatico
    folio = models.CharField(max_length=20, unique=True, blank=True)

    # Relaciones
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

    # Detalles del servicio
    tipo_servicio = models.CharField(max_length=50)
    peso = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cantidad_prendas = models.IntegerField(default=0)
    observaciones = models.TextField(blank=True, null=True)

    # Cobijas/Edredones
    cobija_tipo = models.CharField(max_length=50, blank=True, null=True)
    lavado_especial = models.BooleanField(default=False)

    # Precios
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    metodo_pago = models.CharField(max_length=20, default='efectivo')

    # Estados
    estado = models.CharField(
        max_length=20, choices=ESTADOS_PEDIDO, default='pendiente')
    estado_pago = models.CharField(
        max_length=20, choices=ESTADOS_PAGO, default='pendiente')
    origen = models.CharField(
        max_length=20, choices=ORIGENES, default='cliente')

    # Fechas
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
            # Generar folio unico: CK-YYYY-XXXX
            year = timezone.now().year
            random_part = ''.join(random.choices(
                string.ascii_uppercase + string.digits, k=4))
            self.folio = f"CK-{year}-{random_part}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.folio} - {self.cliente.username} - {self.tipo_servicio}"


class DetallePedido(models.Model):
    """Detalles de las prendas incluidas en un pedido"""
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
    """Registro de movimientos/acciones realizadas por operadores"""
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
        return f"{self.operador.username} - {self.accion} - {self.fecha.strftime('%d/%m/%Y %H:%M')}"

# Modelo para las máquinas  vista/TRABAJADOR


class Maquina(models.Model):
    TIPOS = (
        ('lavadora', 'Lavadora'),
        ('secadora', 'Secadora'),
    )
    ESTADOS = (
        ('disponible', 'Disponible'),
        ('ocupado', 'Ocupado'),
        ('mantenimiento', 'Mantenimiento'),
    )

    nombre = models.CharField(
        max_length=50, unique=True, verbose_name="Identificador")
    tipo = models.CharField(max_length=20, choices=TIPOS, default='lavadora')
    estado = models.CharField(
        max_length=20, choices=ESTADOS, default='disponible')

    descripcion_falla = models.TextField(blank=True, null=True)

    pedido_actual = models.ForeignKey(
        'Pedido', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='maquina_asignada'
    )
    hora_inicio_uso = models.DateTimeField(null=True, blank=True)
    tiempo_asignado = models.IntegerField(
        default=0, help_text="Tiempo en minutos")

    def tiempo_restante(self):
        """Calcula los minutos restantes basado en la hora de inicio y el tiempo asignado"""
        if not self.hora_inicio_uso or self.estado != 'ocupado':
            return 0
        ahora = timezone.now()
        tiempo_transcurrido = (
            ahora - self.hora_inicio_uso).total_seconds() / 60
        restante = self.tiempo_asignado - tiempo_transcurrido
        return max(0, int(restante))

    def __str__(self):
        return f"{self.nombre} ({self.get_estado_display()})"


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
        return f"{self.asunto} - {self.trabajador.username} - {self.get_prioridad_display()}"
    