from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario

# Se agregó este porque modificamos el usuario personalizado para registrar las cuentas
admin.site.register(Usuario, UserAdmin)
