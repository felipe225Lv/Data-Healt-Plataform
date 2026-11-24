"""Registro de conjuntos de datos por fuente (RF-10)."""

from app.core.exceptions import DuplicateNameError, NotFoundError
from app.domain.models import Dataset, DatasetCreateDTO, DatasetOut


class DatasetService:
    def __init__(self, dataset_repository, source_repository):
        self.datasets = dataset_repository
        self.sources = source_repository

    def register_dataset(self, source_id: int, dto: DatasetCreateDTO) -> DatasetOut:
        if self.sources.get_by_id(source_id) is None:
            raise NotFoundError("Fuente no encontrada")
        if self.datasets.exists_in_source(source_id, dto.name):
            raise DuplicateNameError("El conjunto de datos ya existe en esta fuente")
        dataset = Dataset(id=None, source_id=source_id, name=dto.name, type=dto.type)
        return DatasetOut.from_entity(self.datasets.add(dataset))

    def list_by_source(self, source_id: int) -> list[DatasetOut]:
        return [DatasetOut.from_entity(d) for d in self.datasets.list_by_source(source_id)]
