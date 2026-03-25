from django.urls import path
from . import views

app_name = 'finanzas'

urlpatterns = [
    path('panel-admin/finanzas/', views.admin_finanzas, name='admin_finanzas'),
    path('panel-admin/finanzas/corte-caja/', views.admin_corte_caja, name='admin_corte_caja'),
    
    # --- Historiales ---
    path('panel-admin/historial/', views.admin_historialVentas, name='admin_historial'), # Alias
    path('panel-admin/historial/ventas/', views.admin_historialVentas, name='historial_ventas'),
    path('panel-admin/historial/movimientos/', views.admin_historialMovimientos, name='historial_movimientos'),
    path('panel-admin/historial/venta/<int:pedido_id>/', views.admin_detalleVenta, name='detalle_venta'),

    # --- Acciones de Guardado ---
    path('panel-admin/finanzas/guardar-renta/', views.guardar_gasto_renta, name='guardar_gasto_renta'),
    path('panel-admin/finanzas/guardar-servicio/', views.guardar_gasto_servicio, name='guardar_gasto_servicio'),
    path('panel-admin/finanzas/guardar-salario/', views.guardar_salario_empleado, name='guardar_salario_empleado'),

    # --- Exportar / Imprimir ---
    path('panel-admin/finanzas/exportar-excel/', views.exportar_finanzas_excel, name='exportar_finanzas_excel'),
    path('panel-admin/historial/ventas/exportar-excel/', views.exportar_historial_ventas_excel, name='exportar_historial_ventas_excel'),
    path('panel-admin/historial/movimientos/exportar-excel/', views.exportar_historial_movimientos_excel, name='exportar_historial_movimientos_excel'),
    path('panel-admin/finanzas/imprimir-reporte/', views.imprimir_reporte_finanzas, name='imprimir_reporte_finanzas'),
    path('panel-admin/finanzas/enviar-email/', views.enviar_reporte_email, name='enviar_reporte_email'),
    path('panel-admin/finanzas/corte-caja/imprimir/', views.imprimir_corte_caja, name='imprimir_corte_caja'),
]