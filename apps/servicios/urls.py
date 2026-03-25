from django.urls import path
from . import views

app_name = 'servicios'

urlpatterns = [
    # --- Paneles ---
    path('panel-trabajador/', views.trabajador_dashboard, name='trabajador_dashboard'),
    path('mis-pedidos/', views.cliente_dashboard, name='cliente_dashboard'),

    # --- Operación Trabajador ---
    path('nuevo-servicio/', views.nuevo_servicio, name='nuevo_servicio'),
    path('panel-trabajador/validar-ticket/', views.validar_ticket, name='validar_ticket'),
    path('panel-trabajador/incidencias/', views.incidencias, name='incidencias'),
    path('panel-trabajador/detalle-servicio/<int:pedido_id>/', views.detalle_servicio, name='detalle_servicio'),
    path('panel-trabajador/historial/', views.historial_servicios, name='historial_servicios'),
    path('panel-trabajador/proceso/', views.servicios_proceso, name='servicios_proceso'),
    path('imprimir-ticket/<int:pedido_id>/', views.imprimir_ticket, name='imprimir_ticket'),

    # --- Cliente ---
    path('solicitar-servicio/', views.solicitar_servicio, name='solicitar_servicio'),
    path('rastrear-servicio/', views.rastrear_servicio, name='rastrear_servicio'),
    path('dudas-quejas/', views.dudas_quejas, name='dudas_quejas'),
    path('autoservicio/', views.autoservicio, name='autoservicio'),
    path('seleccionar-servicio/', views.seleccionar_servicio, name='seleccionar_servicio'),
    path('servicios-costos/', views.servCosto, name='servCosto'),
    path('terminado/', views.terminado, name='terminado'),
    path('rastreo/<int:pedido_id>/', views.rastreo_qr, name='rastreo_qr'),
    path('buscar-pedido-rastreo/', views.buscar_pedido_rastreo, name='buscar_pedido_rastreo'),

    # --- Admin Configuración Servicios ---
    path('panel-admin/incidencias/', views.admin_incidencias, name='admin_incidencias'),
    path('panel-admin/precios/', views.admin_precios, name='admin_precios'),

    # --- APIs ---
    path('api/buscar-folio/', views.api_buscar_por_folio, name='api_buscar_folio'),
    path('api/entregar-pedido/', views.api_entregar_pedido, name='api_entregar_pedido'),
    path('api/actualizar-precio-prenda/', views.actualizar_precio_prenda, name='actualizar_precio_prenda'),
    path('api/actualizar-precio-servicio/', views.actualizar_precio_servicio, name='actualizar_precio_servicio'),
    path('api/agregar-prenda/', views.agregar_prenda, name='agregar_prenda'),
    path('api/agregar-servicio/', views.agregar_servicio, name='agregar_servicio'),
    path('api/eliminar-prenda/', views.eliminar_prenda, name='eliminar_prenda'),
    path('api/eliminar-servicio/', views.eliminar_servicio, name='eliminar_servicio'),
    path('api/obtener-precios/', views.obtener_precios_json, name='obtener_precios_json'),
]