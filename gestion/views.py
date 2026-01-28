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
    return render(request, 'admin/finanzas/finanzas.html')


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
    ventas = Pedido.objects.select_related('cliente', 'servicio').order_by('-fecha_recepcion')
    
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
    return render(request, 'admin/configuracion.html')


@login_required
def trabajador_dashboard(request):
    return render(request, 'trabajador/dashboard.html')


@login_required
def nuevo_servicio(request):
    # Obtener solo clientes para el dropdown
    clientes = Usuario.objects.filter(rol='cliente').order_by('username')
    servicios = Servicio.objects.filter(activo=True)
    prendas = Prenda.objects.filter(activo=True)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            cliente_id = data.get('cliente_id')
            tipo_servicio = data.get('tipo_servicio', 'por_encargo')
            lavado_especial = data.get('lavado_especial', False)
            cobija_tipo = data.get('cobija_tipo', '')
            peso = Decimal(str(data.get('peso', 0)))
            cantidad_prendas = data.get('cantidad_prendas', 0)
            observaciones = data.get('observaciones', '')
            fecha_entrega = data.get('fecha_entrega')
            metodo_pago = data.get('metodo_pago', 'efectivo')
            total = Decimal(str(data.get('total', 0)))
            
            # Validar que el cliente existe y es cliente
            cliente = Usuario.objects.filter(id=cliente_id, rol='cliente').first()
            if not cliente:
                return JsonResponse({'success': False, 'message': 'Cliente no encontrado'}, status=400)
            
            # Mapear tipo a nombre legible
            tipos_nombres = {
                'normal': 'Lavado por Encargo',
                'por_encargo': 'Lavado por Encargo',
                'autoservicio': 'Autoservicio',
                'planchado': 'Solo Planchado',
                'tintoreria': 'Tintoreria',
                'a_domicilio': 'Servicio a domicilio',
            }
            
            # Crear el pedido
            pedido = Pedido.objects.create(
                cliente=cliente,
                operador=request.user,
                tipo_servicio=tipos_nombres.get(tipo_servicio, tipo_servicio),
                peso=peso,
                cantidad_prendas=cantidad_prendas,
                observaciones=observaciones,
                cobija_tipo=cobija_tipo,
                lavado_especial=lavado_especial,
                total=total,
                metodo_pago=metodo_pago,
                estado='pendiente',
                estado_pago='pendiente',
                origen='operador',
                fecha_entrega_estimada=fecha_entrega if fecha_entrega else None
            )
            
            # Registrar movimiento del operador
            MovimientoOperador.objects.create(
                operador=request.user,
                accion='registro_servicio',
                detalles=pedido.folio,
                pedido=pedido
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Servicio registrado exitosamente',
                'folio': pedido.folio
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    
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
    
    if request.method == 'POST' and pedido:
        try:
            data = json.loads(request.body)
            nuevo_estado = data.get('estado')
            estado_pago = data.get('estado_pago')
            notas = data.get('notas', '')
            
            # Actualizar estado del pedido
            if nuevo_estado:
                pedido.estado = nuevo_estado
                if nuevo_estado == 'entregado':
                    pedido.fecha_entrega_real = timezone.now()
            
            # Actualizar estado de pago
            if estado_pago:
                pedido.estado_pago = estado_pago
            
            # Agregar observaciones si hay
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
                detalles=f"Actualizo pedido {pedido.folio} - Estado: {nuevo_estado or 'sin cambio'}, Pago: {estado_pago or 'sin cambio'}",
                pedido=pedido
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Pedido actualizado exitosamente'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    
    return render(request, 'trabajador/procedimiento/detalle_servicio.html', {
        'pedido': pedido
    })


@login_required
def estatus_maquina(request):
    return render(request, 'trabajador/estatus/estatus_maquina.html')


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
            
            servicio = Servicio.objects.filter(id=servicio_id).first() if servicio_id else None
            
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
                cantidad_prendas=sum([p.get('cantidad', 0) for p in prendas_data]),
                peso=sum([Decimal(str(p.get('peso', 0))) for p in prendas_data]),
                estado='pendiente',
                estado_pago='pendiente',
                origen='cliente'
            )
            
            # Crear detalles de prendas
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
    
    mis_incidencias = Incidencia.objects.filter(trabajador=request.user).order_by('-fecha_reporte')
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
