"""CP-22 y CP-23 · IncidentService"""

from dataclasses import replace
from datetime import datetime, timezone

import pytest

from app.core.exceptions import IncidentAlreadyClosedError, ValidationError
from app.domain.models import Anomaly, Incident
from app.services.incident_service import IncidentService


@pytest.fixture
def servicio(incident_repository, alert_service):
    return IncidentService(incident_repository, alert_service)


@pytest.fixture
def anomalia():
    return Anomaly(type="VOLUME_DROP", dataset_id=5, dataset_name="public.facturas", deviation_pct=-40.0)


def _incidente(status="ABIERTO", occurrences=1):
    return Incident(id=30, dataset_id=5, dataset_name="public.facturas", type="VOLUME_DROP",
                    status=status, detected_at=datetime(2026, 11, 1, tzinfo=timezone.utc),
                    occurrences=occurrences)


# ---------------------------------------------------------------- CP-22 create_incident
def test_cp22_positivo_nuevo_incidente(servicio, incident_repository, alert_service, anomalia):
    incident_repository.find_open.return_value = None
    incident_repository.add.side_effect = lambda i: replace(i, id=30)

    incidente = servicio.create_incident(anomalia)

    assert incidente.id == 30
    assert incidente.status == "ABIERTO"
    assert incidente.occurrences == 1
    assert incidente.detected_at is not None
    incident_repository.find_open.assert_called_once_with(5, "VOLUME_DROP")
    alert_service.send_alert.assert_called_once_with(incidente)


def test_cp22_negativo_deduplicacion(servicio, incident_repository, alert_service, anomalia):
    abierto = _incidente(occurrences=1)
    incident_repository.find_open.return_value = abierto

    servicio.create_incident(anomalia)

    incident_repository.add.assert_not_called()
    assert abierto.occurrences == 2
    alert_service.send_alert.assert_not_called()


# ---------------------------------------------------------------- CP-23 close_incident
def test_cp23_positivo_cierra_incidente_abierto(servicio, incident_repository):
    incidente = _incidente()
    incident_repository.get_by_id.return_value = incidente

    servicio.close_incident(30, action_taken="Se recargó el archivo de ventas del día", user_id=3)

    assert incidente.status == "RESUELTO"
    assert incidente.resolved_by == 3
    assert incidente.action_taken == "Se recargó el archivo de ventas del día"
    assert incidente.resolved_at is not None
    incident_repository.update.assert_called_once_with(incidente)


def test_cp23_negativo_incidente_ya_cerrado(servicio, incident_repository):
    incidente = _incidente(status="RESUELTO")
    incident_repository.get_by_id.return_value = incidente

    with pytest.raises(IncidentAlreadyClosedError):
        servicio.close_incident(30, "Acción repetida de cierre", 3)

    incident_repository.update.assert_not_called()


def test_cp23_negativo_accion_vacia(servicio, incident_repository):
    incidente = _incidente()
    incident_repository.get_by_id.return_value = incidente

    with pytest.raises(ValidationError):
        servicio.close_incident(30, "   ", 3)

    assert incidente.status == "ABIERTO"
