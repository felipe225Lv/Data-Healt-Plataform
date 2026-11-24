"""CP-11 y CP-12 · DatasetService"""

from dataclasses import replace

import pytest

from app.core.exceptions import DuplicateNameError, NotFoundError
from app.domain.models import Dataset, DatasetCreateDTO
from app.services.dataset_service import DatasetService


@pytest.fixture
def servicio(dataset_repository, source_repository):
    return DatasetService(dataset_repository, source_repository)


@pytest.fixture
def dto_tabla():
    return DatasetCreateDTO(name="public.facturas", type="table")


# ---------------------------------------------------------------- CP-11 register_dataset
def test_cp11_positivo_registra_tabla(servicio, source_repository, dataset_repository,
                                      fuente_postgres, dto_tabla):
    source_repository.get_by_id.return_value = fuente_postgres
    dataset_repository.exists_in_source.return_value = False
    dataset_repository.add.side_effect = lambda d: replace(d, id=5)

    resultado = servicio.register_dataset(1, dto_tabla)

    assert resultado.id == 5
    assert resultado.source_id == 1
    assert resultado.type == "table"
    dataset_repository.exists_in_source.assert_called_once_with(1, "public.facturas")
    dataset_repository.add.assert_called_once()


def test_cp11_negativo_fuente_inexistente(servicio, source_repository, dataset_repository, dto_tabla):
    source_repository.get_by_id.return_value = None

    with pytest.raises(NotFoundError):
        servicio.register_dataset(99, dto_tabla)

    dataset_repository.add.assert_not_called()


def test_cp11_negativo_conjunto_duplicado(servicio, source_repository, dataset_repository,
                                          fuente_postgres, dto_tabla):
    source_repository.get_by_id.return_value = fuente_postgres
    dataset_repository.exists_in_source.return_value = True

    with pytest.raises(DuplicateNameError):
        servicio.register_dataset(1, dto_tabla)

    dataset_repository.add.assert_not_called()


# ---------------------------------------------------------------- CP-12 list_by_source
def test_cp12_positivo_fuente_con_conjuntos(servicio, dataset_repository):
    dataset_repository.list_by_source.return_value = [
        Dataset(id=5, source_id=1, name="public.facturas", type="table"),
        Dataset(id=6, source_id=1, name="public.clientes", type="table"),
    ]

    resultado = servicio.list_by_source(1)

    assert len(resultado) == 2
    assert [d.name for d in resultado] == ["public.facturas", "public.clientes"]


def test_cp12_positivo_fuente_sin_conjuntos(servicio, dataset_repository):
    dataset_repository.list_by_source.return_value = []

    assert servicio.list_by_source(2) == []
