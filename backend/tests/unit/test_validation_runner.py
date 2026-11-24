"""CP-19 · ValidationRunner.run_validation()"""

import pytest

from app.domain.models import Dataset, DataSource, Rule
from app.engine.runner import ValidationRunner
from tests.unit.fixtures.datos_calidad import COLUMNA_80, COLUMNA_98


@pytest.fixture
def runner(rule_repository, dataset_repository, source_repository, connector_factory,
           credential_cipher, metric_repository, incident_service):
    rule_repository.get_by_id.return_value = Rule(
        id=7, dataset_id=5, rule_type="completeness", column="nit_cliente",
        threshold=95.0, frequency_minutes=60,
    )
    dataset_repository.get_by_id.return_value = Dataset(id=5, source_id=1, name="ventas.csv", type="file")
    source_repository.get_by_id.return_value = DataSource(id=1, name="Ventas", type="csv", database="/data")
    return ValidationRunner(rule_repository, dataset_repository, source_repository, connector_factory,
                            credential_cipher, metric_repository, incident_service)


def test_cp19_positivo_regla_que_se_cumple(runner, connector_factory, metric_repository, incident_service):
    connector_factory.create.return_value.fetch_column.return_value = COLUMNA_98

    resultado = runner.run_validation(7)

    metric_repository.add.assert_called_once()
    guardado = metric_repository.add.call_args.args[0]
    assert guardado.value == 98.0
    assert guardado.status == "PASSED"
    assert resultado is guardado
    incident_service.create_incident.assert_not_called()


def test_cp19_negativo_regla_que_no_se_cumple(runner, connector_factory, metric_repository, incident_service):
    connector_factory.create.return_value.fetch_column.return_value = COLUMNA_80

    runner.run_validation(7)

    guardado = metric_repository.add.call_args.args[0]
    assert guardado.value == 80.0
    assert guardado.status == "FAILED"
    incident_service.create_incident.assert_called_once()
    anomalia = incident_service.create_incident.call_args.args[0]
    assert anomalia.rule_id == 7
    assert anomalia.value == 80.0


def test_cp19_negativo_error_de_conexion(runner, connector_factory, metric_repository, incident_service):
    connector_factory.create.side_effect = ConnectionError("fuente caída")

    resultado = runner.run_validation(7)  # no debe propagar la excepción

    assert resultado.status == "ERROR"
    assert "fuente caída" in resultado.detail
    metric_repository.add.assert_called_once_with(resultado)
    incident_service.create_incident.assert_not_called()
