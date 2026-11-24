"""Gestión de fuentes de datos (RF-02)."""

from app.core.exceptions import DuplicateNameError, NotFoundError
from app.domain.models import (
    ConnectionTestResult,
    DataSource,
    DataSourceCreateDTO,
    DataSourceOut,
    DataSourceUpdateDTO,
)


class DataSourceService:
    def __init__(self, source_repository, credential_cipher, connector_factory, scheduler):
        self.sources = source_repository
        self.cipher = credential_cipher
        self.connectors = connector_factory
        self.scheduler = scheduler

    def create_source(self, dto: DataSourceCreateDTO) -> DataSourceOut:
        if self.sources.get_by_name(dto.name) is not None:
            raise DuplicateNameError(f"Ya existe una fuente con el nombre '{dto.name}'")
        source = DataSource(
            id=None,
            name=dto.name,
            type=dto.type,
            host=dto.host,
            port=dto.port,
            database=dto.database,
            username=dto.username,
            encrypted_password=self.cipher.encrypt(dto.password) if dto.password else None,
        )
        return DataSourceOut.from_entity(self.sources.add(source))

    def test_connection(self, source_id: int) -> ConnectionTestResult:
        source = self._get(source_id)
        password = self.cipher.decrypt(source.encrypted_password) if source.encrypted_password else None
        connector = None
        try:
            connector = self.connectors.create(source, password)
            connector.ping()
            result = ConnectionTestResult("ok", f"Conexión exitosa con '{source.name}'")
        except Exception:
            # El detalle de la excepción no se muestra: podría incluir credenciales
            result = ConnectionTestResult("failed", f"No fue posible conectar con la fuente '{source.name}'")
        finally:
            if connector is not None:
                connector.close()
        source.last_connection_status = result.status
        self.sources.update(source)
        return result

    def update_source(self, source_id: int, dto: DataSourceUpdateDTO) -> DataSourceOut:
        source = self._get(source_id)
        for field_name in ("name", "host", "port", "database", "username"):
            value = getattr(dto, field_name)
            if value is not None:
                setattr(source, field_name, value)
        if dto.password:
            source.encrypted_password = self.cipher.encrypt(dto.password)
        return DataSourceOut.from_entity(self.sources.update(source))

    def delete_source(self, source_id: int) -> bool:
        self._get(source_id)
        self.scheduler.unschedule_source(source_id)
        self.sources.delete(source_id)
        return True

    def list_sources(self) -> list[DataSourceOut]:
        return [DataSourceOut.from_entity(s) for s in self.sources.list()]

    def _get(self, source_id: int) -> DataSource:
        source = self.sources.get_by_id(source_id)
        if source is None:
            raise NotFoundError("Fuente no encontrada")
        return source
