"""Entidades y DTO del dominio de Data Health Platform."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime

# ---------------------------------------------------------------- Usuarios


@dataclass
class User:
    id: int | None
    full_name: str
    email: str
    password_hash: str
    role: str
    is_active: bool = True
    failed_attempts: int = 0
    locked_until: datetime | None = None


@dataclass
class UserCreateDTO:
    full_name: str
    email: str
    password: str
    role: str


@dataclass
class UserUpdateDTO:
    full_name: str | None = None
    role: str | None = None


@dataclass
class UserOut:
    """Lo que la plataforma devuelve de un usuario: nunca la contraseña ni el hash."""

    id: int
    full_name: str
    email: str
    role: str
    is_active: bool

    @classmethod
    def from_entity(cls, user: User) -> UserOut:
        return cls(user.id, user.full_name, user.email, user.role, user.is_active)


@dataclass
class TokenResponse:
    access_token: str
    token_type: str = "bearer"


# ---------------------------------------------------------------- Fuentes y conjuntos


@dataclass
class DataSource:
    id: int | None
    name: str
    type: str
    host: str | None = None
    port: int | None = None
    database: str | None = None
    username: str | None = None
    encrypted_password: str | None = None
    last_connection_status: str | None = None


@dataclass
class DataSourceCreateDTO:
    name: str
    type: str
    host: str | None = None
    port: int | None = None
    database: str | None = None
    username: str | None = None
    password: str | None = None


@dataclass
class DataSourceUpdateDTO:
    name: str | None = None
    host: str | None = None
    port: int | None = None
    database: str | None = None
    username: str | None = None
    password: str | None = None


@dataclass
class DataSourceOut:
    id: int
    name: str
    type: str
    host: str | None
    port: int | None
    database: str | None
    last_connection_status: str | None

    @classmethod
    def from_entity(cls, s: DataSource) -> DataSourceOut:
        return cls(s.id, s.name, s.type, s.host, s.port, s.database, s.last_connection_status)


@dataclass
class ConnectionTestResult:
    status: str
    message: str


@dataclass
class Dataset:
    id: int | None
    source_id: int
    name: str
    type: str


@dataclass
class DatasetCreateDTO:
    name: str
    type: str


@dataclass
class DatasetOut:
    id: int
    source_id: int
    name: str
    type: str

    @classmethod
    def from_entity(cls, d: Dataset) -> DatasetOut:
        return cls(d.id, d.source_id, d.name, d.type)


# ---------------------------------------------------------------- Reglas y métricas

RULE_TYPES = ("completeness", "uniqueness", "validity", "freshness", "volume")
RULES_WITH_COLUMN = ("completeness", "uniqueness", "validity")


@dataclass
class Rule:
    id: int | None
    dataset_id: int
    rule_type: str
    column: str | None
    threshold: float
    frequency_minutes: int
    min_value: float | None = None
    max_value: float | None = None
    created_by: int | None = None


@dataclass
class RuleCreateDTO:
    rule_type: str
    column: str | None
    threshold: float
    frequency_minutes: int
    min_value: float | None = None
    max_value: float | None = None


@dataclass
class RuleUpdateDTO:
    column: str | None = None
    threshold: float | None = None
    frequency_minutes: int | None = None
    min_value: float | None = None
    max_value: float | None = None


@dataclass
class RuleOut:
    id: int
    dataset_id: int
    rule_type: str
    column: str | None
    threshold: float
    frequency_minutes: int

    @classmethod
    def from_entity(cls, r: Rule) -> RuleOut:
        return cls(r.id, r.dataset_id, r.rule_type, r.column, r.threshold, r.frequency_minutes)


@dataclass
class AuditLog:
    rule_id: int
    user_id: int
    action: str
    changes: dict
    timestamp: datetime


@dataclass
class MetricResult:
    rule_id: int
    dataset_id: int
    value: float | None
    status: str  # PASSED | FAILED | ERROR
    executed_at: datetime
    detail: str = ""
    source_id: int | None = None


@dataclass
class UniquenessResult:
    duplicates: int
    uniqueness_pct: float


@dataclass
class FreshnessResult:
    is_fresh: bool
    delay_hours: float


# ---------------------------------------------------------------- Anomalías e incidentes


@dataclass
class Anomaly:
    type: str
    dataset_id: int | None = None
    dataset_name: str | None = None
    source_id: int | None = None
    deviation_pct: float | None = None
    rule_id: int | None = None
    value: float | None = None
    detail: str = ""


@dataclass
class SchemaChange:
    removed: list[str] = field(default_factory=list)
    added: list[str] = field(default_factory=list)
    type_changed: dict[str, tuple[str, str]] = field(default_factory=dict)

    @property
    def has_changes(self) -> bool:
        return bool(self.removed or self.added or self.type_changed)


@dataclass
class Incident:
    id: int | None
    dataset_id: int | None
    dataset_name: str | None
    type: str
    status: str
    detected_at: datetime
    detail: str = ""
    occurrences: int = 1
    rule_id: int | None = None
    source_id: int | None = None
    action_taken: str | None = None
    resolved_by: int | None = None
    resolved_at: datetime | None = None


@dataclass
class NotificationChannel:
    type: str
    recipients: list[str]
    active: bool = True


@dataclass
class AlertLog:
    incident_id: int | None
    channel: str
    status: str  # ENVIADA | FALLIDA | SIN_CANAL
    sent_at: datetime


@dataclass
class QualityReport:
    source_id: int
    start: date
    end: date
    total_validations: int
    passed: int
    failed: int
    compliance_pct: float
    incidents_count: int
