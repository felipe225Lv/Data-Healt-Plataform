"""CP-15 a CP-18 · Funciones de métricas del motor de calidad (sin mocks)"""

from datetime import datetime, timezone

import pytest

from app.core.exceptions import EmptyDatasetError
from app.engine.metrics import (
    calculate_completeness,
    calculate_freshness,
    calculate_uniqueness,
    calculate_validity,
)
from tests.unit.fixtures.datos_calidad import (
    COLUMNA_COMPLETA,
    COLUMNA_CON_FALTANTES,
    REGISTROS_CLAVE_COMPUESTA,
    REGISTROS_CON_DUPLICADOS,
    VALORES_RANGO,
)

AHORA = datetime(2026, 11, 1, 10, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------- CP-15 completitud
def test_cp15_positivo_columna_con_faltantes():
    assert calculate_completeness(COLUMNA_CON_FALTANTES) == pytest.approx(70.0)


def test_cp15_positivo_columna_completa():
    assert calculate_completeness(COLUMNA_COMPLETA) == 100.0


def test_cp15_negativo_conjunto_vacio():
    with pytest.raises(EmptyDatasetError):
        calculate_completeness([])


# ---------------------------------------------------------------- CP-16 unicidad
def test_cp16_positivo_duplicados_clave_simple():
    resultado = calculate_uniqueness(REGISTROS_CON_DUPLICADOS, key_columns=["nit"])

    assert resultado.duplicates == 2
    assert resultado.uniqueness_pct == pytest.approx(66.67, abs=0.01)


def test_cp16_positivo_clave_compuesta():
    resultado = calculate_uniqueness(REGISTROS_CLAVE_COMPUESTA, key_columns=["nit", "fecha"])

    assert resultado.duplicates == 0
    assert resultado.uniqueness_pct == 100.0


# ---------------------------------------------------------------- CP-17 validez
def test_cp17_positivo_valores_dentro_y_fuera_de_rango():
    assert calculate_validity(VALORES_RANGO, 0, 100) == pytest.approx(60.0)


def test_cp17_negativo_rango_mal_definido():
    with pytest.raises(ValueError, match="min_value no puede ser mayor que max_value"):
        calculate_validity(VALORES_RANGO, 100, 0)


# ---------------------------------------------------------------- CP-18 oportunidad
def test_cp18_positivo_datos_actualizados():
    resultado = calculate_freshness(datetime(2026, 11, 1, 8, 30, tzinfo=timezone.utc), 2, AHORA)

    assert resultado.is_fresh is True
    assert resultado.delay_hours == 1.5


def test_cp18_positivo_valor_limite_exacto():
    resultado = calculate_freshness(datetime(2026, 11, 1, 8, 0, tzinfo=timezone.utc), 2, AHORA)

    assert resultado.is_fresh is True


def test_cp18_negativo_datos_desactualizados():
    resultado = calculate_freshness(datetime(2026, 10, 31, 20, 0, tzinfo=timezone.utc), 2, AHORA)

    assert resultado.is_fresh is False
    assert resultado.delay_hours == 14.0
