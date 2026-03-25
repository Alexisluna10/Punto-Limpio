from django.db import models
from django.utils import timezone
from django.conf import settings
from apps.usuarios.models import Usuario
# IMPORTANTE: Aquí conectamos inventario con servicios
from apps.servicios.models import Pedido

class Insumo(models.Model):
    CATEGORIAS = [
        ('detergente', 'Detergentes'),
        ('suavizante', 'Suavizantes'),
        ('limpieza', 'Limpieza General'),
        ('otros', 'Otros'),
    ]
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código/Lote")
    categoria = models.CharField(max_length=20, choices=CATEGORIAS, default='detergente')
    stock_actual = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    capacidad_maxima = models.DecimalField(
        max_digits=10, decimal_places=2, default=100.0, help_text="Capacidad total")
    unidad_medida = models.CharField(max_length=10, default='Lts', verbose_name="Unidad")
    precio = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def porcentaje(self):
        if self.capacidad_maxima > 0:
            return int((self.stock_actual / self.capacidad_maxima) * 100)
        return 0

    def color_barra(self):
        p = self.porcentaje()
        if p <= 10: return 'nivel-bajo'
        if p <= 40: return 'nivel-medio'
        return 'nivel-alto'
    
    def estado_alerta(self):
        """Retorna True si el stock esta en nivel critico (10% o menos)"""
        return self.porcentaje() <= 10

    def __str__(self):
        return f"{self.nombre} ({self.stock_actual} {self.unidad_medida})"

class NotificacionStock(models.Model):
    insumo = models.ForeignKey(Insumo, on_delete=models.CASCADE)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    atendida = models.BooleanField(default=False)

    def __str__(self):
        return f"Alerta sobre {self.insumo.nombre}"

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
    nombre = models.CharField(max_length=50, unique=True, verbose_name="Identificador")
    tipo = models.CharField(max_length=20, choices=TIPOS, default='lavadora')
    estado = models.CharField(max_length=20, choices=ESTADOS, default='disponible')
    descripcion_falla = models.TextField(blank=True, null=True)
    
    # Aquí usamos el Pedido importado desde servicios
    pedido_actual = models.ForeignKey(
        Pedido, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='maquina_asignada'
    )
    hora_inicio_uso = models.DateTimeField(null=True, blank=True)
    tiempo_asignado = models.IntegerField(default=0, help_text="Tiempo en minutos")

    def tiempo_restante(self):
        if not self.hora_inicio_uso or self.estado != 'ocupado':
            return 0
        ahora = timezone.now()
        tiempo_transcurrido = (ahora - self.hora_inicio_uso).total_seconds() / 60
        restante = self.tiempo_asignado - tiempo_transcurrido
        return max(0, int(restante))

    def __str__(self):
        return f"{self.nombre} ({self.get_estado_display()})"

class MovimientoInsumo(models.Model):
    """Registro de movimientos/consumos de insumos"""
    TIPOS_MOVIMIENTO = (
        ('consumo_automatico', 'Consumo automatico por pedido'),
        ('reabastecimiento', 'Reabastecimiento'),
        ('ajuste_manual', 'Ajuste manual'),
    )
    insumo = models.ForeignKey(
        Insumo, on_delete=models.SET_NULL, null=True, blank=True, related_name='movimientos')
    insumo_nombre = models.CharField(max_length=100, blank=True, null=True)
    insumo_unidad = models.CharField(max_length=10, blank=True, null=True)
    
    # Aquí usamos el Pedido importado desde servicios
    pedido = models.ForeignKey(
        Pedido, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='movimientos_insumos')
    
    tipo_movimiento = models.CharField(
        max_length=30, choices=TIPOS_MOVIMIENTO, default='consumo_automatico')
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    stock_anterior = models.DecimalField(max_digits=10, decimal_places=2)
    stock_nuevo = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Movimiento de Insumo'
        verbose_name_plural = 'Movimientos de Insumos'

    def save(self, *args, **kwargs):
        if self.insumo and not self.insumo_nombre:
            self.insumo_nombre = self.insumo.nombre
            self.insumo_unidad = self.insumo.unidad_medida
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_insumo_nombre()} - {self.cantidad}"
    
    def get_insumo_nombre(self):
        if self.insumo: return self.insumo.nombre
        return self.insumo_nombre or 'Producto eliminado'