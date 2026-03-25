import qrcode
import os
import smtplib
import socket
from io import BytesIO
from django.core.mail import EmailMessage
from django.template.loader import get_template
from django.conf import settings
from xhtml2pdf import pisa
from decimal import Decimal
from django.urls import reverse


# Consumo de detergente por kg de ropa (en litros)
DETERGENTE_POR_KG = Decimal('0.015')  # 15ml por kg

# Consumo de suavizante por kg de ropa (en litros)
SUAVIZANTE_POR_KG = Decimal('0.010')  # 10ml por kg

# Consumo por prenda especial (limpieza, otros)
CONSUMO_POR_PRENDA = {
    'limpieza': Decimal('0.02'),
    'otros': Decimal('0.04'),
}

# Peso mínimo por defecto si no se registró peso (en kg)
PESO_MINIMO_DEFECTO = Decimal('3.5')

# Factor multiplicador para ropa muy sucia
FACTOR_ROPA_SUCIA = Decimal('1.3')  # 30% más de insumos


def descontar_insumos_por_pedido(pedido):
    from .models import DetallePedido
    from apps.inventario.models import Insumo, MovimientoInsumo

    # ============================================
    # 1. OBTENER EL PESO TOTAL DEL PEDIDO
    # ============================================
    peso_total = pedido.peso if pedido.peso else Decimal('0')

    # Si no hay peso en el pedido principal, intentar sumarlo de los detalles
    if peso_total == 0:
        detalles = DetallePedido.objects.filter(pedido=pedido)
        for detalle in detalles:
            if detalle.peso:
                peso_total += detalle.peso

    # Si aún no hay peso, usar peso mínimo por defecto
    # IMPORTANTE: Esto debería evitarse, siempre se debe pesar la ropa
    if peso_total == 0:
        peso_total = PESO_MINIMO_DEFECTO
        print(
            f"⚠️  ADVERTENCIA: Pedido {pedido.folio} sin peso registrado. Usando peso por defecto: {peso_total} kg")

    # ============================================
    # 2. CALCULAR CONSUMO DE INSUMOS
    # ============================================

    # Consumo base de detergente y suavizante
    consumo_detergente = peso_total * DETERGENTE_POR_KG
    consumo_suavizante = peso_total * SUAVIZANTE_POR_KG

    # Si es ropa muy sucia, aumentar el consumo
    tipo_servicio_lower = pedido.tipo_servicio.lower()
    if 'sucia' in tipo_servicio_lower or 'trabajo' in tipo_servicio_lower:
        consumo_detergente *= FACTOR_ROPA_SUCIA
        consumo_suavizante *= FACTOR_ROPA_SUCIA
        print(
            f"📌 Pedido {pedido.folio}: Ropa muy sucia detectada. Consumo aumentado en {(FACTOR_ROPA_SUCIA - 1) * 100}%")

    consumo_por_categoria = {
        'detergente': consumo_detergente,
        'suavizante': consumo_suavizante,
    }

    # ============================================
    # 3. AGREGAR INSUMOS ESPECIALES (PRENDAS)
    # ============================================
    detalles = DetallePedido.objects.filter(
        pedido=pedido).select_related('prenda')

    for detalle in detalles:
        if detalle.prenda:
            categoria = detalle.prenda.tipo_limpieza
            cantidad_prendas = detalle.cantidad or 1

            # Solo procesar categorías que NO sean detergente/suavizante
            # (esas ya se calcularon por peso)
            if categoria not in ['detergente', 'suavizante']:
                consumo_unitario = CONSUMO_POR_PRENDA.get(
                    categoria, Decimal('0.05'))
                consumo_total = consumo_unitario * cantidad_prendas

                if categoria in consumo_por_categoria:
                    consumo_por_categoria[categoria] += consumo_total
                else:
                    consumo_por_categoria[categoria] = consumo_total
    # ============================================
    # 4. DESCONTAR INSUMOS DEL INVENTARIO
    # ============================================
    descuentos_realizados = []

    for categoria, consumo in consumo_por_categoria.items():
        if consumo <= 0:
            continue

        # Obtener insumos disponibles de esta categoría (ordenados por stock)
        insumos = Insumo.objects.filter(
            categoria=categoria,
            stock_actual__gt=0
        ).order_by('-stock_actual')

        consumo_restante = consumo

        for insumo in insumos:
            if consumo_restante <= 0:
                break

            # Descontar lo que se pueda de este insumo
            a_descontar = min(insumo.stock_actual, consumo_restante)
            stock_anterior = insumo.stock_actual

            insumo.stock_actual -= a_descontar
            insumo.save()

            # Registrar el movimiento
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

        # Advertencia si no hubo suficiente stock
        if consumo_restante > 0:
            print(
                f"⚠️  ADVERTENCIA: Faltó stock de {categoria}. Quedaron {consumo_restante} litros sin descontar.")

    # Log de resumen
    print(f"✅ Pedido {pedido.folio}: Peso {peso_total} kg | Detergente: {consumo_detergente} L | Suavizante: {consumo_suavizante} L")

    return {
        'success': True,
        'message': f'Insumos descontados para pedido {pedido.folio} ({peso_total} kg)',
        'peso_total': float(peso_total),
        'descuentos': descuentos_realizados
    }


def descontar_insumos_por_servicio_autoservicio(pedido):
    """
    Descuenta insumos para servicios de autoservicio.

    Si el pedido tiene peso registrado, lo usa.
    Si no, asume una carga típica de lavadora (7 kg).

    Args:
        pedido: Objeto Pedido

    Returns:
        dict: Información sobre los descuentos realizados
    """
    from apps.inventario.models import Insumo, MovimientoInsumo

    # ============================================
    # 1. OBTENER PESO (real o estimado)
    # ============================================
    peso_autoservicio = pedido.peso if pedido.peso and pedido.peso > 0 else Decimal(
        '7.0')

    if pedido.peso and pedido.peso > 0:
        print(
            f"📌 Autoservicio {pedido.folio}: Usando peso real de {peso_autoservicio} kg")
    else:
        print(
            f"📌 Autoservicio {pedido.folio}: Sin peso registrado. Usando peso típico de {peso_autoservicio} kg")

    # ============================================
    # 2. CALCULAR CONSUMO
    # ============================================
    consumo_detergente = peso_autoservicio * DETERGENTE_POR_KG
    consumo_suavizante = peso_autoservicio * SUAVIZANTE_POR_KG

    CONSUMO_AUTOSERVICIO = {
        'detergente': consumo_detergente,
        'suavizante': consumo_suavizante,
    }

    # ============================================
    # 3. DESCONTAR DEL INVENTARIO
    # ============================================
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
        elif insumo:
            # Hay insumo pero no alcanza
            print(
                f"⚠️  ADVERTENCIA: Stock insuficiente de {categoria}. Se necesitan {consumo}L pero solo hay {insumo.stock_actual}L")
        else:
            # No hay insumo de esta categoría
            print(f"❌ ERROR: No hay insumos de tipo {categoria} disponibles")

    print(
        f"✅ Autoservicio {pedido.folio}: Peso {peso_autoservicio} kg | Detergente: {consumo_detergente} L | Suavizante: {consumo_suavizante} L")

    return {
        'success': True,
        'message': f'Insumos descontados para autoservicio {pedido.folio} ({peso_autoservicio} kg)',
        'peso_total': float(peso_autoservicio),
        'descuentos': descuentos_realizados
    }


def render_pdf_ticket(request, pedido):
    """
    Genera el contenido en bytes del PDF del ticket.
    Retorna los bytes del PDF o None si hay error.
    """
    # ---------------------------------------------------------
    # 1. Generar URL Dinámica para el QR (Con Namespace Correcto)
    # ---------------------------------------------------------
    try:
        # CORRECCIÓN: Agregamos el namespace 'servicios:'
        relative_url = reverse('servicios:rastreo_qr', args=[pedido.id])
        url_rastreo = request.build_absolute_uri(relative_url)
    except Exception as e:
        # Fallback por si falla el request o la url no existe aún
        print(f"Advertencia QR: {e}")
        url_rastreo = f"http://127.0.0.1:8000/servicios/rastreo/qr/{pedido.id}/"

    # ---------------------------------------------------------
    # 2. Crear la imagen del QR
    # ---------------------------------------------------------
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url_rastreo)
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="black", back_color="white")

    # ---------------------------------------------------------
    # 3. Guardar QR temporalmente (Necesario para que el PDF lo lea)
    # ---------------------------------------------------------
    qr_filename = f'qr_{pedido.folio}.png'
    # Guardamos en MEDIA_ROOT para tener una ruta física
    qr_path = os.path.join(settings.MEDIA_ROOT, qr_filename)

    # Aseguramos que la carpeta exista
    os.makedirs(settings.MEDIA_ROOT, exist_ok=True)

    try:
        img_qr.save(qr_path)
    except Exception as e:
        print(f"Error guardando imagen QR: {e}")
        return None

    # ---------------------------------------------------------
    # 4. Renderizar Template HTML con los datos
    # ---------------------------------------------------------
    # CORRECCIÓN: Verifica que esta sea la ruta real donde pusiste tu HTML
    # Si lo moviste a la carpeta de templates de servicios, ajusta aquí:
    template_path = 'trabajador/tickets/tickets_pdf.html'

    context = {
        'pedido': pedido,
        'qr_path': qr_path,  # Pasamos la ruta física absoluta
        # Puedes pasar más datos si tu template los necesita
        'MEDIA_ROOT': settings.MEDIA_ROOT,
    }

    try:
        template = get_template(template_path)
        html = template.render(context)
    except Exception as e:
        print(f"Error cargando template '{template_path}': {e}")
        return None

    # ---------------------------------------------------------
    # 5. Generar PDF en memoria (BytesIO)
    # ---------------------------------------------------------
    result = BytesIO()

    # xhtml2pdf necesita saber dónde buscar imágenes estáticas
    def link_callback(uri, rel):
        """
        Convierte URLs de HTML a rutas absolutas del sistema de archivos
        """
        if uri.startswith(settings.MEDIA_URL):
            path = os.path.join(settings.MEDIA_ROOT,
                                uri.replace(settings.MEDIA_URL, ""))
        elif uri.startswith(settings.STATIC_URL):
            path = os.path.join(settings.STATIC_ROOT,
                                uri.replace(settings.STATIC_URL, ""))
        else:
            return uri
        return path

    pdf_status = pisa.pisaDocument(
        BytesIO(html.encode("UTF-8")),
        result,
        link_callback=link_callback  # Ayuda a encontrar logos/estilos
    )

    # ---------------------------------------------------------
    # 6. Limpieza: borrar la imagen QR temporal
    # ---------------------------------------------------------
    if os.path.exists(qr_path):
        try:
            os.remove(qr_path)
        except OSError:
            pass  # Si está bloqueado, lo ignoramos

    if pdf_status.err:
        print(f"Error generando PDF para pedido {pedido.folio}")
        return None

    return result.getvalue()


def enviar_ticket_email(pedido, pdf_bytes):
    """
    Recibe el objeto pedido y los bytes del PDF ya generado, y lo envía por correo.
    """
    if not pedido.cliente.email or not pdf_bytes:
        print("⚠️ No se puede enviar correo: Falta email del cliente o el PDF.")
        return False

    try:
        print(f"📧 Intentando enviar correo a {pedido.cliente.email}...")
        email = EmailMessage(
            subject=f'Tu Ticket de Servicio - {pedido.folio}',
            body=f'Hola {pedido.cliente.first_name}, gracias por elegir Punto Limpio. Adjunto encontrarás tu ticket con los detalles de tu servicio.',
            from_email=settings.EMAIL_HOST_USER,
            to=[pedido.cliente.email],
        )
        # Adjuntar el PDF
        email.attach(f'ticket_{pedido.folio}.pdf',
                     pdf_bytes, 'application/pdf')

        # Enviar el correo. fail_silently=False lanzará la excepción si falla,
        # lo que nos permite atraparla en los bloques except de abajo.
        email.send(fail_silently=False)

        print(f"✅ Correo enviado exitosamente a {pedido.cliente.email}")
        return True

    except socket.timeout:
        # Esto atrapa específicamente si Gmail tarda más de los 5 segundos que definimos en settings
        print(
            f"⏳ Error de Timeout: El servidor de correo tardó demasiado en responder para {pedido.folio}.")
        return False
    except smtplib.SMTPException as e:
        # Esto atrapa errores de autenticación (contraseña incorrecta, etc.)
        print(f"❌ Error SMTP al enviar correo ({pedido.folio}): {e}")
        return False
    except Exception as e:
        # Atrapa cualquier otro error imprevisto
        print(
            f"💥 Error general enviando correo al cliente {pedido.cliente.email}: {e}")
        return False
