import smtplib
from email.mime.text import MIMEText

from finanzas.application.ports.enviador_email import EnviadorEmail
from finanzas.config.settings import settings


class EnviadorEmailSMTP(EnviadorEmail):
    def enviar(self, para: str, asunto: str, cuerpo_html: str) -> None:
        msg = MIMEText(cuerpo_html, "html")
        msg["Subject"] = asunto
        msg["From"] = settings.email_from
        msg["To"] = para

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)
