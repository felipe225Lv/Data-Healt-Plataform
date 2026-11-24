"""Repositorios en memoria.

Implementan la misma interfaz que usan los servicios. En las pruebas unitarias
se reemplazan por mocks; en el ambiente de ejecución del ejercicio guardan los
datos en memoria del proceso (se reinician con el contenedor).
"""

from __future__ import annotations

import itertools
import threading
from datetime import date


class _Store:
    def __init__(self):
        self._items: dict[int, object] = {}
        self._ids = itertools.count(1)
        self._lock = threading.Lock()

    def add(self, item):
        with self._lock:
            item.id = next(self._ids)
            self._items[item.id] = item
            return item

    def update(self, item):
        with self._lock:
            self._items[item.id] = item
            return item

    def get_by_id(self, item_id):
        return self._items.get(item_id)

    def delete(self, item_id):
        with self._lock:
            self._items.pop(item_id, None)

    def all(self):
        return list(self._items.values())


class InMemoryUserRepository(_Store):
    def get_by_email(self, email: str):
        email = email.lower()
        return next((u for u in self.all() if u.email.lower() == email), None)

    def list(self, role: str | None = None, is_active: bool | None = None):
        return [
            u for u in self.all()
            if (role is None or u.role == role) and (is_active is None or u.is_active == is_active)
        ]


class InMemoryDataSourceRepository(_Store):
    def get_by_name(self, name: str):
        return next((s for s in self.all() if s.name.lower() == name.lower()), None)

    def list(self):
        return self.all()


class InMemoryDatasetRepository(_Store):
    def exists_in_source(self, source_id: int, name: str) -> bool:
        return any(d.source_id == source_id and d.name == name for d in self.all())

    def list_by_source(self, source_id: int):
        return [d for d in self.all() if d.source_id == source_id]


class InMemoryRuleRepository(_Store):
    def list_by_dataset(self, dataset_id: int):
        return [r for r in self.all() if r.dataset_id == dataset_id]


class InMemoryIncidentRepository(_Store):
    def find_open(self, dataset_id, incident_type):
        return next(
            (i for i in self.all()
             if i.dataset_id == dataset_id and i.type == incident_type and i.status == "ABIERTO"),
            None,
        )

    def list(self, status: str | None = None):
        return [i for i in self.all() if status is None or i.status == status]

    def count_by_source(self, source_id: int, start: date, end: date) -> int:
        return sum(
            1 for i in self.all()
            if i.source_id == source_id and start <= i.detected_at.date() <= end
        )


class _AppendOnly:
    def __init__(self):
        self.items: list = []

    def add(self, item):
        self.items.append(item)
        return item


class InMemoryAuditLogRepository(_AppendOnly):
    pass


class InMemoryAlertLogRepository(_AppendOnly):
    pass


class InMemoryMetricResultRepository(_AppendOnly):
    def list_by_source(self, source_id: int, start: date, end: date):
        return [
            m for m in self.items
            if m.source_id == source_id and start <= m.executed_at.date() <= end
        ]

    def last_by_rule(self, rule_id: int):
        results = [m for m in self.items if m.rule_id == rule_id]
        return results[-1] if results else None


class InMemoryChannelRepository:
    def __init__(self, channels=None):
        self.channels = list(channels or [])

    def get_active(self):
        return [c for c in self.channels if c.active]
