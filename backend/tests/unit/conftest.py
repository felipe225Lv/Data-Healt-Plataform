"""Fixtures compartidas de las pruebas unitarias.

Todas las dependencias externas (repositorios, cifrado, conectores, scheduler,
SMTP) se reemplazan por objetos MagicMock, como lo define el Plan de Pruebas.
"""

from unittest.mock import MagicMock

import pytest

from app.domain.models import DataSource, User


# ---------------------------------------------------------------- dependencias simuladas
@pytest.fixture
def user_repository():
    return MagicMock(name="UserRepository")


@pytest.fixture
def password_hasher():
    return MagicMock(name="PasswordHasher")


@pytest.fixture
def token_provider():
    return MagicMock(name="TokenProvider")


@pytest.fixture
def source_repository():
    return MagicMock(name="DataSourceRepository")


@pytest.fixture
def dataset_repository():
    return MagicMock(name="DatasetRepository")


@pytest.fixture
def credential_cipher():
    return MagicMock(name="CredentialCipher")


@pytest.fixture
def connector_factory():
    return MagicMock(name="ConnectorFactory")


@pytest.fixture
def scheduler():
    return MagicMock(name="SchedulerService")


@pytest.fixture
def rule_repository():
    return MagicMock(name="RuleRepository")


@pytest.fixture
def audit_repository():
    return MagicMock(name="AuditLogRepository")


@pytest.fixture
def metric_repository():
    return MagicMock(name="MetricResultRepository")


@pytest.fixture
def incident_repository():
    return MagicMock(name="IncidentRepository")


@pytest.fixture
def incident_service():
    return MagicMock(name="IncidentService")


@pytest.fixture
def alert_service():
    return MagicMock(name="AlertService")


# ---------------------------------------------------------------- datos de prueba
@pytest.fixture
def usuario_analista():
    return User(
        id=3,
        full_name="Andrea Ríos",
        email="analista@pyme.co",
        password_hash="hash_bcrypt",
        role="ANALISTA",
        is_active=True,
        failed_attempts=0,
    )


@pytest.fixture
def fuente_postgres():
    return DataSource(
        id=1,
        name="ERP Ventas",
        type="postgresql",
        host="10.0.0.5",
        port=5432,
        database="ventas",
        username="lector",
        encrypted_password="gAAAA_cifrado",
    )
