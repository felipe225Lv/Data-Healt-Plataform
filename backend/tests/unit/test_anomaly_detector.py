"""CP-20 y CP-21 · AnomalyDetector"""

import pytest

from app.engine.anomaly import AnomalyDetector
from tests.unit.fixtures.datos_calidad import HISTORIAL_VOLUMEN


@pytest.fixture
def detector():
    return AnomalyDetector()


# ---------------------------------------------------------------- CP-20 volumen
def test_cp20_positivo_volumen_normal(detector):
    assert detector.detect_volume_anomaly(1050, HISTORIAL_VOLUMEN, 30) is None


def test_cp20_negativo_caida_de_volumen(detector):
    anomalia = detector.detect_volume_anomaly(600, HISTORIAL_VOLUMEN, 30)

    assert anomalia.type == "VOLUME_DROP"
    assert anomalia.deviation_pct == -40.0


def test_cp20_negativo_aumento_de_volumen(detector):
    anomalia = detector.detect_volume_anomaly(1500, HISTORIAL_VOLUMEN, 30)

    assert anomalia.type == "VOLUME_SPIKE"
    assert anomalia.deviation_pct == 50.0


def test_cp20_negativo_historial_insuficiente(detector):
    assert detector.detect_volume_anomaly(100, [1000, 990], 30) is None


# ---------------------------------------------------------------- CP-21 esquema
def test_cp21_negativo_esquema_modificado(detector):
    anterior = {"id": "int", "nit": "varchar", "total": "numeric"}
    actual = {"id": "int", "nit": "int", "descuento": "numeric"}

    cambio = detector.detect_schema_change(anterior, actual)

    assert cambio.removed == ["total"]
    assert cambio.added == ["descuento"]
    assert cambio.type_changed == {"nit": ("varchar", "int")}
    assert cambio.has_changes is True


def test_cp21_positivo_esquema_sin_cambios(detector):
    anterior = {"id": "int", "nit": "varchar", "total": "numeric"}
    actual = {"total": "numeric", "id": "int", "nit": "varchar"}

    cambio = detector.detect_schema_change(anterior, actual)

    assert cambio.has_changes is False
    assert cambio.removed == [] and cambio.added == [] and cambio.type_changed == {}
