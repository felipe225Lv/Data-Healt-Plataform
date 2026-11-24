"""Detección de anomalías frente al comportamiento histórico (RF-05)."""

from app.domain.models import Anomaly, SchemaChange

VOLUME_DROP = "VOLUME_DROP"
VOLUME_SPIKE = "VOLUME_SPIKE"
SCHEMA_CHANGE = "SCHEMA_CHANGE"


class AnomalyDetector:
    def __init__(self, min_history: int = 3):
        self.min_history = min_history

    def detect_volume_anomaly(self, current_count: int, history: list[int],
                              tolerance_pct: float = 30.0) -> Anomaly | None:
        """Compara el volumen actual con el promedio histórico.

        Sin una línea base mínima (3 mediciones) no se evalúa, para evitar falsos positivos.
        """
        if len(history) < self.min_history:
            return None
        mean = sum(history) / len(history)
        if mean == 0:
            return None
        deviation = round((current_count - mean) / mean * 100, 2)
        if deviation < -tolerance_pct:
            return Anomaly(type=VOLUME_DROP, deviation_pct=deviation,
                           detail=f"Volumen {current_count} vs promedio {mean:.0f}")
        if deviation > tolerance_pct:
            return Anomaly(type=VOLUME_SPIKE, deviation_pct=deviation,
                           detail=f"Volumen {current_count} vs promedio {mean:.0f}")
        return None

    def detect_schema_change(self, previous: dict[str, str], current: dict[str, str]) -> SchemaChange:
        removed = sorted(set(previous) - set(current))
        added = sorted(set(current) - set(previous))
        type_changed = {
            col: (previous[col], current[col])
            for col in sorted(set(previous) & set(current))
            if previous[col] != current[col]
        }
        return SchemaChange(removed=removed, added=added, type_changed=type_changed)
