from django.contrib import admin
from .models import Prenda, Servicio, Incidencia, DudaQueja


@admin.register(Prenda)
class PrendaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio', 'activo', 'fecha_actualizacion')
    list_filter = ('activo',)
    search_fields = ('nombre',)
    list_editable = ('precio', 'activo')


@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'precio',
                    'activo', 'fecha_actualizacion')
    list_filter = ('activo', 'tipo')
    search_fields = ('nombre',)
    list_editable = ('precio', 'activo')


@admin.register(Incidencia)
class IncidenciaAdmin(admin.ModelAdmin):
    list_display = ('asunto', 'trabajador', 'prioridad',
                    'estado', 'fecha_reporte')
    list_filter = ('estado', 'prioridad', 'fecha_reporte')
    search_fields = ('asunto', 'descripcion', 'trabajador__username')
    readonly_fields = ('fecha_reporte', 'fecha_resolucion')
    fieldsets = (
        ('Información General', {
            'fields': ('trabajador', 'asunto', 'descripcion', 'prioridad', 'evidencia')
        }),
        ('Estado', {
            'fields': ('estado', 'respuesta', 'fecha_reporte', 'fecha_resolucion')
        }),
    )


@admin.register(DudaQueja)
class DudaQuejaAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'estado', 'fecha_creacion')
    list_filter = ('estado', 'fecha_creacion')
    search_fields = ('comentario', 'cliente__username')
    readonly_fields = ('fecha_creacion', 'fecha_resolucion')
    