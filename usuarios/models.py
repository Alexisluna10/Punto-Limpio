from django.db import models
from django.contrib.auth.models import AbstractUser


class Usuario(AbstractUser):
    ROLES = (
        ('admin', 'Administrador'),
        ('operador', 'Operador'),
        ('cliente', 'Cliente'),
    )

    rol = models.CharField(max_length=10, choices=ROLES, default='cliente')
    telefono = models.CharField(max_length=15, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.username} - {self.get_rol_display()}"
