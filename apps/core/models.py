from django.db import models

class ConfiguracionNegocio(models.Model):
    nombre = models.CharField(max_length=200, default='Punto Limpio')
    direccion = models.CharField(max_length=300, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    horario = models.CharField(
        max_length=200, default='Lun-Vie: 8:00-20:00, Sáb: 9:00-18:00')

    class Meta:
        verbose_name = 'Configuración del Negocio'

    def __str__(self):
        return self.nombre