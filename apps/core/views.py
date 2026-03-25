from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from django.db.models import Sum
from django.contrib.auth.decorators import login_required

# --- IMPORTACIONES DEL PROYECTO ---
from apps.core.decorators import solo_admin, solo_trabajador, solo_cliente
from apps.usuarios.models import Usuario
from apps.servicios.models import Pedido, Incidencia, DudaQueja, Prenda
from apps.inventario.models import Insumo, Maquina

def prueba(request):
    return HttpResponse("Prueba app core funcionando")

@login_required
def tasks(request):
    user = request.user
    rol = user.rol

    if user.is_superuser or rol == 'admin':
        return redirect('core:admin_dashboard')
    elif rol == 'operador':
        return redirect('servicios:trabajador_dashboard')
    else:
        return redirect('servicios:cliente_dashboard')

@solo_admin
def admin_dashboard(request):

    hoy = timezone.now().date()
    inicio_semana = hoy - timedelta(days=7)
    inicio_mes = hoy.replace(day=1)

    # ========== GANANCIAS ==========
    # Hoy
    pedidos_hoy = Pedido.objects.filter(
        fecha_recepcion__date=hoy,
        estado_pago='pagado'
    )
    ganancias_hoy = pedidos_hoy.aggregate(total=Sum('total'))[
        'total'] or Decimal('0')
    servicios_hoy = pedidos_hoy.count()

    # Esta semana
    pedidos_semana = Pedido.objects.filter(
        fecha_recepcion__date__gte=inicio_semana,
        fecha_recepcion__date__lte=hoy,
        estado_pago='pagado'
    )
    ganancias_semana = pedidos_semana.aggregate(
        total=Sum('total'))['total'] or Decimal('0')
    servicios_semana = pedidos_semana.count()

    # Este mes
    pedidos_mes = Pedido.objects.filter(
        fecha_recepcion__date__gte=inicio_mes,
        fecha_recepcion__date__lte=hoy,
        estado_pago='pagado'
    )
    ganancias_mes = pedidos_mes.aggregate(total=Sum('total'))[
        'total'] or Decimal('0')
    servicios_mes = pedidos_mes.count()

    # ========== ALERTAS CRÍTICAS ==========
    # Insumos con stock crítico (<=10%)
    insumos_criticos = Insumo.objects.all()
    alertas_insumos = []
    for insumo in insumos_criticos:
        if insumo.porcentaje() <= 10:
            alertas_insumos.append({
                'texto': f'{insumo.nombre} al {insumo.porcentaje()}% de stock',
                'tipo': 'insumo'
            })

    # Incidencias recientes del personal (últimas 3 pendientes o en proceso)
    incidencias_recientes = Incidencia.objects.filter(
        estado__in=['pendiente', 'en_proceso']
    ).order_by('-fecha_reporte')[:3]

    # Dudas/Quejas recientes de clientes (últimas 3 pendientes o en proceso)
    dudas_recientes = DudaQueja.objects.filter(
        estado__in=['pendiente', 'en_proceso']
    ).order_by('-fecha_creacion')[:3]

    # ========== SERVICIOS ACTIVOS ==========
    servicios_totales = Pedido.objects.exclude(estado='entregado').count()
    servicios_pendientes = Pedido.objects.filter(estado='pendiente').count()
    servicios_proceso = Pedido.objects.filter(estado='en_proceso').count()
    servicios_listos = Pedido.objects.filter(estado='listo').count()

    # Máquinas en uso (lavado/secado)
    maquinas_lavado = Maquina.objects.filter(
        tipo='lavadora', estado='ocupado').count()
    maquinas_secado = Maquina.objects.filter(
        tipo='secadora', estado='ocupado').count()

    # ========== PRECIOS DE PRENDAS ==========
    # Obtener 5 prendas destacadas (las más caras o populares)
    prendas_destacadas = Prenda.objects.filter(
        activo=True).order_by('-precio')[:5]

    context = {
        # Ganancias
        'ganancias_hoy': ganancias_hoy,
        'servicios_hoy': servicios_hoy,
        'ganancias_semana': ganancias_semana,
        'servicios_semana': servicios_semana,
        'ganancias_mes': ganancias_mes,
        'servicios_mes': servicios_mes,

        # Alertas
        'alertas_insumos': alertas_insumos,
        'incidencias_recientes': incidencias_recientes,
        'dudas_recientes': dudas_recientes,

        # Servicios activos
        'servicios_totales': servicios_totales,
        'servicios_pendientes': servicios_pendientes,
        'servicios_proceso': servicios_proceso,
        'servicios_listos': servicios_listos,
        'maquinas_lavado': maquinas_lavado,
        'maquinas_secado': maquinas_secado,

        # Precios
        'prendas_destacadas': prendas_destacadas,
    }

    return render(request, 'core/dashboard_admin.html', context)

@solo_admin
def admin_configuracion(request):
    incidencias_pendientes = Incidencia.objects.exclude(
        estado='resuelto').count()
    productos_bajo_stock = 0
    for insumo in Insumo.objects.all():
        if insumo.capacidad_maxima > 0:
            porcentaje = (insumo.stock_actual / insumo.capacidad_maxima) * 100
            if porcentaje <= 10:
                productos_bajo_stock += 1

    context = {
        'incidencias_pendientes': incidencias_pendientes,
        'productos_bajo_stock': productos_bajo_stock,
    }

    return render(request, 'admin/configuracion.html', context)