"""Reloj de la aplicación.

Todos los servicios piden la hora por aquí, así en las pruebas se puede
congelar el tiempo con freezegun y los resultados son repetibles.
"""

from datetime import datetime, timezone


def now() -> datetime:
    return datetime.now(timezone.utc)
