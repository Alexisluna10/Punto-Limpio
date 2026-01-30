from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.contrib.auth.models import Group
from django.utils import timezone
from django.db.models import Q, Sum, Count
from decimal import Decimal
import json
from datetime import datetime, timedelta

# Modelos
from usuarios.models import Usuario
from usuarios.forms import RegistroUsuarioAdminForm
from .models import (
    Insumo, NotificacionStock, Prenda, Servicio, Pedido,
    DetallePedido, MovimientoOperador, Maquina,
    Incidencia, DudaQueja, MovimientoInsumo, GastoOperativo
)
from .forms_inventario import InsumoForm

# Utils
from .utils import render_pdf_ticket, enviar_ticket_email
from django.urls import reverse


def prueba(request):
    return HttpResponse("Prueba app gestión")


# ==========================================
#              VISTAS ADMINISTRADOR
# ==========================================

@login_required
def admin_dashboard(request):
    if not request.user.groups.filter(name='Administrador').exists():
        return redirect('tasks')
    return render(request, 'admin/dashboard.html')


@login_required
def admin_finanzas(request):
    if not request.user.groups.filter(name='Administrador').exists():
        return redirect('tasks')

    hoy = timezone.now().date()
    filtro = request.GET.get('filtro', 'hoy')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')

    if filtro == 'hoy':
        fecha_inicio = fecha_fin = hoy
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
        fecha_inicio = fecha_fin = hoy

    pedidos_periodo = Pedido.objects.filter(
        fecha_recepcion__date__gte=fecha_inicio,
        fecha_recepcion__date__lte=fecha_fin,
        estado_pago='pagado'
    )

    ingresos_totales = pedidos_periodo.aggregate(
        total=Sum('total')
    )['total'] or Decimal('0')

    gastos_insumos = MovimientoInsumo.objects.filter(
        fecha__date__gte=fecha_inicio,
        fecha__date__lte=fecha_fin,
        tipo='entrada'
    ).aggregate(total=Sum('costo_total'))['total'] or Decimal('0')

    gastos_operativos_total = GastoOperativo.objects.filter(
        fecha__gte=fecha_inicio,
        fecha__lte=fecha_fin
    ).aggregate(total=Sum('monto'))['total'] or Decimal('0')

    utilidad_neta = ingresos_totales - gastos_insumos - gastos_operativos_total

    # Métodos de pago
    def pago_total(tipo):
        return pedidos_periodo.filter(metodo_pago=tipo).aggregate(
            total=Sum('total'))['total'] or Decimal('0')

    pago_efectivo = pago_total('efectivo')
    pago_tarjeta = pago_total('tarjeta')
    pago_transferencia = pago_total('transferencia')

    total_pagos = pago_efectivo + pago_tarjeta + pago_transferencia
    pct = lambda x: round((x / total_pagos * 100), 1) if total_pagos > 0 else 0

    # PRENDAS
    detalles = DetallePedido.objects.filter(
        pedido__fecha_recepcion__date__gte=fecha_inicio,
        pedido__fecha_recepcion__date__lte=fecha_fin,
        pedido__estado_pago='pagado'
    )

    prendas_stats = detalles.values('prenda__nombre').annotate(
        cantidad=Sum('cantidad'),
        ganancia=Sum('subtotal')
    ).order_by('-cantidad')[:10]

    total_prendas = sum(p['cantidad'] for p in prendas_stats if p['cantidad'])
    prendas_data = [
        {
            'nombre': p['prenda__nombre'],
            'cantidad': p['cantidad'],
            'ganancia': float(p['ganancia'] or 0),
            'porcentaje': pct(p['cantidad'])
        }
        for p in prendas_stats if p['prenda__nombre']
    ]

    # SERVICIOS
    servicios_stats = pedidos_periodo.values('tipo_servicio').annotate(
        cantidad=Count('id'),
        ganancia=Sum('total')
    )

    total_serv = sum(s['cantidad'] for s in servicios_stats)
    servicios_data = [
        {
            'nombre': s['tipo_servicio'] or 'Sin especificar',
            'cantidad': s['cantidad'],
            'ganancia': float(s['ganancia'] or 0),
            'porcentaje': pct(s['cantidad'])
        }
        for s in servicios_stats
    ]

    # INSUMOS
    insumos_stats = MovimientoInsumo.objects.filter(
        fecha__date__gte=fecha_inicio,
        fecha__date__lte=fecha_fin,
        tipo='entrada'
    ).values('insumo__nombre').annotate(
        cantidad=Sum('cantidad'),
        gasto=Sum('costo_total')
    )

    insumos_data = [
        {
            'nombre': i['insumo__nombre'],
            'cantidad': float(i['cantidad'] or 0),
            'gasto': float(i['gasto'] or 0)
        }
        for i in insumos_stats if i['insumo__nombre']
    ]

    # GASTOS OPERATIVOS
    gastos_stats = GastoOperativo.objects.filter(
        fecha__gte=fecha_inicio,
        fecha__lte=fecha_fin
    ).values('categoria').annotate(
        total=Sum('monto'),
        cantidad=Count('id')
    )

    categorias = dict(GastoOperativo.CATEGORIA_CHOICES)
    gastos_data = [
        {
            'categoria': categorias.get(g['categoria'], g['categoria']),
            'total': float(g['total'] or 0),
            'cantidad': g['cantidad']
        }
        for g in gastos_stats
    ]

    context = {
        'ingresos_totales': ingresos_totales,
        'gastos_insumos': gastos_insumos,
        'gastos_operativos_total': gastos_operativos_total,
        'utilidad_neta': utilidad_neta,
        'prendas_json': json.dumps(prendas_data),
        'servicios_json': json.dumps(servicios_data),
        'insumos_json': json.dumps(insumos_data),
        'gastos_operativos_json': json.dumps(gastos_data),
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

    trabajadores = Usuario.objects.filter(rol__in=['operador', 'admin'])
    clientes = Usuario.objects.filter(rol='cliente')
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

            if rol == 'admin':
                grupo, created = Group.objects.get_or_create(name='Administrador')
                user.groups.add(grupo)
            elif rol == 'operador':
                grupo, created = Group.objects.get_or_create(name='Trabajador')
                user.groups.add(grupo)

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
        if usuario != request.user:
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


@login_required
@require_POST
def actualizar_precio_prenda(request):
    if not request.user.groups.filter(name='Administrador').exists():
        return JsonResponse({'success': False, 'mensaje': 'No autorizado'}, status=403)
    try:
        data = json.loads(request.body)
        prenda = get_object_or_404(Prenda, id=data.get('id'))
        prenda.precio = data.get('precio')
        prenda.save()
        return JsonResponse({'success': True, 'mensaje': 'Precio actualizado correctamente'})
    except Exception as e:
        return JsonResponse({'success': False, 'mensaje': str(e)}, status=400)


@login_required
@require_POST
def actualizar_precio_servicio(request):
    if not request.user.groups.filter(name='Administrador').exists():
        return JsonResponse({'success': False, 'mensaje': 'No autorizado'}, status=403)
    try:
        data = json.loads(request.body)
        servicio = get_object_or_404(Servicio, id=data.get('id'))
        servicio.precio = data.get('precio')
        servicio.save()
        return JsonResponse({'success': True, 'mensaje': 'Precio actualizado correctamente'})
    except Exception as e:
        return JsonResponse({'success': False, 'mensaje': str(e)}, status=400)


@login_required
@require_POST
def agregar_prenda(request):
    if not request.user.groups.filter(name='Administrador').exists():
        return JsonResponse({'success': False, 'mensaje': 'No autorizado'}, status=403)
    try:
        data = json.loads(request.body)
        nombre = data.get('nombre')
        if Prenda.objects.filter(nombre=nombre).exists():
            return JsonResponse({'success': False, 'mensaje': 'Ya existe una prenda con ese nombre'}, status=400)

        prenda = Prenda.objects.create(nombre=nombre, precio=data.get('precio'))
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
    if not request.user.groups.filter(name='Administrador').exists():
        return JsonResponse({'success': False, 'mensaje': 'No autorizado'}, status=403)
    try:
        data = json.loads(request.body)
        nombre = data.get('nombre')
        if Servicio.objects.filter(nombre=nombre).exists():
            return JsonResponse({'success': False, 'mensaje': 'Ya existe un servicio con ese nombre'}, status=400)

        servicio = Servicio.objects.create(
            nombre=nombre,
            precio=data.get('precio'),
            tipo=data.get('tipo', 'autoservicio'),
            descripcion=data.get('descripcion', '')
        )
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
    if not request.user.groups.filter(name='Administrador').exists():
        return JsonResponse({'success': False, 'mensaje': 'No autorizado'}, status=403)
    try:
        data = json.loads(request.body)
        prenda = get_object_or_404(Prenda, id=data.get('id'))
        prenda.activo = False
        prenda.save()
        return JsonResponse({'success': True, 'mensaje': 'Prenda eliminada correctamente'})
    except Exception as e:
        return JsonResponse({'success': False, 'mensaje': str(e)}, status=400)


@login_required
@require_POST
def eliminar_servicio(request):
    if not request.user.groups.filter(name='Administrador').exists():
        return JsonResponse({'success': False, 'mensaje': 'No autorizado'}, status=403)
    try:
        data = json.loads(request.body)
        servicio = get_object_or_404(Servicio, id=data.get('id'))
        servicio.activo = False
        servicio.save()
        return JsonResponse({'success': True, 'mensaje': 'Servicio eliminado correctamente'})
    except Exception as e:
        return JsonResponse({'success': False, 'mensaje': str(e)}, status=400)


def obtener_precios_json(request):
    prendas = list(Prenda.objects.filter(activo=True).values('id', 'nombre', 'precio'))
    servicios = list(Servicio.objects.filter(activo=True).values('id', 'nombre', 'tipo', 'precio', 'descripcion'))

    for prenda in prendas:
        prenda['precio'] = str(prenda['precio'])
    for servicio in servicios:
        servicio['precio'] = str(servicio['precio'])

    return JsonResponse({'prendas': prendas, 'servicios': servicios})


@login_required
def buscar_clientes(request):
    query = request.GET.get('q', '').strip()

    if len(query) < 2:
        return JsonResponse({'clientes': []})

    clientes = Usuario.objects.filter(
        rol='cliente'
    ).filter(
        Q(username__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(telefono__icontains=query)
    )[:10]

    clientes_data = [
        {
            'id': c.id,
            'username': c.username,
            'nombre_completo': f"{c.first_name} {c.last_name}".strip() or c.username,
            'telefono': c.telefono or 'Sin telefono'
        }
        for c in clientes
    ]

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


@login_required
def editar_insumo(request, id):
    insumo = get_object_or_404(Insumo, id=id)
    if request.method == 'POST':
        form = InsumoForm(request.POST, instance=insumo)
        if form.is_valid():
            form.save()
            NotificacionStock.objects.filter(
                insumo=insumo, atendida=False).update(atendida=True)
            messages.success(request, 'Inventario actualizado y alertas resueltas.')
            return redirect('admin_inventarios')
        else:
            errores = form.errors.as_text()
            messages.error(request, f'Error al guardar: {errores}')
    return redirect('admin_inventarios')


@login_required
def eliminar_insumo(request, id):
    insumo = get_object_or_404(Insumo, id=id)
    insumo.delete()
    messages.success(request, 'Producto eliminado.')
    return redirect('admin_inventarios')


@login_required
def admin_detalles_inventario(request):
    if not request.user.groups.filter(name='Administrador').exists():
        return redirect('tasks')
    insumos = Insumo.objects.all().order_by('nombre')
    return render(request, 'admin/inventario/detalles_inventario.html', {'insumos': insumos})


@login_required
def admin_historialVentas(request):
    if not request.user.groups.filter(name='Administrador').exists():
        return redirect('tasks')

    ventas = Pedido.objects.select_related('cliente', 'servicio').order_by('-fecha_recepcion')

    busqueda = request.GET.get('buscar', '').strip()
    if busqueda:
        ventas = ventas.filter(
            Q(folio__icontains=busqueda) |
            Q(cliente__username__icontains=busqueda) |
            Q(cliente__first_name__icontains=busqueda)
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

    movimientos = MovimientoOperador.objects.select_related(
        'operador', 'pedido'
    ).order_by('-fecha')

    operadores = Usuario.objects.filter(rol__in=['operador', 'admin']).order_by('username')

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
    """
    Vista ADMIN para gestionar incidencias y dudas/quejas.
    """
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

    dudas_quejas = DudaQueja.objects.select_related('cliente').all().order_by('-fecha_creacion')
    incidencias_list = Incidencia.objects.select_related('trabajador').all().order_by('-fecha_reporte')

    context = {
        'dudas_quejas': dudas_quejas,
        'incidencias': incidencias_list
    }
    return render(request, 'admin/incidencias.html', context)


@login_required
def admin_configuracion(request):
    if not request.user.groups.filter(name='Administrador').exists():
        return redirect('tasks')

    # Incidencias pendientes
    incidencias_pendientes = Incidencia.objects.exclude(estado='resuelto').count()

    # Productos con stock bajo
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


# ==========================================
#              VISTAS TRABAJADOR
# ==========================================

@login_required
def trabajador_dashboard(request):
    return render(request, 'trabajador/dashboard.html')


@login_required
def servicios_proceso(request):
    """
    Muestra SOLO los servicios activos que requieren atención.
    Excluye: Entregado y Cancelado.
    """
    pedidos = Pedido.objects.exclude(
        estado__in=['entregado', 'cancelado']
    ).select_related('cliente').order_by('fecha_recepcion')

    busqueda = request.GET.get('buscar', '').strip()
    if busqueda:
        pedidos = pedidos.filter(
            Q(folio__icontains=busqueda) |
            Q(cliente__username__icontains=busqueda) |
            Q(cliente__first_name__icontains=busqueda) |
            Q(cliente__last_name__icontains=busqueda)
        )

    return render(request, 'trabajador/procedimiento/servicios_proceso.html', {
        'pedidos': pedidos,
        'busqueda': busqueda
    })


@login_required
def historial_servicios(request):
    """
    Muestra SOLO el archivo muerto (servicios finalizados).
    Ordenados del más reciente entregado al más antiguo.
    """
    pedidos = Pedido.objects.filter(
        estado__in=['entregado', 'cancelado']
    ).select_related('cliente').order_by('-fecha_entrega_real', '-fecha_recepcion')

    busqueda = request.GET.get('buscar', '').strip()
    if busqueda:
        pedidos = pedidos.filter(
            Q(folio__icontains=busqueda) |
            Q(cliente__username__icontains=busqueda) |
            Q(cliente__first_name__icontains=busqueda)
        )

    return render(request, 'trabajador/procedimiento/historial_servicios.html', {
        'pedidos': pedidos
    })


@login_required
def nuevo_servicio(request):
    clientes = Usuario.objects.filter(rol='cliente').order_by('username')
    servicios = Servicio.objects.filter(activo=True)
    prendas = Prenda.objects.filter(activo=True)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            cliente_id = data.get('cliente_id')
            cliente = Usuario.objects.filter(id=cliente_id, rol='cliente').first()
            if not cliente:
                return JsonResponse({'success': False, 'message': 'Cliente no encontrado'}, status=400)

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
                fecha_entrega_estimada=data.get('fecha_entrega') if data.get('fecha_entrega') else None
            )

            MovimientoOperador.objects.create(
                operador=request.user,
                accion='registro_servicio',
                detalles=pedido.folio,
                pedido=pedido
            )

            pedido.refresh_from_db()
            mensaje_ticket = ""
            ticket_url = ""

            try:
                pdf_bytes = render_pdf_ticket(pedido)
                if pdf_bytes:
                    ticket_url = reverse('imprimir_ticket', args=[pedido.id])
                    enviado = enviar_ticket_email(pedido, pdf_bytes)
                    if enviado:
                        mensaje_ticket = " y ticket enviado por correo."
                    else:
                        mensaje_ticket = " (Ticket generado, pero no se pudo enviar correo)."
                else:
                    mensaje_ticket = " (Nota: Error al generar el PDF visual)."
            except Exception as e:
                print(f"Error en proceso de ticket: {e}")
                mensaje_ticket = " (Error técnico con el ticket PDF)."

            return JsonResponse({
                'success': True,
                'message': f'Servicio registrado correctamente{mensaje_ticket}',
                'folio': pedido.folio,
                'ticket_url': ticket_url
            })

        except Exception as e:
            return JsonResponse({'success': False, 'message': f"Error interno: {str(e)}"}, status=400)

    return render(request, 'trabajador/procedimiento/nuevo_servicio.html', {
        'clientes': clientes,
        'servicios': servicios,
        'prendas': prendas
    })


@login_required
def validar_ticket(request):
    """
    Vista principal para la pantalla de entrega y validación de tickets.
    """
    return render(request, 'trabajador/tickets/validar_ticket.html')


@login_required
def api_buscar_pedido(request):
    """
    API JSON para buscar un pedido por folio (usado en validar_ticket).
    """
    folio = request.GET.get('folio', '').strip().upper()
    try:
        pedido = Pedido.objects.get(folio__iexact=folio)
        data = {
            'success': True,
            'pedido': {
                'id': pedido.id,
                'folio': pedido.folio,
                'cliente': f"{pedido.cliente.first_name} {pedido.cliente.last_name}" if pedido.cliente.first_name else pedido.cliente.username,
                'servicio': pedido.tipo_servicio,
                'total': str(pedido.total),
                'estado': pedido.estado,
                'estado_display': pedido.get_estado_display(),
                'estado_pago': pedido.estado_pago,
                'peso': str(pedido.peso)
            }
        }
    except Pedido.DoesNotExist:
        data = {'success': False, 'message': 'No existe ningún pedido con ese folio.'}
    return JsonResponse(data)


@login_required
def api_entregar_pedido(request):
    """
    API JSON para cambiar el estado a entregado y registrar pago si aplica.
    """
    if request.method == 'POST':
        data = json.loads(request.body)
        pedido = get_object_or_404(Pedido, id=data.get('pedido_id'))

        if pedido.estado != 'listo':
            return JsonResponse({'success': False, 'message': 'El pedido no está listo para entrega.'})

        pedido.estado = 'entregado'
        pedido.fecha_entrega_real = timezone.now()

        if pedido.estado_pago == 'pendiente':
            pedido.estado_pago = 'pagado'
            pedido.metodo_pago = 'efectivo'

        pedido.save()

        MovimientoOperador.objects.create(
            operador=request.user,
            accion='entrego',
            detalles=f"Entregó pedido {pedido.folio}",
            pedido=pedido
        )
        return JsonResponse({'success': True})

    return JsonResponse({'success': False}, status=400)


@login_required
def incidencias(request):
    """
    Vista para que el trabajador reporte incidencias.
    """
    if request.method == 'POST':
        asunto = request.POST.get('asunto')
        descripcion = request.POST.get('descripcion')
        prioridad = request.POST.get('prioridad', 'media')
        evidencia = request.FILES.get('evidencia')

        if asunto and asunto.strip() and descripcion and descripcion.strip():
            Incidencia.objects.create(
                trabajador=request.user,
                asunto=asunto.strip(),
                descripcion=descripcion.strip(),
                prioridad=prioridad,
                evidencia=evidencia
            )
            return JsonResponse({'success': True, 'message': 'Incidencia reportada exitosamente.'})
        return JsonResponse({'success': False, 'message': 'Por favor complete todos los campos requeridos.'})

    mis_incidencias = Incidencia.objects.filter(trabajador=request.user).order_by('-fecha_reporte')
    return render(request, 'trabajador/incidencias/incidencias.html', {'mis_incidencias': mis_incidencias})


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
            messages.success(request, f'¡Aviso enviado al administrador sobre: {producto_nombre}!')
        return redirect('inventario')

    return render(request, 'trabajador/inventario/inventario.html', {'insumos': insumos})


@login_required
def detalle_servicio(request, pedido_id=None):
    pedido = get_object_or_404(Pedido, id=pedido_id) if pedido_id else None

    lavadoras_disp = Maquina.objects.filter(estado='disponible', tipo='lavadora')
    secadoras_disp = Maquina.objects.filter(estado='disponible', tipo='secadora')

    if request.method == 'POST' and pedido:
        try:
            data = json.loads(request.body)
            nuevo_estado = data.get('estado')
            estado_pago = data.get('estado_pago')
            notas = data.get('notas', '')
            maquina_id = data.get('maquina_id')
            tiempo_asignado = data.get('tiempo_asignado', 30)

            if nuevo_estado:
                pedido.estado = nuevo_estado
                if nuevo_estado == 'entregado':
                    pedido.fecha_entrega_real = timezone.now()

            if nuevo_estado == 'en_proceso' and maquina_id:
                try:
                    maquina = Maquina.objects.get(id=maquina_id)
                    if maquina.estado == 'disponible':
                        maquina.estado = 'ocupado'
                        maquina.pedido_actual = pedido
                        maquina.hora_inicio_uso = timezone.now()
                        maquina.tiempo_asignado = int(tiempo_asignado) if tiempo_asignado else 30
                        maquina.save()

                        msg_sistema = f"\n[Sistema {timezone.now().strftime('%H:%M')}] Iniciado en {maquina.nombre} ({maquina.tiempo_asignado} min)."
                        if pedido.observaciones:
                            pedido.observaciones += msg_sistema
                        else:
                            pedido.observaciones = msg_sistema
                except Maquina.DoesNotExist:
                    pass

            if estado_pago:
                pedido.estado_pago = estado_pago

            if notas:
                if pedido.observaciones:
                    pedido.observaciones += f"\n{notas}"
                else:
                    pedido.observaciones = notas

            pedido.save()

            MovimientoOperador.objects.create(
                operador=request.user,
                accion='actualizo',
                detalles=f"Actualizo pedido {pedido.folio} a estado: {nuevo_estado}",
                pedido=pedido
            )

            return JsonResponse({'success': True, 'message': 'Pedido actualizado correctamente'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)

    return render(request, 'trabajador/procedimiento/detalle_servicio.html', {
        'pedido': pedido,
        'lavadoras': lavadoras_disp,
        'secadoras': secadoras_disp
    })


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


@login_required
@require_POST
def asignar_maquina(request):
    """
    Asigna un pedido a una máquina, cambia su estado a ocupado e inicia el contador.
    """
    try:
        data = json.loads(request.body)
        pedido_id = data.get('pedido_id')
        maquina_id = data.get('maquina_id')
        tiempo = int(data.get('tiempo', 30))

        pedido = get_object_or_404(Pedido, id=pedido_id)
        maquina = get_object_or_404(Maquina, id=maquina_id)

        if maquina.estado != 'disponible':
            return JsonResponse({'success': False, 'message': 'La máquina no está disponible.'})

        maquina.estado = 'ocupado'
        maquina.pedido_actual = pedido
        maquina.hora_inicio_uso = timezone.now()
        maquina.tiempo_asignado = tiempo
        maquina.save()

        if maquina.tipo == 'lavadora':
            pedido.estado = 'en_proceso'

        pedido.save()

        return JsonResponse({'success': True, 'message': f'Máquina {maquina.nombre} asignada al folio {pedido.folio}'})

    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required
def imprimir_ticket(request, pedido_id):
    """
    Vista para descargar el ticket PDF directamente en el navegador.
    """
    pedido = get_object_or_404(Pedido, id=pedido_id)
    pdf_bytes = render_pdf_ticket(pedido)

    if not pdf_bytes:
        return HttpResponse("Error al generar el ticket", status=500)

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="ticket_{pedido.folio}.pdf"'
    return response


# ==========================================
#              VISTAS CLIENTE
# ==========================================

@login_required
def cliente_dashboard(request):
    pedidos_activos = Pedido.objects.filter(
        cliente=request.user
    ).exclude(
        estado__in=['entregado', 'cancelado']
    ).order_by('-fecha_recepcion')

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
    if request.method == 'POST':
        comentario = request.POST.get('comentario')
        if comentario and comentario.strip():
            DudaQueja.objects.create(cliente=request.user, comentario=comentario.strip())
            return JsonResponse({'success': True, 'message': 'Tu comentario ha sido enviado exitosamente.'})
        return JsonResponse({'success': False, 'message': 'El comentario no puede estar vacío.'})

    mis_dudas = DudaQueja.objects.filter(cliente=request.user).order_by('-fecha_creacion')
    return render(request, 'cliente/dudas_quejas.html', {'mis_dudas': mis_dudas})


@login_required
def autoservicio(request):
    servicios_autoservicio = Servicio.objects.filter(activo=True, tipo='autoservicio')

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            servicio_id = data.get('servicio_id')
            servicio_nombre = data.get('servicio_nombre')
            total = Decimal(str(data.get('total', 0)))
            metodo_pago = data.get('metodo_pago', 'efectivo')

            servicio = Servicio.objects.filter(id=servicio_id).first() if servicio_id else None

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

    return render(request, 'cliente/autoservicio.html', {'servicios': servicios_autoservicio})


@login_required
def seleccionar_servicio(request):
    return render(request, 'cliente/seleccionar_servicio.html')


@login_required
def servCosto(request):
    tipo_servicio = request.GET.get('tipo', 'por_encargo')
    tipos_nombres = {
        'autoservicio': 'Autoservicio',
        'por_encargo': 'Servicio por encargo',
        'a_domicilio': 'Servicio a domicilio',
        'tintoreria': 'Tintoreria',
    }
    tipo_servicio_nombre = tipos_nombres.get(tipo_servicio, 'Servicio')
    servicio = Servicio.objects.filter(activo=True, tipo=tipo_servicio).first()
    servicio_precio = servicio.precio if servicio else 0
    prendas = Prenda.objects.filter(activo=True)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            prendas_data = data.get('prendas', [])
            total = Decimal(str(data.get('total', 0)))
            metodo_pago = data.get('metodo_pago', 'efectivo')
            tipo = data.get('tipo_servicio', tipo_servicio)

            pedido = Pedido.objects.create(
                cliente=request.user,
                servicio=servicio,
                tipo_servicio=tipos_nombres.get(tipo, tipo_servicio_nombre),
                total=total,
                metodo_pago=metodo_pago,
                cantidad_prendas=sum([p.get('cantidad', 0) for p in prendas_data]),
                peso=sum([Decimal(str(p.get('peso', 0))) for p in prendas_data]),
                estado='pendiente',
                estado_pago='pendiente',
                origen='cliente'
            )

            for prenda_data in prendas_data:
                prenda_obj = Prenda.objects.filter(id=prenda_data.get('prenda_id')).first()
                if prenda_obj:
                    DetallePedido.objects.create(
                        pedido=pedido,
                        prenda=prenda_obj,
                        cantidad=prenda_data.get('cantidad', 1),
                        peso=Decimal(str(prenda_data.get('peso', 0))),
                        precio_unitario=Decimal(str(prenda_data.get('precio', 0))),
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