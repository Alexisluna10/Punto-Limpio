from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario

class CustomUserAdmin(UserAdmin):
    # Esto agrega tus campos a la pantalla de edición del usuario
    fieldsets = UserAdmin.fieldsets + (
        ('Información Extra', {'fields': ('rol', 'telefono', 'direccion')}),
    )
    # Esto hace que el rol aparezca en la lista general de usuarios
    list_display = ['username', 'email', 'rol', 'is_staff']

# Registramos el modelo con la nueva configuración
admin.site.register(Usuario, CustomUserAdmin)
