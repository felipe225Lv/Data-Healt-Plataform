"""Envío de correos de alerta."""

import logging
import smtplib
from email.message import EmailMessage

log = logging.getLogger("dhp.alerts")


class EmailNotifier:
    """Envía por SMTP. Si no hay servidor configurado, deja la alerta en el log."""

    def __init__(self, host: str | None = None, port: int = 587, user: str | None = None,
                 password: str | None = None, sender: str = "alertas@dhp.local"):
        self.host, self.port, self.user, self.password, self.sender = host, port, user, password, sender
        self.sent: list[dict] = []

    def send(self, recipients: list[str], subject: str, body: str) -> None:
        self.sent.append({"to": recipients, "subject": subject})
        if not self.host:
            log.warning("ALERTA (sin SMTP configurado) para %s: %s", ", ".join(recipients), subject)
            return
        msg = EmailMessage()
        msg["From"], msg["To"], msg["Subject"] = self.sender, ", ".join(recipients), subject
        msg.set_content(body)
        with smtplib.SMTP(self.host, self.port, timeout=10) as smtp:
            smtp.starttls()
            if self.user:
                smtp.login(self.user, self.password)
            smtp.send_message(msg)
