from django.urls import path
from . import views

app_name = 'inventario'

urlpatterns = [
    # --- Admin Inventario ---
    path('panel-admin/inventarios/', views.admin_inventarios, name='admin_inventarios'),
    path('panel-admin/inventarios/editar/<int:id>/', views.editar_insumo, name='editar_insumo'),
    path('panel-admin/inventarios/eliminar/<int:id>/', views.eliminar_insumo, name='eliminar_insumo'),
    path('panel-admin/inventarios/detalles/', views.admin_detalles_inventario, name='admin_detalles_inventario'),

    # --- Trabajador Inventario ---
    path('panel-trabajador/inventario/', views.inventario, name='inventario'),
    path('panel-trabajador/estatus-maquinas/', views.estatus_maquina, name='estatus_maquina'),
    path('api/asignar-maquina/', views.asignar_maquina, name='asignar_maquina'),
]