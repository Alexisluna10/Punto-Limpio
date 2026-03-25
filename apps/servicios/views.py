from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Q
from decimal import Decimal
import json
import traceback
from django.urls import reverse
from django.views.decorators.cache import never_cache

# --- IMPORTACIONES DEL PROYECTO ---
from apps.core.decorators import solo_cliente, solo_trabajador, solo_admin
from apps.servicios.utils import enviar_ticket_email, descontar_insumos_por_pedido
from apps.usuarios.models import Usuario
from apps.servicios.models import Pedido, DetallePedido, Servicio, Prenda, Incidencia, DudaQueja, MovimientoOperador
from apps.inventario.models import Maquina
from .models import Servicio, Pedido, DetallePedido
from apps.inventario.models import Insumo
from .utils import render_pdf_ticket
import threading


@solo_trabajador
def trabajador_dashboard(request):
    return render(request, 'trabajador/dashboard.html')


@solo_cliente
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


@solo_trabajador
def nuevo_servicio(request):
    # ---------------------------------------------------------
    # 1. GET: Preparar datos para el formulario HTML
    # ---------------------------------------------------------
    clientes = Usuario.objects.filter(rol='cliente').order_by('username')

    # Cargamos el catálogo de prendas activas
    prendas_qs = Prenda.objects.filter(activo=True).order_by('nombre')
    prendas_list = list(prendas_qs.values('id', 'nombre', 'precio'))

    # Convertimos Decimal a float para JS
    for p in prendas_list:
        p['precio'] = float(p['precio'])

    precios_base = {
        'tintoreria': 80.00,
        'a_domicilio': 50.00,
        'por_encargo': 20.00
    }

    # Intentamos actualizar con los precios reales de la BD
    try:
        # CORRECCIÓN 1: Usamos 'tipo_limpieza' en lugar de 'tipo'
        servicios_db = Prenda.objects.filter(
            tipo_limpieza__in=['tintoreria',
                               'a_domicilio', 'por_encargo', 'planchado']
        )
        for s in servicios_db:
            # Usamos s.tipo_limpieza porque s.tipo no existe en el modelo
            if s.tipo_limpieza in precios_base:
                precios_base[s.tipo_limpieza] = float(s.precio)
    except Exception as e:
        print(f"Error cargando precios base: {e}")

    # ---------------------------------------------------------
    # 2. POST: Procesar el Guardado de la Orden
    # ---------------------------------------------------------
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            # --- A) Validar Cliente ---
            cliente_id = data.get('cliente_id')
            cliente = Usuario.objects.filter(
                id=cliente_id, rol='cliente').first()
            if not cliente:
                return JsonResponse({'success': False, 'message': 'Cliente no encontrado'}, status=400)

            # --- B) Mapeo de Tipos de Servicio ---
            tipos_nombres = {
                'por_encargo': 'Lavado por Encargo',
                'autoservicio': 'Autoservicio',
                'a_domicilio': 'Servicio a Domicilio',
                'tintoreria': 'Tintorería / Planchado'
            }
            tipo_raw = data.get('tipo_servicio', 'por_encargo')
            tipo_legible = tipos_nombres.get(
                tipo_raw, tipo_raw.replace('_', ' ').title())

            # --- C) Manejo de Fechas ---
            if tipo_raw == 'autoservicio':
                fecha_entrega = timezone.localdate()
            else:
                fecha_str = data.get('fecha_entrega')
                fecha_entrega = fecha_str if fecha_str else None

            # --- D) Helper para Decimales ---
            def to_decimal(val):
                if not val:
                    return Decimal('0')
                return Decimal(str(val))

            peso_normal = to_decimal(data.get('peso_normal'))
            peso_sucio = to_decimal(data.get('peso_sucio'))
            total_estimado = to_decimal(data.get('total'))

            if total_estimado <= 0:
                return JsonResponse({'success': False, 'message': 'El total no puede ser cero.'}, status=400)

            # --- E) CALCULAR Y CONGELAR EL PRECIO ---
            precio_base_kilo = Decimal('23.00')
            subtotal_peso_calculado = peso_normal * precio_base_kilo

            # Obtener el precio del servicio de la BD
            costo_servicio_db = Decimal('0.00')

            # CORRECCIÓN 2: Definir 'servicio_obj' antes de usarlo
            # Buscamos usando 'tipo_limpieza' que es el campo correcto
            servicio_obj = Prenda.objects.filter(
                tipo_limpieza=tipo_raw).first()

            if servicio_obj:
                costo_servicio_db = servicio_obj.precio
            else:
                # Fallback de seguridad
                if tipo_raw == 'tintoreria':
                    costo_servicio_db = Decimal('80.00')
                elif tipo_raw == 'a_domicilio':
                    costo_servicio_db = Decimal('50.00')
                elif tipo_raw == 'por_encargo':
                    costo_servicio_db = Decimal('20.00')

            # --- F) CREAR EL PEDIDO ---
            pedido = Pedido.objects.create(
                cliente=cliente,
                operador=request.user,
                tipo_servicio=tipo_legible,

                peso=peso_normal,
                subtotal_peso=subtotal_peso_calculado,
                costo_servicio=costo_servicio_db,

                fecha_entrega_estimada=fecha_entrega,
                observaciones=data.get('observaciones', ''),
                total=total_estimado,
                metodo_pago=data.get('metodo_pago', 'efectivo'),
                estado='pendiente',
                estado_pago='pendiente',
                origen='operador'
            )

            total_prendas_qty = 0

            # --- G) Procesar Ropa Muy Sucia ---
            if peso_sucio > 0:
                prenda_sucia, created = Prenda.objects.get_or_create(
                    nombre="Carga Ropa Muy Sucia (Kg)",
                    defaults={'precio': 30.00, 'tipo_limpieza': 'otros'}
                )
                if prenda_sucia.precio != 30.00:
                    prenda_sucia.precio = 30.00
                    prenda_sucia.save()

                DetallePedido.objects.create(
                    pedido=pedido,
                    prenda=prenda_sucia,
                    cantidad=1,
                    peso=peso_sucio,
                    precio_unitario=30.00,
                    subtotal=peso_sucio * 30
                )

            # --- H) Procesar Prendas Especiales ---
            items = data.get('items_especiales', [])
            for item in items:
                prenda_id = item.get('id')
                prenda_obj = Prenda.objects.filter(id=prenda_id).first()

                if prenda_obj:
                    qty = int(item.get('cantidad', 1))
                    if qty > 0:
                        peso_unitario = prenda_obj.peso_kg if prenda_obj.peso_kg else 0
                        peso_total = peso_unitario * qty

                        DetallePedido.objects.create(
                            pedido=pedido,
                            prenda=prenda_obj,
                            cantidad=qty,
                            peso=peso_total,
                            precio_unitario=to_decimal(item.get('precio')),
                            subtotal=to_decimal(item.get('subtotal'))
                        )
                        total_prendas_qty += qty

            pedido.cantidad_prendas = total_prendas_qty
            pedido.save()

            # --- I) Movimientos ---
            MovimientoOperador.objects.create(
                operador=request.user,
                accion='registro_servicio',
                detalles=f"Nuevo pedido: {pedido.folio}",
                pedido=pedido
            )

            try:
                descontar_insumos_por_pedido(pedido)
            except Exception as e:
                print(f"Advertencia Stock: {e}")

            # --- J) Ticket PDF ---
            ticket_url = ""
            try:
                pdf_bytes = render_pdf_ticket(request, pedido)
                if pdf_bytes:
                    ticket_url = reverse(
                        'servicios:imprimir_ticket', args=[pedido.id])
                    enviar_ticket_email(pedido, pdf_bytes)
            except Exception as e:
                print(f"Error Ticket: {e}")

            return JsonResponse({'success': True, 'folio': pedido.folio, 'ticket_url': ticket_url})

        except Exception as e:
            print("================ ERROR DETALLADO ================")
            traceback.print_exc()  # Ahora sí funcionará porque importamos traceback
            print(f"MENSAJE: {e}")
            print("=================================================")
            return JsonResponse({'success': False, 'message': str(e)}, status=400)

    # 3. Renderizar Template
    return render(request, 'trabajador/servicio/nuevo_servicio.html', {
        'clientes': clientes,
        'prendas_json': prendas_list,
        'precios_base': precios_base
    })


@solo_trabajador
def validar_ticket(request):
    return render(request, 'trabajador/tickets/validar_ticket.html')


@solo_trabajador
def api_buscar_por_folio(request):
    """
    API que busca un pedido por su folio y devuelve JSON con DETALLES.
    Reemplaza a tu antigua 'api_buscar_pedido'.
    """
    folio = request.GET.get('folio', '').strip().upper()

    if not folio:
        return JsonResponse({'success': False, 'message': 'Escribe un folio.'}, status=400)

    # Usamos filter().first() para evitar try/except y manejar el error manualmente
    pedido = Pedido.objects.filter(folio__iexact=folio).first()

    if not pedido:
        return JsonResponse({'success': False, 'message': 'Folio no encontrado.'}, status=404)

    # --- CAMBIO IMPORTANTE: PREPARAR LISTA DE PRENDAS ---
    # Tu función anterior no enviaba esto, y el modal lo necesita.
    detalles = []
    for d in pedido.detalles.all():
        nombre_prenda = d.prenda.nombre
        detalles.append(f"{d.cantidad}x {nombre_prenda}")

    data = {
        'success': True,
        'pedido': {
            'id': pedido.id,
            'folio': pedido.folio,
            'cliente': f"{pedido.cliente.first_name} {pedido.cliente.last_name}" if pedido.cliente.first_name else pedido.cliente.username,
            'total': float(pedido.total),

            # Enviamos el texto legible y el código interno para la lógica de colores en JS
            'estado': pedido.get_estado_display(),
            'estado_pago': pedido.get_estado_pago_display(),
            'estado_raw': pedido.estado,           # Vital para el JS
            'estado_pago_raw': pedido.estado_pago,  # Vital para el JS

            'items': detalles,  # Vital para mostrar qué se entrega
            'observaciones': pedido.observaciones
        }
    }
    return JsonResponse(data)


@solo_trabajador
def api_entregar_pedido(request):
    """API que marca un pedido como entregado con validaciones estrictas"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            pedido = get_object_or_404(Pedido, id=data.get('pedido_id'))

            # --- VALIDACIÓN 1: ¿Ya se entregó? ---
            if pedido.estado == 'entregado':
                return JsonResponse({'success': False, 'message': 'Este pedido YA fue entregado anteriormente.'})

            # --- VALIDACIÓN 2: ¿Está listo? (NUEVO) ---
            if pedido.estado != 'listo':
                return JsonResponse({
                    'success': False,
                    'message': f'⛔ NO SE PUEDE ENTREGAR. El pedido está en estatus: "{pedido.get_estado_display()}". Debe estar "Listo".'
                })

            # --- PROCESO DE ENTREGA ---
            pedido.estado = 'entregado'
            pedido.fecha_entrega_real = timezone.now()

            mensaje_exito = '¡Pedido entregado correctamente!'

            # --- VALIDACIÓN 3: Cobro Automático ---
            if pedido.estado_pago == 'pendiente':
                pedido.estado_pago = 'pagado'
                if not pedido.metodo_pago:
                    pedido.metodo_pago = 'efectivo'
                mensaje_exito = f'¡Cobro de ${pedido.total} registrado y pedido entregado!'

            pedido.save()

            # Registrar Movimiento
            MovimientoOperador.objects.create(
                operador=request.user,
                accion='entregado',
                detalles=f"Entregó pedido {pedido.folio} (Cobro realizado: {pedido.total})",
                pedido=pedido
            )

            return JsonResponse({'success': True, 'message': mensaje_exito})

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

    return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)


@solo_trabajador
def incidencias(request):
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

    mis_incidencias = Incidencia.objects.filter(
        trabajador=request.user).order_by('-fecha_reporte')
    return render(request, 'trabajador/incidencias/incidencias.html', {'mis_incidencias': mis_incidencias})


@solo_trabajador
def detalle_servicio(request, pedido_id):
    pedido = get_object_or_404(
        Pedido.objects.select_related('cliente'),
        id=pedido_id
    )

    # --- CÁLCULO DE KILOS TOTALES ---
    peso_sucio = 0
    for d in pedido.detalles.all():
        if d.peso:
            peso_sucio += d.peso

    pedido.kilos_totales = pedido.peso + peso_sucio
    # -------------------------------

    # Manejo del POST (Actualización)
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            # Actualizar Estado
            nuevo_estado = data.get('estado')
            if nuevo_estado:
                # VALIDACIÓN: No permitir 'entregado' desde aquí
                if nuevo_estado == 'entregado':
                    return JsonResponse({'success': False, 'message': 'Para entregar, usa la opción "Validar Ticket".'})
                pedido.estado = nuevo_estado

            # Actualizar Pago
            nuevo_pago = data.get('estado_pago')
            if nuevo_pago:
                pedido.estado_pago = nuevo_pago

            # Actualizar Método de Pago
            nuevo_metodo = data.get('metodo_pago')
            if nuevo_metodo:
                pedido.metodo_pago = nuevo_metodo

            # Actualizar Notas
            nuevas_notas = data.get('notas')
            if nuevas_notas:
                if pedido.observaciones:
                    pedido.observaciones += f"\n[Act]: {nuevas_notas}"
                else:
                    pedido.observaciones = nuevas_notas

            # Asignación de Máquina (Lógica existente)
            maquina_id = data.get('maquina_id')
            tiempo = data.get('tiempo_asignado')

            if maquina_id:
                maquina = Maquina.objects.filter(id=maquina_id).first()
                if maquina and maquina.estado == 'disponible':
                    maquina.estado = 'ocupado'
                    maquina.pedido_actual = pedido
                    maquina.hora_inicio_uso = timezone.now()
                    maquina.tiempo_asignado = int(tiempo) if tiempo else 30
                    maquina.save()

                    pedido.estado = 'en_proceso'

            pedido.save()

            # Registrar Movimiento
            MovimientoOperador.objects.create(
                operador=request.user,
                accion='actualizo_estado',
                detalles=f"Actualizó servicio {pedido.folio} a {pedido.estado}",
                pedido=pedido
            )

            return JsonResponse({'success': True, 'message': 'Servicio actualizado correctamente.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)

    # GET: Mostrar HTML
    lavadoras = Maquina.objects.filter(tipo='lavadora', estado='disponible')
    secadoras = Maquina.objects.filter(tipo='secadora', estado='disponible')

    return render(request, 'trabajador/procedimiento/detalle_servicio.html', {
        'pedido': pedido,
        'lavadoras': lavadoras,
        'secadoras': secadoras
    })


@solo_trabajador
def imprimir_ticket(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    # CAMBIO CLAVE: Pasamos 'request' para generar el QR dinámico
    pdf_bytes = render_pdf_ticket(request, pedido)

    if not pdf_bytes:
        return HttpResponse("Error al generar el ticket", status=500)

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="ticket_{pedido.folio}.pdf"'
    return response


@solo_cliente
def solicitar_servicio(request):
    servicios = Servicio.objects.filter(activo=True)
    return render(request, 'cliente/solicitar_servicio.html', {'servicios': servicios})


@solo_cliente
def rastrear_servicio(request):
    return render(request, 'cliente/rastrear_servicio.html')


@solo_cliente
def dudas_quejas(request):
    if request.method == 'POST':
        comentario = request.POST.get('comentario')
        if comentario and comentario.strip():
            DudaQueja.objects.create(
                cliente=request.user, comentario=comentario.strip())
            return JsonResponse({'success': True, 'message': 'Tu comentario ha sido enviado exitosamente.'})
        return JsonResponse({'success': False, 'message': 'El comentario no puede estar vacío.'})

    mis_dudas = DudaQueja.objects.filter(
        cliente=request.user).order_by('-fecha_creacion')
    return render(request, 'cliente/dudas_quejas.html', {'mis_dudas': mis_dudas})


@solo_cliente
def autoservicio(request):
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

            # ✅ Enviar ticket en segundo plano (sin bloquear la respuesta)
            hilo = threading.Thread(
                target=enviar_ticket_en_background, args=(request, pedido))
            hilo.daemon = True
            hilo.start()

            return JsonResponse({
                'success': True,
                'message': 'Servicio registrado exitosamente',
                'folio': pedido.folio
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)

    return render(request, 'cliente/autoservicio.html', {'servicios': servicios_autoservicio})


@solo_cliente
def seleccionar_servicio(request):
    return render(request, 'cliente/seleccionar_servicio.html')


@solo_cliente
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
                cantidad_prendas=sum([p.get('cantidad', 0)
                                     for p in prendas_data]),
                peso=sum([Decimal(str(p.get('peso', 0)))
                         for p in prendas_data]),
                estado='pendiente',
                estado_pago='pendiente',
                origen='cliente'
            )

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

            # Descontar insumos automaticamente del inventario
            resultado_descuento = descontar_insumos_por_pedido(pedido)

            # ✅ Enviar ticket en segundo plano (sin bloquear la respuesta)
            hilo = threading.Thread(
                target=enviar_ticket_en_background, args=(request, pedido))
            hilo.daemon = True
            hilo.start()

            return JsonResponse({
                'success': True,
                'message': 'Servicio registrado exitosamente',
                'folio': pedido.folio,
                'insumos_descontados': resultado_descuento.get('descuentos', [])
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)

    return render(request, 'cliente/servCosto.html', {
        'prendas': prendas,
        'tipo_servicio': tipo_servicio,
        'tipo_servicio_nombre': tipo_servicio_nombre,
        'servicio_precio': servicio_precio,
    })


@solo_cliente
def enviar_ticket_en_background(request, pedido):
    try:
        pdf_bytes = render_pdf_ticket(request, pedido)
        if pdf_bytes:
            enviar_ticket_email(pedido, pdf_bytes)
    except Exception as e:
        print(
            f"⚠️ Error enviando ticket al cliente {pedido.cliente.email}: {e}")


@solo_cliente
def terminado(request):
    return render(request, 'cliente/terminado.html')


@never_cache
def rastreo_qr(request, pedido_id):
    """
    Vista pública para ver el estado del pedido al escanear el QR.
    No requiere login para facilitar el acceso rápido al cliente.
    """
    from django.shortcuts import get_object_or_404

    # Buscamos el pedido
    pedido = get_object_or_404(Pedido, id=pedido_id)

    context = {
        'pedido': pedido,
    }
    # Asegúrate de tener esta plantilla creada en gestion/templates/cliente/rastrear_servicio.html
    return render(request, 'cliente/rastrear_servicio.html', context)


@never_cache
def buscar_pedido_rastreo(request):
    """
    Vista LÓGICA para procesar la búsqueda manual por FOLIO (Texto).
    Recibe el folio del formulario, busca el ID y redirige a la vista principal.
    """
    if request.method == 'GET':
        folio_query = request.GET.get('folio', '').strip()

        if folio_query:
            # Intentar encontrar el pedido por el Folio (ignorando mayúsculas/minúsculas)
            pedido = Pedido.objects.filter(folio__iexact=folio_query).first()

            if pedido:
                # Si existe, redirigimos a la vista oficial usando su ID
                return redirect('servicios:rastreo_qr', pedido_id=pedido.id)
            else:
                # Si no existe, volvemos a la página con un mensaje de error
                messages.error(
                    request, f'No se encontró ningún servicio con el folio "{folio_query}".')

    # Si entra aquí sin buscar o si falló, renderiza la página "vacía" (buscador)
    return render(request, 'cliente/rastrear_servicio.html')


@solo_admin
def admin_incidencias(request):
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

    dudas_quejas = DudaQueja.objects.select_related(
        'cliente').all().order_by('-fecha_creacion')
    incidencias_list = Incidencia.objects.select_related(
        'trabajador').all().order_by('-fecha_reporte')

    context = {
        'dudas_quejas': dudas_quejas,
        'incidencias': incidencias_list
    }
    return render(request, 'admin/incidencias.html', context)


@solo_admin
def admin_precios(request):
    prendas = Prenda.objects.filter(activo=True).order_by('nombre')
    servicios = Servicio.objects.filter(activo=True).order_by('tipo', 'nombre')
    return render(request, 'admin/precios.html', {
        'prendas': prendas,
        'servicios': servicios
    })


@solo_admin
@require_POST
def actualizar_precio_prenda(request):
    try:
        data = json.loads(request.body)
        prenda = get_object_or_404(Prenda, id=data.get('id'))
        prenda.precio = data.get('precio')
        prenda.save()
        return JsonResponse({'success': True, 'mensaje': 'Precio actualizado correctamente'})
    except Exception as e:
        return JsonResponse({'success': False, 'mensaje': str(e)}, status=400)


@solo_admin
@require_POST
def actualizar_precio_servicio(request):
    try:
        data = json.loads(request.body)
        servicio = get_object_or_404(Servicio, id=data.get('id'))
        servicio.precio = data.get('precio')
        servicio.save()
        return JsonResponse({'success': True, 'mensaje': 'Precio actualizado correctamente'})
    except Exception as e:
        return JsonResponse({'success': False, 'mensaje': str(e)}, status=400)


@solo_admin
@require_POST
def agregar_prenda(request):
    try:
        data = json.loads(request.body)
        nombre = data.get('nombre')
        if Prenda.objects.filter(nombre=nombre).exists():
            return JsonResponse({'success': False, 'mensaje': 'Ya existe una prenda con ese nombre'}, status=400)

        prenda = Prenda.objects.create(
            nombre=nombre, precio=data.get('precio'))
        return JsonResponse({
            'success': True,
            'mensaje': 'Prenda agregada correctamente',
            'prenda': {'id': prenda.id, 'nombre': prenda.nombre, 'precio': str(prenda.precio)}
        })
    except Exception as e:
        return JsonResponse({'success': False, 'mensaje': str(e)}, status=400)


@solo_admin
@require_POST
def agregar_servicio(request):
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


@solo_admin
@require_POST
def eliminar_prenda(request):
    try:
        data = json.loads(request.body)
        prenda = get_object_or_404(Prenda, id=data.get('id'))
        prenda.activo = False
        prenda.save()
        return JsonResponse({'success': True, 'mensaje': 'Prenda eliminada correctamente'})
    except Exception as e:
        return JsonResponse({'success': False, 'mensaje': str(e)}, status=400)


@solo_admin
@require_POST
def eliminar_servicio(request):
    try:
        data = json.loads(request.body)
        servicio = get_object_or_404(Servicio, id=data.get('id'))
        servicio.activo = False
        servicio.save()
        return JsonResponse({'success': True, 'mensaje': 'Servicio eliminado correctamente'})
    except Exception as e:
        return JsonResponse({'success': False, 'mensaje': str(e)}, status=400)


@solo_admin
def obtener_precios_json(request):
    prendas = list(Prenda.objects.filter(
        activo=True).values('id', 'nombre', 'precio'))
    servicios = list(Servicio.objects.filter(activo=True).values(
        'id', 'nombre', 'tipo', 'precio', 'descripcion'))

    for prenda in prendas:
        prenda['precio'] = str(prenda['precio'])
    for servicio in servicios:
        servicio['precio'] = str(servicio['precio'])

    return JsonResponse({'prendas': prendas, 'servicios': servicios})


@solo_trabajador
def historial_servicios(request):
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


@solo_trabajador
def servicios_proceso(request):
    # Obtenemos los pedidos activos
    pedidos = Pedido.objects.exclude(
        estado__in=['entregado', 'cancelado']
    ).select_related('cliente').prefetch_related('detalles').order_by('fecha_recepcion')

    busqueda = request.GET.get('buscar', '').strip()
    if busqueda:
        pedidos = pedidos.filter(
            Q(folio__icontains=busqueda) |
            Q(cliente__username__icontains=busqueda) |
            Q(cliente__first_name__icontains=busqueda)
        )

    # --- CÁLCULO DE KILOS TOTALES ---
    # Iteramos para sumar: Peso Normal (pedido.peso) + Peso Sucio (en detalles)
    for p in pedidos:
        peso_sucio = 0
        # Buscamos en los detalles si hay alguno que tenga peso registrado (la ropa sucia lo tiene)
        for d in p.detalles.all():
            if d.peso:
                peso_sucio += d.peso

        # Creamos un atributo temporal 'kilos_totales' para usar en el HTML
        p.kilos_totales = p.peso + peso_sucio

    return render(request, 'trabajador/procedimiento/servicios_proceso.html', {
        'pedidos': pedidos,
        'busqueda': busqueda
    })
