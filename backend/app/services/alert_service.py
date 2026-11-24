"""Envío de alertas por los canales configurados (RF-06, RF-14)."""

from app.core import clock
from app.domain.models import AlertLog, Incident

ENVIADA = "ENVIADA"
FALLIDA = "FALLIDA"
SIN_CANAL = "SIN_CANAL"


class AlertService:
    def __init__(self, channel_repository, email_notifier, alert_log_repository, scheduler):
        self.channels = channel_repository
        self.notifier = email_notifier
        self.logs = alert_log_repository
        self.scheduler = scheduler

    def send_alert(self, incident: Incident) -> list[AlertLog]:
        channels = self.channels.get_active()
        if not channels:
            log = AlertLog(incident.id, "-", SIN_CANAL, clock.now())
            self.logs.add(log)
            return [log]

        subject = f"[DHP] Incidente {incident.type} en {incident.dataset_name}"
        body = (
            f"Se detectó un incidente de calidad de datos.\n\n"
            f"Conjunto de datos: {incident.dataset_name}\n"
            f"Tipo: {incident.type}\n"
            f"Detalle: {incident.detail}\n"
            f"Detectado: {incident.detected_at:%Y-%m-%d %H:%M} UTC\n"
        )
        logs = []
        for channel in channels:
            try:
                self.notifier.send(channel.recipients, subject, body)
                status = ENVIADA
            except Exception:
                status = FALLIDA
                self.scheduler.retry_alert(incident.id)
            log = AlertLog(incident.id, channel.type, status, clock.now())
            self.logs.add(log)
            logs.append(log)
        return logs
