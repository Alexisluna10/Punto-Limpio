from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
import json

# --- IMPORTACIONES DEL PROYECTO ---
from apps.core.decorators import solo_admin, solo_trabajador
from apps.inventario.models import Insumo, NotificacionStock, MovimientoInsumo, Maquina
from apps.inventario.forms import InsumoForm
from apps.servicios.models import Pedido

@solo_admin
def admin_inventarios(request):
    from .models import MovimientoInsumo

    insumos = Insumo.objects.all().order_by('-fecha_actualizacion')
    notificaciones = NotificacionStock.objects.filter(
        atendida=False).select_related('insumo', 'usuario')

    # Obtener los ultimos movimientos automaticos de insumos (ultimos 10)
    ultimos_movimientos = MovimientoInsumo.objects.filter(
        tipo_movimiento='consumo_automatico'
    ).select_related('insumo', 'pedido').order_by('-fecha')[:10]

    if request.method == 'POST':
        form = InsumoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto agregado correctamente.')
            return redirect('inventario:admin_inventarios')
    else:
        form = InsumoForm()

    return render(request, 'admin/inventario/inventarios.html', {
        'insumos': insumos,
        'form': form,
        'notificaciones': notificaciones,
        'ultimos_movimientos': ultimos_movimientos
    })

@solo_admin
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
            return redirect('inventario:admin_inventarios')
        else:
            errores = form.errors.as_text()
            messages.error(request, f'Error al guardar: {errores}')
    return redirect('inventario:admin_inventarios')

@solo_admin
def eliminar_insumo(request, id):
    insumo = get_object_or_404(Insumo, id=id)
    insumo.delete()
    messages.success(request, 'Producto eliminado.')
    return redirect('inventario:admin_inventarios')

@solo_admin
def admin_detalles_inventario(request):
    insumos = Insumo.objects.all().order_by('nombre')
    return render(request, 'admin/inventario/detalles_inventario.html', {'insumos': insumos})

@solo_trabajador
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
        return redirect('inventario:inventario')

    return render(request, 'trabajador/inventario/inventario.html', {'insumos': insumos})

@solo_trabajador
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

        return redirect('inventario:estatus_maquina')

    lavadoras = Maquina.objects.filter(tipo='lavadora').order_by('nombre')
    secadoras = Maquina.objects.filter(tipo='secadora').order_by('nombre')

    return render(request, 'trabajador/estatus/estatus_maquina.html', {
        'lavadoras': lavadoras,
        'secadoras': secadoras
    })
    
@solo_trabajador
@require_POST
def asignar_maquina(request):
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