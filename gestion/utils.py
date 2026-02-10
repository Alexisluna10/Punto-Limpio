import qrcode
import os
from io import BytesIO
from django.core.mail import EmailMessage
from django.template.loader import get_template
from django.conf import settings
from xhtml2pdf import pisa
from decimal import Decimal
from django.urls import reverse

CONSUMO_POR_PRENDA = {
    'limpieza': Decimal('0.02'),
    'otros': Decimal('0.04'),
}


def descontar_insumos_por_pedido(pedido):
    from .models import Insumo, DetallePedido, MovimientoInsumo

    detalles = DetallePedido.objects.filter(
        pedido=pedido).select_related('prenda')

    peso_total = pedido.peso if pedido.peso else Decimal('0')
    
    if peso_total == 0:
        for detalle in detalles:
            peso_total += detalle.peso if detalle.peso else Decimal('0')
    
    if peso_total == 0:
        peso_total = Decimal('3.5')
    consumo_detergente = (peso_total / Decimal('3.5')) * Decimal('0.05')
    
    consumo_suavizante = peso_total * Decimal('0.02')

    consumo_por_categoria = {
        'detergente': consumo_detergente,
        'suavizante': consumo_suavizante,
    }
    for detalle in detalles:
        if detalle.prenda:
            categorias_requeridas = detalle.prenda.get_insumos_requeridos()
            cantidad_prendas = detalle.cantidad or 1

            for categoria in categorias_requeridas:
                if categoria not in ['detergente', 'suavizante']:
                    consumo_unitario = CONSUMO_POR_PRENDA.get(
                        categoria, Decimal('0.05'))
                    consumo_total = consumo_unitario * cantidad_prendas

                    if categoria in consumo_por_categoria:
                        consumo_por_categoria[categoria] += consumo_total
                    else:
                        consumo_por_categoria[categoria] = consumo_total

    descuentos_realizados = []
    for categoria, consumo in consumo_por_categoria.items():
        insumos = Insumo.objects.filter(
            categoria=categoria, stock_actual__gt=0).order_by('-stock_actual')

        consumo_restante = consumo

        for insumo in insumos:
            if consumo_restante <= 0:
                break

            a_descontar = min(insumo.stock_actual, consumo_restante)
            stock_anterior = insumo.stock_actual

            insumo.stock_actual -= a_descontar
            insumo.save()

            MovimientoInsumo.objects.create(
                insumo=insumo,
                pedido=pedido,
                tipo_movimiento='consumo_automatico',
                cantidad=a_descontar,
                stock_anterior=stock_anterior,
                stock_nuevo=insumo.stock_actual
            )

            descuentos_realizados.append({
                'insumo': insumo.nombre,
                'categoria': categoria,
                'cantidad_descontada': float(a_descontar),
                'stock_restante': float(insumo.stock_actual),
                'alerta': insumo.estado_alerta()
            })

            consumo_restante -= a_descontar

    return {
        'success': True,
        'message': f'Insumos descontados para pedido {pedido.folio}',
        'descuentos': descuentos_realizados
    }


def descontar_insumos_por_servicio_autoservicio(pedido):
    from .models import Insumo, MovimientoInsumo

    peso_autoservicio = Decimal('7.0')
    
    consumo_detergente = (peso_autoservicio / Decimal('3.5')) * Decimal('0.05')
    
    consumo_suavizante = peso_autoservicio * Decimal('0.02')

    CONSUMO_AUTOSERVICIO = {
        'detergente': consumo_detergente,
        'suavizante': consumo_suavizante,
    }

    descuentos_realizados = []

    for categoria, consumo in CONSUMO_AUTOSERVICIO.items():
        insumo = Insumo.objects.filter(
            categoria=categoria,
            stock_actual__gt=0
        ).order_by('-stock_actual').first()

        if insumo and insumo.stock_actual >= consumo:
            stock_anterior = insumo.stock_actual
            insumo.stock_actual -= consumo
            insumo.save()

            MovimientoInsumo.objects.create(
                insumo=insumo,
                pedido=pedido,
                tipo_movimiento='consumo_automatico',
                cantidad=consumo,
                stock_anterior=stock_anterior,
                stock_nuevo=insumo.stock_actual
            )

            descuentos_realizados.append({
                'insumo': insumo.nombre,
                'categoria': categoria,
                'cantidad_descontada': float(consumo),
                'stock_restante': float(insumo.stock_actual),
                'alerta': insumo.estado_alerta()
            })

    return {
        'success': True,
        'message': f'Insumos descontados para autoservicio {pedido.folio}',
        'descuentos': descuentos_realizados
    }

def render_pdf_ticket(request, pedido):
    """
    Genera el contenido en bytes del PDF del ticket.
    Retorna los bytes del PDF o None si hay error.
    Recibe 'request' para poder generar la URL absoluta del QR.
    """

    # 1. Generar URL Dinámica para el QR
    # Esto convierte 'rastreo_qr' en 'http://192.168.1.50:8000/rastreo/qr/5/' automáticamente
    try:
        relative_url = reverse('rastreo_qr', args=[pedido.id])
        url_rastreo = request.build_absolute_uri(relative_url)
    except Exception as e:
        # Fallback de seguridad por si algo falla con el request
        print(f"Advertencia QR: {e}")
        url_rastreo = f"http://localhost:8000/rastreo/qr/{pedido.id}/"

    # 2. Crear la imagen del QR
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url_rastreo)
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="black", back_color="white")

    # 3. Guardar QR temporalmente en disco (Requerido para xhtml2pdf)
    qr_filename = f'qr_{pedido.folio}.png'
    qr_path = os.path.join(settings.MEDIA_ROOT, qr_filename)

    # Asegurar que existe el directorio media
    os.makedirs(settings.MEDIA_ROOT, exist_ok=True)

    img_qr.save(qr_path)

    # 4. Renderizar Template HTML con los datos
    template_path = 'gestion/tickets/tickets_pdf.html'
    context = {
        'pedido': pedido,
        'qr_path': qr_path,  # Pasamos la ruta física del archivo
    }

    template = get_template(template_path)
    html = template.render(context)

    # 5. Generar PDF en memoria
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)

    # 6. Limpieza: borrar la imagen QR temporal del disco
    if os.path.exists(qr_path):
        try:
            os.remove(qr_path)
        except OSError:
            pass  # Si no se puede borrar por permisos, lo ignoramos por ahora

    if pdf.err:
        print(f"Error generando PDF para pedido {pedido.folio}")
        return None

    return result.getvalue()


def enviar_ticket_email(pedido, pdf_bytes):
    """
    Recibe el objeto pedido y los bytes del PDF ya generado, y lo envía por correo.
    """
    if not pedido.cliente.email or not pdf_bytes:
        return False

    try:
        email = EmailMessage(
            subject=f'Tu Ticket de Servicio - {pedido.folio}',
            body=f'Hola {pedido.cliente.first_name}, gracias por elegir Punto Limpio. Adjunto encontrarás tu ticket con los detalles de tu servicio.',
            from_email=settings.EMAIL_HOST_USER,
            to=[pedido.cliente.email],
        )
        # Adjuntar el PDF
        email.attach(f'ticket_{pedido.folio}.pdf',
                     pdf_bytes, 'application/pdf')
        email.send()
        return True
    except Exception as e:
        print(f"Error enviando correo al cliente {pedido.cliente.email}: {e}")
        return False
