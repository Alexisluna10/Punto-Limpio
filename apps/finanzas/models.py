from django.db import models
from django.utils import timezone
from apps.usuarios.models import Usuario

class CorteCaja(models.Model):
    """Modelo para registrar los cortes de caja diarios"""
    fecha = models.DateField(default=timezone.now)
    responsable = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, related_name='cortes_realizados')

    # Ventas registradas en sistema
    ventas_efectivo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    ventas_tarjeta = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    ventas_transferencia = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_ventas = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Dinero físico reportado
    efectivo_contado = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tarjeta_terminal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    transferencia_banco = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_fisico = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Diferencia y justificación
    diferencia = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    justificacion = models.TextField(blank=True, null=True)

    fecha_hora_registro = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Corte de Caja'
        verbose_name_plural = 'Cortes de Caja'
        unique_together = ['fecha', 'responsable']

    def __str__(self):
        return f"Corte {self.fecha.strftime('%d/%m/%Y')} - {self.responsable.username}"

    def calcular_diferencia(self):
        self.diferencia = self.total_fisico - self.total_ventas
        return self.diferencia

class GastoRenta(models.Model):
    """Modelo para el gasto de renta mensual del local"""
    monto_mensual = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    mes = models.IntegerField(choices=[(i, i) for i in range(1, 13)])
    anio = models.IntegerField(default=timezone.now().year)
    pagado = models.BooleanField(default=False)
    fecha_pago = models.DateField(blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Gasto de Renta'
        verbose_name_plural = 'Gastos de Renta'
        unique_together = ['mes', 'anio']
        ordering = ['-anio', '-mes']

    def __str__(self):
        return f"Renta {self.mes}/{self.anio} - ${self.monto_mensual}"

class GastoServicio(models.Model):
    """Modelo para los gastos de servicios (agua, luz, gas, internet)"""
    TIPOS_SERVICIO = (
        ('agua', 'Agua'),
        ('luz', 'Luz'),
        ('gas', 'Gas'),
        ('internet', 'Internet'),
    )

    tipo = models.CharField(max_length=20, choices=TIPOS_SERVICIO)
    monto_mensual = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    mes = models.IntegerField(choices=[(i, i) for i in range(1, 13)])
    anio = models.IntegerField(default=timezone.now().year)
    pagado = models.BooleanField(default=False)
    fecha_pago = models.DateField(blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Gasto de Servicio'
        verbose_name_plural = 'Gastos de Servicios'
        unique_together = ['tipo', 'mes', 'anio']
        ordering = ['-anio', '-mes', 'tipo']

    def __str__(self):
        return f"{self.get_tipo_display()} {self.mes}/{self.anio} - ${self.monto_mensual}"

class SalarioEmpleado(models.Model):
    """Modelo para los salarios de los empleados"""
    empleado = models.OneToOneField(
        Usuario, on_delete=models.CASCADE,
        related_name='salario',
        limit_choices_to={'rol__in': ['admin', 'operador']}
    )
    salario_semanal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    activo = models.BooleanField(default=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Salario de Empleado'
        verbose_name_plural = 'Salarios de Empleados'
        ordering = ['empleado__rol', 'empleado__username']

    def __str__(self):
        return f"{self.empleado.username} ({self.empleado.rol}) - ${self.salario_semanal}/semana"