from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.contrib.auth.models import Group
from django.utils import timezone
from django.db import models
from decimal import Decimal
from .models import Insumo, NotificacionStock, Maquina
import json

from usuarios.models import Usuario
from usuarios.forms import RegistroUsuarioAdminForm
from .models import Insumo, NotificacionStock, Prenda, Servicio, Pedido, DetallePedido, MovimientoOperador
from .forms_inventario import InsumoForm
from .utils import render_pdf_ticket, enviar_ticket_email
from django.urls import reverse
# Create your views here.


def prueba(request):
    return HttpResponse("Prueba app gestión")
    return HttpResponse("Prueba app gestion")


@login_required
def admin_dashboard(request):
    if not request.user.groups.filter(name='Administrador').exists():
        return redirect('tasks')
    return render(request, 'admin/dashboard.html')


@login_required
def admin_finanzas(request):
    if not request.user.groups.filter(name='Administrador').exists():
        return redirect('tasks')

    from datetime import datetime, timedelta
    from django.db.models import Sum, Count, F
    from .models import MovimientoInsumo, GastoOperativo

    hoy = timezone.now().date()

    # Determinar el período de filtro
    filtro = request.GET.get('filtro', 'hoy')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')

    if filtro == 'hoy':
        fecha_inicio = hoy
        fecha_fin = hoy
    elif filtro == 'semana':
        fecha_inicio = hoy - timedelta(days=7)
        fecha_fin = hoy
    elif filtro == 'mes':
        fecha_inicio = hoy.replace(day=1)
        fecha_fin = hoy
    elif filtro == 'personalizado' and fecha_desde and fecha_hasta:
        fecha_inicio = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
        fecha_fin = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
    else:
        fecha_inicio = hoy
        fecha_fin = hoy

    # ========== DATOS FINANCIEROS ==========
    # Pedidos pagados en el período
    pedidos_periodo = Pedido.objects.filter(
        fecha_recepcion_date_gte=fecha_inicio,
        fecha_recepcion_date_lte=fecha_fin,
        estado_pago='pagado'
    )

    # Ingresos totales
    ingresos_totales = pedidos_periodo.aggregate(
        total=Sum('total'))['total'] or Decimal('0')

    # Gastos en insumos (movimientos de entrada = compras)
    gastos_insumos = MovimientoInsumo.objects.filter(
        fecha_date_gte=fecha_inicio,
        fecha_date_lte=fecha_fin,
        tipo='entrada'
    ).aggregate(total=Sum('costo_total'))['total'] or Decimal('0')

    # Gastos operativos
    gastos_operativos_total = GastoOperativo.objects.filter(
        fecha__gte=fecha_inicio,
        fecha__lte=fecha_fin
    ).aggregate(total=Sum('monto'))['total'] or Decimal('0')

    # Utilidad neta
    utilidad_neta = ingresos_totales - gastos_insumos - gastos_operativos_total

    # ========== MÉTODOS DE PAGO ==========
    pago_efectivo = pedidos_periodo.filter(metodo_pago='efectivo').aggregate(
        total=Sum('total'))['total'] or Decimal('0')
    pago_tarjeta = pedidos_periodo.filter(metodo_pago='tarjeta').aggregate(
        total=Sum('total'))['total'] or Decimal('0')
    pago_transferencia = pedidos_periodo.filter(metodo_pago='transferencia').aggregate(
        total=Sum('total'))['total'] or Decimal('0')

    # Calcular porcentajes
    total_pagos = pago_efectivo + pago_tarjeta + pago_transferencia
    pct_efectivo = round((pago_efectivo / total_pagos * 100),
                         1) if total_pagos > 0 else 0
    pct_tarjeta = round((pago_tarjeta / total_pagos * 100),
                        1) if total_pagos > 0 else 0
    pct_transferencia = round(
        (pago_transferencia / total_pagos * 100), 1) if total_pagos > 0 else 0

    # ========== GRÁFICA DE PRENDAS ==========
    # Prendas más usadas y sus ganancias (desde DetallePedido)
    detalles_periodo = DetallePedido.objects.filter(
        pedido_fecha_recepciondate_gte=fecha_inicio,
        pedido_fecha_recepciondate_lte=fecha_fin,
        pedido__estado_pago='pagado'
    )

    prendas_stats = detalles_periodo.values(
        'prenda__nombre'
    ).annotate(
        cantidad_total=Sum('cantidad'),
        ganancia_total=Sum('subtotal')
    ).order_by('-cantidad_total')[:10]

    # Calcular porcentajes de prendas
    total_prendas = sum(p['cantidad_total']
                        for p in prendas_stats if p['cantidad_total']) if prendas_stats else 0
    prendas_data = []
    for prenda in prendas_stats:
        if prenda['prenda__nombre'] and prenda['cantidad_total']:
            pct = round(
                (prenda['cantidad_total'] / total_prendas * 100), 1) if total_prendas > 0 else 0
            prendas_data.append({
                'nombre': prenda['prenda__nombre'],
                'cantidad': prenda['cantidad_total'],
                'ganancia': float(prenda['ganancia_total'] or 0),
                'porcentaje': pct
            })

    # ========== GRÁFICA DE SERVICIOS ==========
    servicios_stats = pedidos_periodo.values(
        'tipo_servicio'
    ).annotate(
        cantidad=Count('id'),
        ganancia_total=Sum('total')
    ).order_by('-cantidad')

    total_servicios = sum(s['cantidad']
                          for s in servicios_stats) if servicios_stats else 0
    servicios_data = []
    for servicio in servicios_stats:
        pct = round((servicio['cantidad'] / total_servicios *
                    100), 1) if total_servicios > 0 else 0
        servicios_data.append({
            'nombre': servicio['tipo_servicio'] or 'Sin especificar',
            'cantidad': servicio['cantidad'],
            'ganancia': float(servicio['ganancia_total'] or 0),
            'porcentaje': pct
        })

    # ========== GRÁFICA DE INSUMOS ==========
    insumos_stats = MovimientoInsumo.objects.filter(
        fecha_date_gte=fecha_inicio,
        fecha_date_lte=fecha_fin,
        tipo='entrada'
    ).values(
        'insumo__nombre'
    ).annotate(
        cantidad_total=Sum('cantidad'),
        gasto_total=Sum('costo_total')
    ).order_by('-gasto_total')[:10]

    insumos_data = []
    for insumo in insumos_stats:
        if insumo['insumo__nombre']:
            insumos_data.append({
                'nombre': insumo['insumo__nombre'],
                'cantidad': float(insumo['cantidad_total'] or 0),
                'gasto': float(insumo['gasto_total'] or 0)
            })

    # ========== GRÁFICA DE GASTOS OPERATIVOS ==========
    gastos_operativos_stats = GastoOperativo.objects.filter(
        fecha__gte=fecha_inicio,
        fecha__lte=fecha_fin
    ).values(
        'categoria'
    ).annotate(
        total=Sum('monto'),
        cantidad=Count('id')
    ).order_by('-total')

    # Mapeo de categorías a nombres legibles
    categoria_nombres = dict(GastoOperativo.CATEGORIA_CHOICES)
    gastos_operativos_data = []
    for gasto in gastos_operativos_stats:
        gastos_operativos_data.append({
            'categoria': categoria_nombres.get(gasto['categoria'], gasto['categoria']),
            'total': float(gasto['total'] or 0),
            'cantidad': gasto['cantidad']
        })

    context = {
        'filtro': filtro,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        # Resumen financiero
        'ingresos_totales': ingresos_totales,
        'gastos_insumos': gastos_insumos,
        'gastos_operativos_total': gastos_operativos_total,
        'utilidad_neta': utilidad_neta,
        # Métodos de pago
        'pago_efectivo': pago_efectivo,
        'pago_tarjeta': pago_tarjeta,
        'pago_transferencia': pago_transferencia,
        'pct_efectivo': pct_efectivo,
        'pct_tarjeta': pct_tarjeta,
        'pct_transferencia': pct_transferencia,
        # Datos para gráficas (JSON)
        'prendas_json': json.dumps(prendas_data),
        'servicios_json': json.dumps(servicios_data),
        'insumos_json': json.dumps(insumos_data),
        'gastos_operativos_json': json.dumps(gastos_operativos_data),
        'metodos_pago_json': json.dumps([
            {'nombre': 'Efectivo', 'total': float(
                pago_efectivo), 'porcentaje': float(pct_efectivo)},
            {'nombre': 'Tarjeta', 'total': float(
                pago_tarjeta), 'porcentaje': float(pct_tarjeta)},
            {'nombre': 'Transferencia', 'total': float(
                pago_transferencia), 'porcentaje': float(pct_transferencia)},
        ]),
    }
    return render(request, 'admin/finanzas/finanzas.html', context)


@login_required
def admin_corte_caja(request):
    if not request.user.groups.filter(name='Administrador').exists():
        return redirect('tasks')
    return render(request, 'admin/finanzas/corte_caja.html')


@login_required
def admin_usuarios(request):
    if not request.user.groups.filter(name='Administrador').exists():
        return redirect('tasks')

    # Obtener trabajadores (operadores y admins)
    trabajadores = Usuario.objects.filter(rol__in=['operador', 'admin'])
    # Obtener clientes
    clientes = Usuario.objects.filter(rol='cliente')

    # Obtener la pestaña activa (por defecto clientes)
    tab = request.GET.get('tab', 'clientes')

    context = {
        'trabajadores': trabajadores,
        'clientes': clientes,
        'tab': tab,
        'total_trabajadores': trabajadores.count(),
        'total_clientes': clientes.count(),
    }
    return render(request, 'admin/usuarios/usuarios.html', context)


@login_required
def admin_nuevo_usuario(request):
    if not request.user.groups.filter(name='Administrador').exists():
        return redirect('tasks')

    if request.method == 'POST':
        form = RegistroUsuarioAdminForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            rol = form.cleaned_data['rol']
            user.rol = rol
            user.save()

            # Asignar al grupo correspondiente
            if rol == 'admin':
                grupo, created = Group.objects.get_or_create(
                    name='Administrador')
                user.groups.add(grupo)
            elif rol == 'operador':
                grupo, created = Group.objects.get_or_create(name='Trabajador')
                user.groups.add(grupo)
            # Los clientes no necesitan grupo especial

            messages.success(request, 'Usuario registrado exitosamente.')
            return redirect('admin_usuarios')
    else:
        form = RegistroUsuarioAdminForm()

    return render(request, 'admin/usuarios/nuevo_usuario.html', {'form': form})


@login_required
def admin_eliminar_usuario(request, usuario_id):
    if not request.user.groups.filter(name='Administrador').exists():
        return redirect('tasks')

    try:
        usuario = Usuario.objects.get(id=usuario_id)
        if usuario != request.user:  # No permitir eliminarse a si mismo
            usuario.delete()
            messages.success(request, 'Usuario eliminado exitosamente.')
        else:
            messages.error(request, 'No puedes eliminarte a ti mismo.')
    except Usuario.DoesNotExist:
        messages.error(request, 'Usuario no encontrado.')

    return redirect('admin_usuarios')


@login_required
def admin_precios(request):
    if not request.user.groups.filter(name='Administrador').exists():
        return redirect('tasks')

    prendas = Prenda.objects.filter(activo=True).order_by('nombre')
    servicios = Servicio.objects.filter(activo=True).order_by('tipo', 'nombre')
    return render(request, 'admin/precios.html', {
        'prendas': prendas,
        'servicios': servicios
    })


# APIs para gestion de precios
@login_required
@require_POST
def actualizar_precio_prenda(request):
    """Vista para actualizar el precio de una prenda via AJAX"""
    if not request.user.groups.filter(name='Administrador').exists():
        return JsonResponse({'success': False, 'mensaje': 'No autorizado'}, status=403)

    try:
        data = json.loads(request.body)
        prenda_id = data.get('id')
        nuevo_precio = data.get('precio')

        prenda = get_object_or_404(Prenda, id=prenda_id)
        prenda.precio = nuevo_precio
        prenda.save()

        return JsonResponse({'success': True, 'mensaje': 'Precio actualizado correctamente'})
    except Exception as e:
        return JsonResponse({'success': False, 'mensaje': str(e)}, status=400)


@login_required
@require_POST
def actualizar_precio_servicio(request):
    """Vista para actualizar el precio de un servicio via AJAX"""
    if not request.user.groups.filter(name='Administrador').exists():
        return JsonResponse({'success': False, 'mensaje': 'No autorizado'}, status=403)

    try:
        data = json.loads(request.body)
        servicio_id = data.get('id')
        nuevo_precio = data.get('precio')

        servicio = get_object_or_404(Servicio, id=servicio_id)
        servicio.precio = nuevo_precio
        servicio.save()

        return JsonResponse({'success': True, 'mensaje': 'Precio actualizado correctamente'})
    except Exception as e:
        return JsonResponse({'success': False, 'mensaje': str(e)}, status=400)


@login_required
@require_POST
def agregar_prenda(request):
    """Vista para agregar una nueva prenda"""
    if not request.user.groups.filter(name='Administrador').exists():
        return JsonResponse({'success': False, 'mensaje': 'No autorizado'}, status=403)

    try:
        data = json.loads(request.body)
        nombre = data.get('nombre')
        precio = data.get('precio')

        if Prenda.objects.filter(nombre=nombre).exists():
            return JsonResponse({'success': False, 'mensaje': 'Ya existe una prenda con ese nombre'}, status=400)

        prenda = Prenda.objects.create(nombre=nombre, precio=precio)
        return JsonResponse({
            'success': True,
            'mensaje': 'Prenda agregada correctamente',
            'prenda': {'id': prenda.id, 'nombre': prenda.nombre, 'precio': str(prenda.precio)}
        })
    except Exception as e:
        return JsonResponse({'success': False, 'mensaje': str(e)}, status=400)


@login_required
@require_POST
def agregar_servicio(request):
    """Vista para agregar un nuevo servicio"""
    if not request.user.groups.filter(name='Administrador').exists():
        return JsonResponse({'success': False, 'mensaje': 'No autorizado'}, status=403)

    try:
        data = json.loads(request.body)
        nombre = data.get('nombre')
        precio = data.get('precio')
        tipo = data.get('tipo', 'autoservicio')
        descripcion = data.get('descripcion', '')

        if Servicio.objects.filter(nombre=nombre).exists():
            return JsonResponse({'success': False, 'mensaje': 'Ya existe un servicio con ese nombre'}, status=400)

        servicio = Servicio.objects.create(
            nombre=nombre, precio=precio, tipo=tipo, descripcion=descripcion)
        return JsonResponse({
            'success': True,
            'mensaje': 'Servicio agregado correctamente',
            'servicio': {'id': servicio.id, 'nombre': servicio.nombre, 'precio': str(servicio.precio)}
        })
    except Exception as e:
        return JsonResponse({'success': False, 'mensaje': str(e)}, status=400)


@login_required
@require_POST
def eliminar_prenda(request):
    """Vista para eliminar (desactivar) una prenda"""
    if not request.user.groups.filter(name='Administrador').exists():
        return JsonResponse({'success': False, 'mensaje': 'No autorizado'}, status=403)

    try:
        data = json.loads(request.body)
        prenda_id = data.get('id')

        prenda = get_object_or_404(Prenda, id=prenda_id)
        prenda.activo = False
        prenda.save()

        return JsonResponse({'success': True, 'mensaje': 'Prenda eliminada correctamente'})
    except Exception as e:
        return JsonResponse({'success': False, 'mensaje': str(e)}, status=400)


@login_required
@require_POST
def eliminar_servicio(request):
    """Vista para eliminar (desactivar) un servicio"""
    if not request.user.groups.filter(name='Administrador').exists():
        return JsonResponse({'success': False, 'mensaje': 'No autorizado'}, status=403)

    try:
        data = json.loads(request.body)
        servicio_id = data.get('id')

        servicio = get_object_or_404(Servicio, id=servicio_id)
        servicio.activo = False
        servicio.save()

        return JsonResponse({'success': True, 'mensaje': 'Servicio eliminado correctamente'})
    except Exception as e:
        return JsonResponse({'success': False, 'mensaje': str(e)}, status=400)


def obtener_precios_json(request):
    """Vista para obtener los precios en formato JSON (para uso en JavaScript del cliente)"""
    prendas = list(Prenda.objects.filter(
        activo=True).values('id', 'nombre', 'precio'))
    servicios = list(Servicio.objects.filter(activo=True).values(
        'id', 'nombre', 'tipo', 'precio', 'descripcion'))

    # Convertir Decimal a string para JSON
    for prenda in prendas:
        prenda['precio'] = str(prenda['precio'])
    for servicio in servicios:
        servicio['precio'] = str(servicio['precio'])

    return JsonResponse({
        'prendas': prendas,
        'servicios': servicios
    })


@login_required
def buscar_clientes(request):
    """API para buscar clientes por nombre o telefono (solo rol cliente)"""
    query = request.GET.get('q', '').strip()

    if len(query) < 2:
        return JsonResponse({'clientes': []})

    clientes = Usuario.objects.filter(
        rol='cliente'
    ).filter(
        models.Q(username__icontains=query) |
        models.Q(first_name__icontains=query) |
        models.Q(last_name__icontains=query) |
        models.Q(telefono__icontains=query)
    )[:10]

    clientes_data = [{
        'id': c.id,
        'username': c.username,
        'nombre_completo': f"{c.first_name} {c.last_name}".strip() or c.username,
        'telefono': c.telefono or 'Sin telefono'
    } for c in clientes]

    return JsonResponse({'clientes': clientes_data})


@login_required
def admin_inventarios(request):
    if not request.user.groups.filter(name='Administrador').exists():
        return redirect('tasks')

    insumos = Insumo.objects.all().order_by('-fecha_actualizacion')

    notificaciones = NotificacionStock.objects.filter(
        atendida=False).select_related('insumo', 'usuario')

    if request.method == 'POST':
        form = InsumoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto agregado correctamente.')
            return redirect('admin_inventarios')
    else:
        form = InsumoForm()

    return render(request, 'admin/inventario/inventarios.html', {
        'insumos': insumos,
        'form': form,
        'notificaciones': notificaciones
    })

# Vista para editar inventario / vistaADMINISTRADOR


@login_required
@login_required
def editar_insumo(request, id):
    insumo = get_object_or_404(Insumo, id=id)

    if request.method == 'POST':
        form = InsumoForm(request.POST, instance=insumo)
        if form.is_valid():
            form.save()

            NotificacionStock.objects.filter(
                insumo=insumo, atendida=False).update(atendida=True)

            messages.success(
                request, 'Inventario actualizado y alertas resueltas.')
            return redirect('admin_inventarios')
        else:
            errores = form.errors.as_text()
            messages.error(request, f'Error al guardar: {errores}')

    return redirect('admin_inventarios')

# Vista para eliminar inventario / vista ADMINISTRADOR


@login_required
def eliminar_insumo(request, id):
    insumo = get_object_or_404(Insumo, id=id)
    insumo.delete()
    messages.success(request, 'Producto eliminado.')
    return redirect('admin_inventarios')


@login_required
@login_required
def admin_detalles_inventario(request):
    if not request.user.groups.filter(name='Administrador').exists():
        return redirect('tasks')

    insumos = Insumo.objects.all().order_by('nombre')

    return render(request, 'admin/inventario/detalles_inventario.html', {
        'insumos': insumos
    })


@login_required
def admin_historialVentas(request):
    if not request.user.groups.filter(name='Administrador').exists():
        return redirect('tasks')

    # Obtener TODOS los pedidos para el historial de ventas
    ventas = Pedido.objects.select_related(
        'cliente', 'servicio').order_by('-fecha_recepcion')

    # Filtrar por busqueda si hay
    busqueda = request.GET.get('buscar', '').strip()
    if busqueda:
        ventas = ventas.filter(
            models.Q(folio__icontains=busqueda) |
            models.Q(cliente__username__icontains=busqueda) |
            models.Q(cliente__first_name__icontains=busqueda)
        )

    context = {
        'ventas': ventas,
        'total_ventas': ventas.count(),
        'busqueda': busqueda
    }
    return render(request, 'admin/historial/historial-ventas.html', context)


@login_required
def admin_historialMovimientos(request):
    if not request.user.groups.filter(name='Administrador').exists():
        return redirect('tasks')

    # Obtener movimientos realizados por operadores
    movimientos = MovimientoOperador.objects.select_related(
        'operador', 'pedido'
    ).order_by('-fecha')

    # Obtener lista de operadores para el filtro
    operadores = Usuario.objects.filter(
        rol__in=['operador', 'admin']).order_by('username')

    context = {
        'movimientos': movimientos,
        'total_movimientos': movimientos.count(),
        'operadores': operadores
    }
    return render(request, 'admin/historial/historial-movimientos.html', context)


@login_required
def admin_detalleVenta(request, pedido_id=None):
    if not request.user.groups.filter(name='Administrador').exists():
        return redirect('tasks')

    pedido = None
    if pedido_id:
        pedido = get_object_or_404(Pedido, id=pedido_id)

    context = {
        'pedido': pedido
    }
    return render(request, 'admin/historial/detalle-venta.html', context)


@login_required
def admin_incidencias(request):
    from gestion.models import DudaQueja
    from django.http import JsonResponse
    if not request.user.groups.filter(name='Administrador').exists():
        return redirect('tasks')
    if request.method == 'POST':
        duda_id = request.POST.get('duda_id')
        respuesta = request.POST.get('respuesta')
        accion = request.POST.get('accion')

        try:
            duda = DudaQueja.objects.get(id=duda_id)
            if accion == 'resolver':
                duda.respuesta = respuesta
                duda.estdo = 'resuelto'
                duda.fecha_resolucion = timezone.now()
                duda.save()
                return JsonResponse({'success': True, 'message': 'Duda/queja resuelta.'})
            elif accion == 'en_proceso':
                duda.estado = 'en_proceso'
                duda.save()
                return JsonResponse({'success': True, 'message': 'Actualización en proceso.'})
        except DudaQueja.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Duda/queja no encontrada.'})
    dudas_quejas = DudaQueja.objects.select_related('cliente').all()
    context = {
        'dudas_quejas': dudas_quejas
    }
    return render(request, 'admin/incidencias.html', context)


@login_required
def admin_configuracion(request):
    if not request.user.groups.filter(name='Administrador').exists():
        return redirect('tasks')
    
    from .models import Incidencia, Insumo
    
    # Incidencias pendientes
    incidencias_pendientes = Incidencia.objects.exclude(estado='resuelto').count()
    
    # Productos con stock bajo (calculado manualmente)
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

@login_required
def trabajador_dashboard(request):
    return render(request, 'trabajador/dashboard.html')


@login_required
def nuevo_servicio(request):
    # Cargar datos para los selectores del formulario
    clientes = Usuario.objects.filter(rol='cliente').order_by('username')
    servicios = Servicio.objects.filter(activo=True)
    prendas = Prenda.objects.filter(activo=True)

    if request.method == 'POST':
        try:
            # 1. Procesar datos del Frontend
            data = json.loads(request.body)

            # Validación básica de cliente
            cliente_id = data.get('cliente_id')
            cliente = Usuario.objects.filter(
                id=cliente_id, rol='cliente').first()
            if not cliente:
                return JsonResponse({'success': False, 'message': 'Cliente no encontrado'}, status=400)

            # 2. Crear el objeto Pedido
            # Usamos Decimal() para asegurar que el dinero y peso se guarden exactos
            pedido = Pedido.objects.create(
                cliente=cliente,
                operador=request.user,
                tipo_servicio=data.get('tipo_servicio', 'por_encargo'),
                peso=Decimal(str(data.get('peso', 0))),
                cantidad_prendas=int(data.get('cantidad_prendas', 0)),
                observaciones=data.get('observaciones', ''),
                cobija_tipo=data.get('cobija_tipo', ''),
                lavado_especial=data.get('lavado_especial', False),
                total=Decimal(str(data.get('total', 0))),
                metodo_pago=data.get('metodo_pago', 'efectivo'),
                estado='pendiente',
                estado_pago='pendiente',
                origen='operador',
                # Si viene fecha, la guardamos, si no, se queda NULL
                fecha_entrega_estimada=data.get(
                    'fecha_entrega') if data.get('fecha_entrega') else None
            )

            # 3. Registrar el movimiento en el historial del operador
            MovimientoOperador.objects.create(
                operador=request.user,
                accion='registro_servicio',
                detalles=pedido.folio,
                pedido=pedido
            )

            # --- CORRECCIÓN CLAVE ---
            # Esto obliga a Django a releer el pedido desde la base de datos.
            # Arregla el problema de que el folio, fechas o datos relacionados salgan vacíos en el PDF.
            pedido.refresh_from_db()
            # ------------------------

            # 4. Generación de PDF y Envío de Correo
            mensaje_ticket = ""
            ticket_url = ""

            try:
                # Generamos el PDF en memoria
                pdf_bytes = render_pdf_ticket(pedido)

                if pdf_bytes:
                    # a) Crear la URL para que el JS abra el PDF
                    ticket_url = reverse('imprimir_ticket', args=[pedido.id])

                    # b) Enviar el PDF por correo
                    enviado = enviar_ticket_email(pedido, pdf_bytes)

                    if enviado:
                        mensaje_ticket = " y ticket enviado por correo."
                    else:
                        mensaje_ticket = " (Ticket generado, pero no se pudo enviar correo)."
                else:
                    mensaje_ticket = " (Nota: Error al generar el PDF visual)."

            except Exception as e:
                print(f"Error en proceso de ticket: {e}")
                # No detenemos el flujo, el pedido ya se guardó
                mensaje_ticket = " (Error técnico con el ticket PDF)."

            # 5. Respuesta Final al Frontend
            return JsonResponse({
                'success': True,
                'message': f'Servicio registrado correctamente{mensaje_ticket}',
                'folio': pedido.folio,
                'ticket_url': ticket_url  # Esta URL es la que usa el window.open()
            })

        except Exception as e:
            # Captura cualquier otro error (ej. base de datos, tipos de datos)
            return JsonResponse({'success': False, 'message': f"Error interno: {str(e)}"}, status=400)

    # Si es GET, mostramos el formulario
    return render(request, 'trabajador/servicio/nuevo_servicio.html', {
        'clientes': clientes,
        'servicios': servicios,
        'prendas': prendas
    })


@login_required
def validar_ticket(request):
    return render(request, 'trabajador/tickets/validar_ticket.html')


@login_required
def incidencias(request):
    return render(request, 'trabajador/incidencias/incidencias.html')


# Vista para el inventario / vista TRABAJADOR
@login_required
def inventario(request):
    insumos = Insumo.objects.all()

    if request.method == 'POST':
        producto_nombre = request.POST.get('producto_nombre')

        insumo_obj = Insumo.objects.filter(nombre=producto_nombre).first()

        if insumo_obj:
            NotificacionStock.objects.get_or_create(
                insumo=insumo_obj,
                atendida=False,
                defaults={'usuario': request.user}
            )
            messages.success(
                request, f'¡Aviso enviado al administrador sobre: {producto_nombre}!')

        return redirect('inventario')

    return render(request, 'trabajador/inventario/inventario.html', {'insumos': insumos})


@login_required
def servicios_proceso(request):
    # Obtener todos los pedidos que no estan entregados ni cancelados
    pedidos = Pedido.objects.filter(
        estado__in=['pendiente', 'en_proceso', 'listo']
    ).select_related('cliente').order_by('-fecha_recepcion')

    # Busqueda por folio o cliente
    busqueda = request.GET.get('buscar', '').strip()
    if busqueda:
        pedidos = pedidos.filter(
            models.Q(folio__icontains=busqueda) |
            models.Q(cliente__username__icontains=busqueda) |
            models.Q(cliente__first_name__icontains=busqueda) |
            models.Q(cliente__last_name__icontains=busqueda)
        )

    return render(request, 'trabajador/procedimiento/servicios_proceso.html', {
        'pedidos': pedidos,
        'busqueda': busqueda
    })


@login_required
def detalle_servicio(request, pedido_id=None):
    pedido = get_object_or_404(Pedido, id=pedido_id) if pedido_id else None

    # 1. Obtener máquinas disponibles para enviarlas al Modal de selección
    lavadoras_disp = Maquina.objects.filter(
        estado='disponible', tipo='lavadora')
    secadoras_disp = Maquina.objects.filter(
        estado='disponible', tipo='secadora')

    if request.method == 'POST' and pedido:
        try:
            data = json.loads(request.body)
            nuevo_estado = data.get('estado')
            estado_pago = data.get('estado_pago')
            notas = data.get('notas', '')

            # Datos de la máquina (si vienen)
            maquina_id = data.get('maquina_id')
            tiempo_asignado = data.get('tiempo_asignado', 30)

            # Actualizar estado del pedido
            if nuevo_estado:
                pedido.estado = nuevo_estado
                if nuevo_estado == 'entregado':
                    pedido.fecha_entrega_real = timezone.now()

            # --- LÓGICA DE MÁQUINA ---
            # Si pasamos a "en_proceso" y seleccionaron una máquina
            if nuevo_estado == 'en_proceso' and maquina_id:
                maquina = Maquina.objects.get(id=maquina_id)
                if maquina.estado == 'disponible':
                    maquina.estado = 'ocupado'
                    maquina.pedido_actual = pedido  # Vinculamos el cliente
                    maquina.hora_inicio_uso = timezone.now()  # Iniciamos cronómetro
                    maquina.tiempo_asignado = int(tiempo_asignado)
                    maquina.save()

                    # Agregamos nota automática
                    if pedido.observaciones:
                        pedido.observaciones += f"\n[Sistema] Asignado a {maquina.nombre}"
                    else:
                        pedido.observaciones = f"[Sistema] Asignado a {maquina.nombre}"
            # -------------------------

            # Actualizar estado de pago
            if estado_pago:
                pedido.estado_pago = estado_pago

            # Agregar observaciones manuales
            if notas:
                if pedido.observaciones:
                    pedido.observaciones += f"\n{notas}"
                else:
                    pedido.observaciones = notas

            pedido.save()

            # Registrar movimiento del operador
            MovimientoOperador.objects.create(
                operador=request.user,
                accion='actualizo',
                detalles=f"Actualizo pedido {pedido.folio} - Estado: {nuevo_estado}",
                pedido=pedido
            )

            return JsonResponse({
                'success': True,
                'message': 'Pedido actualizado y máquina asignada correctamente'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)

    return render(request, 'trabajador/procedimiento/detalle_servicio.html', {
        'pedido': pedido,
        'lavadoras': lavadoras_disp,
        'secadoras': secadoras_disp
    })


@login_required
def estatus_maquina(request):
    return render(request, 'trabajador/estatus/estatus_maquina.html')


@login_required
@require_POST
def asignar_maquina(request):
    """
    Asigna un pedido a una máquina, cambia su estado a ocupado e inicia el contador.
    """
    import json
    try:
        data = json.loads(request.body)
        pedido_id = data.get('pedido_id')
        maquina_id = data.get('maquina_id')
        tiempo = int(data.get('tiempo', 30))  # Tiempo por defecto 30 min

        pedido = get_object_or_404(Pedido, id=pedido_id)
        maquina = get_object_or_404(Maquina, id=maquina_id)

        if maquina.estado != 'disponible':
            return JsonResponse({'success': False, 'message': 'La máquina no está disponible.'})

        # Actualizar Máquina
        maquina.estado = 'ocupado'
        maquina.pedido_actual = pedido
        maquina.hora_inicio_uso = timezone.now()
        maquina.tiempo_asignado = tiempo
        maquina.save()

        # Actualizar Estado del Pedido
        if maquina.tipo == 'lavadora':
            pedido.estado = 'en_proceso'  # O crea un estado específico 'lavando' si prefieres
            # Aquí podrías agregar notas al pedido indicando que inició lavado
        elif maquina.tipo == 'secadora':
            # Lógica similar para secado
            pass

        pedido.save()

        return JsonResponse({'success': True, 'message': f'Máquina {maquina.nombre} asignada al folio {pedido.folio}'})

    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required
def cliente_dashboard(request):
    # Obtener pedidos activos del cliente (no entregados ni cancelados)
    pedidos_activos = Pedido.objects.filter(
        cliente=request.user
    ).exclude(
        estado__in=['entregado', 'cancelado']
    ).order_by('-fecha_recepcion')

    # Obtener pedidos finalizados del cliente
    pedidos_finalizados = Pedido.objects.filter(
        cliente=request.user,
        estado='entregado'
    ).order_by('-fecha_entrega_real')

    context = {
        'pedidos_activos': pedidos_activos,
        'pedidos_finalizados': pedidos_finalizados,
    }
    return render(request, 'cliente/dashboard.html', context)


@login_required
def solicitar_servicio(request):
    servicios = Servicio.objects.filter(activo=True)
    return render(request, 'cliente/solicitar_servicio.html', {'servicios': servicios})


@login_required
def perfil(request):
    return render(request, 'cliente/perfil.html')


@login_required
def rastrear_servicio(request):
    return render(request, 'cliente/rastrear_servicio.html')


@login_required
def dudas_quejas(request):
    from gestion.models import DudaQueja

    if request.method == 'POST':
        comentario = request.POST.get('comentario')
        if comentario and comentario.strip():
            DudaQueja.objects.create(
                cliente=request.user,
                comentario=comentario.strip()
            )
            return JsonResponse({'success': True, 'message': 'Tu comentario ha sido enviado exitosamente.'})
        return JsonResponse({'success': False, 'message': 'El comentario no puede estar vacío.'})

    # Obtener el historial de dudas/quejas del cliente actual
    mis_dudas = DudaQueja.objects.filter(
        cliente=request.user).order_by('-fecha_creacion')

    context = {
        'mis_dudas': mis_dudas
    }
    return render(request, 'cliente/dudas_quejas.html', context)


@login_required
def autoservicio(request):
    # Obtener precios de servicios de autoservicio
    servicios_autoservicio = Servicio.objects.filter(
        activo=True, tipo='autoservicio')

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            servicio_id = data.get('servicio_id')
            servicio_nombre = data.get('servicio_nombre')
            total = Decimal(str(data.get('total', 0)))
            metodo_pago = data.get('metodo_pago', 'efectivo')

            servicio = Servicio.objects.filter(
                id=servicio_id).first() if servicio_id else None

            # Crear el pedido
            pedido = Pedido.objects.create(
                cliente=request.user,
                servicio=servicio,
                tipo_servicio='Autoservicio' if not servicio_nombre else servicio_nombre,
                total=total,
                metodo_pago=metodo_pago,
                estado='pendiente',
                estado_pago='pendiente',
                origen='cliente'
            )

            return JsonResponse({
                'success': True,
                'message': 'Servicio registrado exitosamente',
                'folio': pedido.folio
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)

    return render(request, 'cliente/autoservicio.html', {
        'servicios': servicios_autoservicio
    })


@login_required
def seleccionar_servicio(request):
    return render(request, 'cliente/seleccionar_servicio.html')


@login_required
def servCosto(request):
    # Obtener el tipo de servicio de la URL
    tipo_servicio = request.GET.get('tipo', 'por_encargo')

    # Mapear tipo a nombre legible
    tipos_nombres = {
        'autoservicio': 'Autoservicio',
        'por_encargo': 'Servicio por encargo',
        'a_domicilio': 'Servicio a domicilio',
        'tintoreria': 'Tintoreria',
    }
    tipo_servicio_nombre = tipos_nombres.get(tipo_servicio, 'Servicio')

    # Obtener el precio del servicio desde la BD
    servicio = Servicio.objects.filter(activo=True, tipo=tipo_servicio).first()
    servicio_precio = servicio.precio if servicio else 0

    # Obtener todas las prendas para el formulario
    prendas = Prenda.objects.filter(activo=True)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            prendas_data = data.get('prendas', [])
            total = Decimal(str(data.get('total', 0)))
            metodo_pago = data.get('metodo_pago', 'efectivo')
            tipo = data.get('tipo_servicio', tipo_servicio)

            # Crear el pedido
            pedido = Pedido.objects.create(
                cliente=request.user,
                servicio=servicio,
                tipo_servicio=tipos_nombres.get(tipo, tipo_servicio_nombre),
                total=total,
                metodo_pago=metodo_pago,
                cantidad_prendas=sum([p.get('cantidad', 0)
                                     for p in prendas_data]),
                peso=sum([Decimal(str(p.get('peso', 0)))
                         for p in prendas_data]),
                estado='pendiente',
                estado_pago='pendiente',
                origen='cliente'
            )

            # Crear detalles de prendas
            for prenda_data in prendas_data:
                prenda_obj = Prenda.objects.filter(
                    id=prenda_data.get('prenda_id')).first()
                if prenda_obj:
                    DetallePedido.objects.create(
                        pedido=pedido,
                        prenda=prenda_obj,
                        cantidad=prenda_data.get('cantidad', 1),
                        peso=Decimal(str(prenda_data.get('peso', 0))),
                        precio_unitario=Decimal(
                            str(prenda_data.get('precio', 0))),
                        subtotal=Decimal(str(prenda_data.get('subtotal', 0)))
                    )

            return JsonResponse({
                'success': True,
                'message': 'Servicio registrado exitosamente',
                'folio': pedido.folio
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)

    return render(request, 'cliente/servCosto.html', {
        'prendas': prendas,
        'tipo_servicio': tipo_servicio,
        'tipo_servicio_nombre': tipo_servicio_nombre,
        'servicio_precio': servicio_precio,
    })


@login_required
def terminado(request):
    return render(request, 'cliente/terminado.html')


@login_required
def tasks(request):
    user = request.user

    if user.groups.filter(name='Administrador').exists():
        return redirect('admin_dashboard')

    elif user.groups.filter(name='Trabajador').exists():
        return redirect('trabajador_dashboard')

    else:
        return redirect('cliente_dashboard')


@login_required
def estatus_maquina(request):
    if request.method == 'POST':
        accion = request.POST.get('accion')

        if accion == 'agregar':
            nombre = request.POST.get('nombre')
            tipo = request.POST.get('tipo')
            if nombre and tipo:
                Maquina.objects.create(nombre=nombre, tipo=tipo)
                messages.success(request, 'Máquina registrada correctamente.')

        elif accion == 'baja_definitiva':
            maquina_id = request.POST.get('maquina_id')
            Maquina.objects.filter(id=maquina_id).delete()
            messages.success(request, 'Máquina eliminada.')

        elif accion == 'reportar_mantenimiento':
            maquina_id = request.POST.get('maquina_id')
            maquina = get_object_or_404(Maquina, id=maquina_id)
            maquina.estado = 'mantenimiento'
            maquina.save()
            messages.warning(request, 'Máquina puesta en mantenimiento.')

        elif accion == 'toggle_uso':
            maquina_id = request.POST.get('maquina_id')
            maquina = get_object_or_404(Maquina, id=maquina_id)

            if maquina.estado == 'disponible':
                maquina.estado = 'ocupado'
            elif maquina.estado == 'ocupado':
                maquina.estado = 'disponible'

            maquina.save()

        elif accion == 'reactivar':
            maquina_id = request.POST.get('maquina_id')
            maquina = get_object_or_404(Maquina, id=maquina_id)
            maquina.estado = 'disponible'
            maquina.save()
            messages.success(request, 'Máquina reactivada y lista para usar.')

        return redirect('estatus_maquina')

    lavadoras = Maquina.objects.filter(tipo='lavadora').order_by('nombre')
    secadoras = Maquina.objects.filter(tipo='secadora').order_by('nombre')

    return render(request, 'trabajador/estatus/estatus_maquina.html', {
        'lavadoras': lavadoras,
        'secadoras': secadoras
    })


def incidencias(request):
    from gestion.models import Incidencia
    if request.method == 'POST':
        asunto = request.POST.get('asunto')
        descripcion = request.POST.get('descripcion')
        prioridad = request.POST.get('prioridad', 'media')
        evidencia = request.FILES.get('evidencia')

        if asunto and asunto.strip() and descripcion and descripcion.strip():
            incidencia = Incidencia.objects.create(
                trabajador=request.user,
                asunto=asunto.strip(),
                descripcion=descripcion.strip(),
                prioridad=prioridad,
                evidencia=evidencia
            )
            return JsonResponse({
                'success': True,
                'message': 'Incidencia reportada exitosamente.'
            })
        return JsonResponse({
            'success': False,
            'message': 'Por favor complete todos los campos requeridos.'
        })

    mis_incidencias = Incidencia.objects.filter(
        trabajador=request.user).order_by('-fecha_reporte')
    return render(request, 'trabajador/incidencias/incidencias.html', {
        'mis_incidencias': mis_incidencias
    })


def admin_incidencias(request):
    from gestion.models import DudaQueja, Incidencia
    from django.http import JsonResponse
    if not request.user.groups.filter(name='Administrador').exists():
        return redirect('tasks')
    if request.method == 'POST':
        tipo = request.POST.get('tipo', 'duda')
        accion = request.POST.get('accion')

        if tipo == 'duda':
            duda_id = request.POST.get('duda_id')
            respuesta = request.POST.get('respuesta')

            try:
                duda = DudaQueja.objects.get(id=duda_id)
                if accion == 'resolver':
                    duda.respuesta = respuesta
                    duda.estado = 'resuelto'
                    duda.fecha_resolucion = timezone.now()
                    duda.save()
                    return JsonResponse({'success': True, 'message': 'Duda/queja resuelta.'})
                elif accion == 'en_proceso':
                    duda.estado = 'en_proceso'
                    duda.save()
                    return JsonResponse({'success': True, 'message': 'Actualización en proceso.'})
            except DudaQueja.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Duda/queja no encontrada.'})

        elif tipo == 'incidencia':
            incidencia_id = request.POST.get('incidencia_id')
            respuesta = request.POST.get('respuesta')

            try:
                incidencia = Incidencia.objects.get(id=incidencia_id)
                if accion == 'resolver':
                    incidencia.respuesta = respuesta
                    incidencia.estado = 'resuelto'
                    incidencia.fecha_resolucion = timezone.now()
                    incidencia.save()
                    return JsonResponse({'success': True, 'message': 'Incidencia resuelta.'})
                elif accion == 'en_proceso':
                    incidencia.estado = 'en_proceso'
                    incidencia.save()
                    return JsonResponse({'success': True, 'message': 'Incidencia en proceso.'})
            except Incidencia.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Incidencia no encontrada.'})

    dudas_quejas = DudaQueja.objects.select_related('cliente').all()
    incidencias = Incidencia.objects.select_related('trabajador').all()

    context = {
        'dudas_quejas': dudas_quejas,
        'incidencias': incidencias
    }
    return render(request, 'admin/incidencias.html', context)


@login_required
def imprimir_ticket(request, pedido_id):
    """
    Vista para descargar el ticket PDF directamente en el navegador.
    """
    pedido = get_object_or_404(Pedido, id=pedido_id)

    # Usamos la función de utils para obtener el PDF
    pdf_bytes = render_pdf_ticket(pedido)

    if not pdf_bytes:
        return HttpResponse("Error al generar el ticket", status=500)

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    # 'inline' hace que se abra en el navegador (puedes cambiar a 'attachment' para forzar guardar)
    response['Content-Disposition'] = f'inline; filename="ticket_{pedido.folio}.pdf"'
    return response
