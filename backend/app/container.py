"""Arma las dependencias de la aplicación (inyección de dependencias manual)."""

import os
from pathlib import Path

from app.core.security import CredentialCipher, PasswordHasher, TokenProvider
from app.domain.models import (
    DatasetCreateDTO,
    DataSourceCreateDTO,
    NotificationChannel,
    RuleCreateDTO,
    User,
)
from app.engine.anomaly import AnomalyDetector
from app.engine.runner import ValidationRunner
from app.infra.connectors import ConnectorFactory
from app.infra.notifier import EmailNotifier
from app.infra.scheduler import InMemoryScheduler
from app.repositories.memory import (
    InMemoryAlertLogRepository,
    InMemoryAuditLogRepository,
    InMemoryChannelRepository,
    InMemoryDatasetRepository,
    InMemoryDataSourceRepository,
    InMemoryIncidentRepository,
    InMemoryMetricResultRepository,
    InMemoryRuleRepository,
    InMemoryUserRepository,
)
from app.services.alert_service import AlertService
from app.services.auth_service import AuthService
from app.services.datasource_service import DataSourceService
from app.services.dataset_service import DatasetService
from app.services.incident_service import IncidentService
from app.services.report_service import ReportService
from app.services.rule_service import RuleService
from app.services.user_service import UserService

SAMPLE_DATA_DIR = os.getenv("SAMPLE_DATA_DIR", str(Path(__file__).resolve().parent.parent / "sample_data"))

USUARIOS_DEMO = [
    ("Administrador DHP", "admin@dhp.test", "Admin#2026", "ADMIN"),
    ("Analista DHP", "analista@dhp.test", "Analista#2026", "ANALISTA"),
    ("Usuario Negocio", "negocio@dhp.test", "Negocio#2026", "NEGOCIO"),
]


class Container:
    def __init__(self):
        # Infraestructura
        self.hasher = PasswordHasher()
        self.tokens = TokenProvider(os.getenv("JWT_SECRET", "dhp-secreto-solo-para-desarrollo"))
        self.cipher = CredentialCipher(os.getenv("FERNET_KEY") or None)
        self.connectors = ConnectorFactory()
        self.scheduler = InMemoryScheduler()
        self.notifier = EmailNotifier(
            host=os.getenv("SMTP_HOST") or None,
            port=int(os.getenv("SMTP_PORT", "587")),
            user=os.getenv("SMTP_USER") or None,
            password=os.getenv("SMTP_PASSWORD") or None,
        )

        # Repositorios
        self.users = InMemoryUserRepository()
        self.sources = InMemoryDataSourceRepository()
        self.datasets = InMemoryDatasetRepository()
        self.rules = InMemoryRuleRepository()
        self.audit = InMemoryAuditLogRepository()
        self.metrics = InMemoryMetricResultRepository()
        self.incidents = InMemoryIncidentRepository()
        self.alert_logs = InMemoryAlertLogRepository()
        recipients = [r.strip() for r in os.getenv("ALERT_RECIPIENTS", "datos@dhp.test").split(",") if r.strip()]
        self.channels = InMemoryChannelRepository([NotificationChannel("email", recipients)])

        # Servicios
        self.auth_service = AuthService(self.users, self.hasher, self.tokens)
        self.user_service = UserService(self.users, self.hasher)
        self.source_service = DataSourceService(self.sources, self.cipher, self.connectors, self.scheduler)
        self.dataset_service = DatasetService(self.datasets, self.sources)
        self.rule_service = RuleService(self.rules, self.datasets, self.audit, self.scheduler)
        self.alert_service = AlertService(self.channels, self.notifier, self.alert_logs, self.scheduler)
        self.incident_service = IncidentService(self.incidents, self.alert_service)
        self.report_service = ReportService(self.metrics, self.incidents)
        self.runner = ValidationRunner(self.rules, self.datasets, self.sources, self.connectors,
                                       self.cipher, self.metrics, self.incident_service)
        self.anomaly_detector = AnomalyDetector()

    def seed(self) -> None:
        """Datos de demostración para el dashboard y las pruebas de humo."""
        for full_name, email, password, role in USUARIOS_DEMO:
            self.users.add(User(None, full_name, email, self.hasher.hash(password), role))

        fuente = self.source_service.create_source(
            DataSourceCreateDTO(name="Ventas demo (CSV)", type="csv", database=SAMPLE_DATA_DIR)
        )
        ventas = self.dataset_service.register_dataset(fuente.id, DatasetCreateDTO("ventas.csv", "file"))
        admin_id = self.users.get_by_email("admin@dhp.test").id
        reglas = [
            RuleCreateDTO("completeness", "nit_cliente", 95.0, 60),
            RuleCreateDTO("validity", "total", 90.0, 60, min_value=0, max_value=10_000_000),
            RuleCreateDTO("uniqueness", "factura", 100.0, 1440),
        ]
        for dto in reglas:
            regla = self.rule_service.create_rule(ventas.id, dto, admin_id)
            self.runner.run_validation(regla.id)
