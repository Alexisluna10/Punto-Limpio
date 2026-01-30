import qrcode
import os
from io import BytesIO
from django.core.mail import EmailMessage
from django.template.loader import get_template
from django.conf import settings
from xhtml2pdf import pisa


def render_pdf_ticket(pedido):
    """
    Genera el contenido en bytes del PDF del ticket.
    Retorna los bytes del PDF o None si hay error.
    """
    # 1. Generar Código QR (Apunta a una URL de rastreo)
    # Ajusta 'localhost:8000' por tu dominio real cuando lo subas a internet
    url_rastreo = f"http://localhost:8000/cliente/rastreo-servicio/?folio={pedido.folio}"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url_rastreo)
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="black", back_color="white")

    # Guardar QR temporalmente para que xhtml2pdf lo pueda leer
    qr_filename = f'qr_{pedido.folio}.png'
    qr_path = os.path.join(settings.MEDIA_ROOT, qr_filename)

    # Asegurar que existe el directorio media
    os.makedirs(settings.MEDIA_ROOT, exist_ok=True)

    img_qr.save(qr_path)

    # 2. Renderizar Template HTML con los datos
    template_path = 'gestion/tickets/tickets_pdf.html'
    context = {
        'pedido': pedido,
        'qr_path': qr_path,
        # Puedes pasar más variables de contexto si lo necesitas
    }

    template = get_template(template_path)
    html = template.render(context)

    # 3. Generar PDF en memoria
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)

    # Limpieza: borrar la imagen QR temporal del disco
    if os.path.exists(qr_path):
        os.remove(qr_path)

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
