"""Registro y cierre de incidentes (RF-12, RF-13)."""

from app.core import clock
from app.core.exceptions import IncidentAlreadyClosedError, NotFoundError, ValidationError
from app.domain.models import Anomaly, Incident

ABIERTO = "ABIERTO"
RESUELTO = "RESUELTO"


class IncidentService:
    def __init__(self, incident_repository, alert_service):
        self.incidents = incident_repository
        self.alerts = alert_service

    def create_incident(self, anomaly: Anomaly) -> Incident:
        existing = self.incidents.find_open(anomaly.dataset_id, anomaly.type)
        if existing is not None:
            # Deduplicación: el mismo problema abierto no genera un incidente ni una alerta nueva
            existing.occurrences += 1
            self.incidents.update(existing)
            return existing

        incident = Incident(
            id=None,
            dataset_id=anomaly.dataset_id,
            dataset_name=anomaly.dataset_name,
            type=anomaly.type,
            status=ABIERTO,
            detected_at=clock.now(),
            detail=anomaly.detail,
            occurrences=1,
            rule_id=anomaly.rule_id,
            source_id=anomaly.source_id,
        )
        saved = self.incidents.add(incident)
        self.alerts.send_alert(saved)
        return saved

    def close_incident(self, incident_id: int, action_taken: str, user_id: int) -> Incident:
        incident = self.incidents.get_by_id(incident_id)
        if incident is None:
            raise NotFoundError("Incidente no encontrado")
        if incident.status == RESUELTO:
            raise IncidentAlreadyClosedError()
        if action_taken is None or not action_taken.strip():
            raise ValidationError("Debe registrar la acción tomada")
        incident.status = RESUELTO
        incident.action_taken = action_taken.strip()
        incident.resolved_by = user_id
        incident.resolved_at = clock.now()
        self.incidents.update(incident)
        return incident
