"""Métricas de calidad de datos (dimensiones de completitud, unicidad, validez y oportunidad).

Son funciones puras: reciben datos en memoria y devuelven el resultado.
"""

from datetime import datetime

from app.core import clock
from app.core.exceptions import EmptyDatasetError
from app.domain.models import FreshnessResult, UniquenessResult


def _is_missing(value) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")


def calculate_completeness(values: list) -> float:
    """Porcentaje de valores no vacíos. None y cadenas vacías cuentan como faltantes."""
    if not values:
        raise EmptyDatasetError()
    present = sum(1 for v in values if not _is_missing(v))
    return round(present / len(values) * 100, 2)


def calculate_uniqueness(records: list[dict], key_columns: list[str]) -> UniquenessResult:
    """Registros duplicados según una o varias columnas clave."""
    if not records:
        raise EmptyDatasetError()
    keys = [tuple(r.get(col) for col in key_columns) for r in records]
    distinct = len(set(keys))
    return UniquenessResult(
        duplicates=len(keys) - distinct,
        uniqueness_pct=round(distinct / len(keys) * 100, 2),
    )


def calculate_validity(values: list, min_value: float, max_value: float) -> float:
    """Porcentaje de valores dentro de [min_value, max_value]. Los nulos no se evalúan."""
    if min_value > max_value:
        raise ValueError("min_value no puede ser mayor que max_value")
    evaluated = [float(v) for v in values if not _is_missing(v)]
    if not evaluated:
        raise EmptyDatasetError()
    valid = sum(1 for v in evaluated if min_value <= v <= max_value)
    return round(valid / len(evaluated) * 100, 2)


def calculate_freshness(last_updated: datetime, max_delay_hours: float,
                        now: datetime | None = None) -> FreshnessResult:
    """Indica si el conjunto se actualizó dentro del tiempo máximo esperado."""
    now = now or clock.now()
    delay_hours = round((now - last_updated).total_seconds() / 3600, 2)
    return FreshnessResult(is_fresh=delay_hours <= max_delay_hours, delay_hours=delay_hours)
