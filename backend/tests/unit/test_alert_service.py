"""CP-24 · AlertService.send_alert()"""

import smtplib
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from app.domain.models import Incident, NotificationChannel
from app.services.alert_service import AlertService


@pytest.fixture
def channel_repository():
    return MagicMock(name="NotificationChannelRepository")


@pytest.fixture
def email_notifier():
    return MagicMock(name="EmailNotifier")


@pytest.fixture
def alert_log_repository():
    return MagicMock(name="AlertLogRepository")


@pytest.fixture
def servicio(channel_repository, email_notifier, alert_log_repository, scheduler):
    return AlertService(channel_repository, email_notifier, alert_log_repository, scheduler)


@pytest.fixture
def incidente():
    return Incident(id=30, dataset_id=5, dataset_name="public.facturas", type="VOLUME_DROP",
                    status="ABIERTO", detected_at=datetime(2026, 11, 1, 10, 0, tzinfo=timezone.utc))


@pytest.fixture
def canal_email():
    return NotificationChannel(type="email", recipients=["datos@pyme.co", "gerencia@pyme.co"])


def test_cp24_positivo_envio_por_correo(servicio, channel_repository, email_notifier,
                                        alert_log_repository, incidente, canal_email):
    channel_repository.get_active.return_value = [canal_email]

    servicio.send_alert(incidente)

    email_notifier.send.assert_called_once()
    destinatarios, asunto, _ = email_notifier.send.call_args.args
    assert destinatarios == ["datos@pyme.co", "gerencia@pyme.co"]
    assert "public.facturas" in asunto
    assert "VOLUME_DROP" in asunto
    assert alert_log_repository.add.call_args.args[0].status == "ENVIADA"


def test_cp24_negativo_falla_smtp(servicio, channel_repository, email_notifier, alert_log_repository,
                                  scheduler, incidente, canal_email):
    channel_repository.get_active.return_value = [canal_email]
    email_notifier.send.side_effect = smtplib.SMTPException("servidor no disponible")

    servicio.send_alert(incidente)  # no debe propagar la excepción

    assert alert_log_repository.add.call_args.args[0].status == "FALLIDA"
    scheduler.retry_alert.assert_called_once_with(30)


def test_cp24_negativo_sin_canales(servicio, channel_repository, email_notifier,
                                   alert_log_repository, incidente):
    channel_repository.get_active.return_value = []

    servicio.send_alert(incidente)

    email_notifier.send.assert_not_called()
    assert alert_log_repository.add.call_args.args[0].status == "SIN_CANAL"
