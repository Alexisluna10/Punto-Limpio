import ssl
from django.core.mail.backends.smtp import EmailBackend


class CustomEmailBackend(EmailBackend):
    """
    Backend de email personalizado que deshabilita la verificación SSL.
    Necesario en algunos entornos de desarrollo donde los certificados
    de CA no están correctamente configurados.
    """

    def open(self):
        if self.connection:
            return False

        try:
            # Crear la conexión SMTP normalmente
            self.connection = self.connection_class(
                self.host, self.port, timeout=self.timeout)
            if self.use_tls:
                # Crear contexto SSL que no verifica certificados
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                self.connection.ehlo()
                self.connection.starttls(context=context)
                self.connection.ehlo()

            if self.username and self.password:
                self.connection.login(self.username, self.password)

            return True

        except OSError:
            if not self.fail_silently:
                raise
