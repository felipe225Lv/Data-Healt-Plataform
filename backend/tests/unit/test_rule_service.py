"""CP-13 y CP-14 · RuleService"""

from dataclasses import replace
from datetime import datetime, timezone

import pytest
from freezegun import freeze_time

from app.core.exceptions import InvalidRuleError
from app.domain.models import Dataset, Rule, RuleCreateDTO, RuleUpdateDTO
from app.services.rule_service import RuleService


@pytest.fixture
def servicio(rule_repository, dataset_repository, audit_repository, scheduler):
    dataset_repository.get_by_id.return_value = Dataset(id=5, source_id=1, name="public.facturas", type="table")
    return RuleService(rule_repository, dataset_repository, audit_repository, scheduler)


@pytest.fixture
def regla_existente():
    return Rule(id=7, dataset_id=5, rule_type="completeness", column="nit_cliente",
                threshold=95.0, frequency_minutes=60)


# ---------------------------------------------------------------- CP-13 create_rule
def test_cp13_positivo_regla_completitud_valida(servicio, rule_repository, scheduler, audit_repository):
    rule_repository.add.side_effect = lambda r: replace(r, id=7)
    dto = RuleCreateDTO(rule_type="completeness", column="nit_cliente", threshold=95.0, frequency_minutes=60)

    resultado = servicio.create_rule(dataset_id=5, dto=dto, user_id=3)

    assert resultado.id == 7
    assert resultado.threshold == 95.0
    scheduler.schedule_rule.assert_called_once_with(7, 60)
    audit_repository.add.assert_called_once()
    registro = audit_repository.add.call_args.args[0]
    assert registro.action == "CREATE"
    assert registro.user_id == 3


def test_cp13_negativo_umbral_fuera_de_rango(servicio, rule_repository, scheduler):
    dto = RuleCreateDTO(rule_type="completeness", column="nit_cliente", threshold=120.0, frequency_minutes=60)

    with pytest.raises(InvalidRuleError, match="El umbral debe estar entre 0 y 100"):
        servicio.create_rule(5, dto, user_id=3)

    rule_repository.add.assert_not_called()
    scheduler.schedule_rule.assert_not_called()


def test_cp13_negativo_completitud_sin_columna(servicio, rule_repository):
    dto = RuleCreateDTO(rule_type="completeness", column=None, threshold=95.0, frequency_minutes=60)

    with pytest.raises(InvalidRuleError, match="columna es obligatoria"):
        servicio.create_rule(5, dto, user_id=3)

    rule_repository.add.assert_not_called()


# ---------------------------------------------------------------- CP-14 update_rule
@freeze_time("2026-11-01 10:00:00")
def test_cp14_positivo_cambio_de_umbral_y_frecuencia(servicio, rule_repository, audit_repository,
                                                     scheduler, regla_existente):
    rule_repository.get_by_id.return_value = regla_existente
    rule_repository.update.side_effect = lambda r: r

    resultado = servicio.update_rule(7, RuleUpdateDTO(threshold=90.0, frequency_minutes=30), user_id=3)

    assert resultado.threshold == 90.0
    registro = audit_repository.add.call_args.args[0]
    assert registro.rule_id == 7
    assert registro.user_id == 3
    assert registro.action == "UPDATE"
    assert registro.changes == {"threshold": [95.0, 90.0], "frequency_minutes": [60, 30]}
    assert registro.timestamp == datetime(2026, 11, 1, 10, 0, tzinfo=timezone.utc)
    scheduler.reschedule_rule.assert_called_once_with(7, 30)


def test_cp14_positivo_cambio_sin_modificar_frecuencia(servicio, rule_repository, audit_repository,
                                                       scheduler, regla_existente):
    rule_repository.get_by_id.return_value = regla_existente
    rule_repository.update.side_effect = lambda r: r

    servicio.update_rule(7, RuleUpdateDTO(threshold=85.0), user_id=3)

    registro = audit_repository.add.call_args.args[0]
    assert registro.changes == {"threshold": [95.0, 85.0]}
    scheduler.reschedule_rule.assert_not_called()
