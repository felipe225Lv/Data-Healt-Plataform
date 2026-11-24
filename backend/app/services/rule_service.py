"""Reglas de calidad con umbral y frecuencia (RF-03, RF-15, RF-17) y su auditoría (RF-18)."""

from app.core import clock
from app.core.exceptions import InvalidRuleError, NotFoundError
from app.domain.models import (
    RULE_TYPES,
    RULES_WITH_COLUMN,
    AuditLog,
    Rule,
    RuleCreateDTO,
    RuleOut,
    RuleUpdateDTO,
)

MIN_FREQUENCY = 5
MAX_FREQUENCY = 1440


def validate_rule(rule_type: str, column: str | None, threshold: float, frequency_minutes: int) -> None:
    if rule_type not in RULE_TYPES:
        raise InvalidRuleError(f"Tipo de regla no soportado: {rule_type}")
    if threshold is None or not 0 <= threshold <= 100:
        raise InvalidRuleError("El umbral debe estar entre 0 y 100")
    if not MIN_FREQUENCY <= frequency_minutes <= MAX_FREQUENCY:
        raise InvalidRuleError("La frecuencia debe estar entre 5 y 1440 minutos")
    if rule_type in RULES_WITH_COLUMN and not column:
        raise InvalidRuleError("La columna es obligatoria para este tipo de regla")


class RuleService:
    def __init__(self, rule_repository, dataset_repository, audit_repository, scheduler):
        self.rules = rule_repository
        self.datasets = dataset_repository
        self.audit = audit_repository
        self.scheduler = scheduler

    def create_rule(self, dataset_id: int, dto: RuleCreateDTO, user_id: int) -> RuleOut:
        validate_rule(dto.rule_type, dto.column, dto.threshold, dto.frequency_minutes)
        if self.datasets.get_by_id(dataset_id) is None:
            raise NotFoundError("Conjunto de datos no encontrado")
        rule = Rule(
            id=None,
            dataset_id=dataset_id,
            rule_type=dto.rule_type,
            column=dto.column,
            threshold=dto.threshold,
            frequency_minutes=dto.frequency_minutes,
            min_value=dto.min_value,
            max_value=dto.max_value,
            created_by=user_id,
        )
        saved = self.rules.add(rule)
        self.scheduler.schedule_rule(saved.id, saved.frequency_minutes)
        self.audit.add(AuditLog(saved.id, user_id, "CREATE", {}, clock.now()))
        return RuleOut.from_entity(saved)

    def update_rule(self, rule_id: int, dto: RuleUpdateDTO, user_id: int) -> RuleOut:
        rule = self.rules.get_by_id(rule_id)
        if rule is None:
            raise NotFoundError("Regla no encontrada")

        changes: dict[str, list] = {}
        for field_name in ("column", "threshold", "frequency_minutes", "min_value", "max_value"):
            new_value = getattr(dto, field_name)
            old_value = getattr(rule, field_name)
            if new_value is not None and new_value != old_value:
                changes[field_name] = [old_value, new_value]

        validate_rule(
            rule.rule_type,
            dto.column if dto.column is not None else rule.column,
            dto.threshold if dto.threshold is not None else rule.threshold,
            dto.frequency_minutes if dto.frequency_minutes is not None else rule.frequency_minutes,
        )
        for field_name, (_, new_value) in changes.items():
            setattr(rule, field_name, new_value)

        saved = self.rules.update(rule)
        if changes:
            self.audit.add(AuditLog(rule_id, user_id, "UPDATE", changes, clock.now()))
        if "frequency_minutes" in changes:
            self.scheduler.reschedule_rule(rule_id, rule.frequency_minutes)
        return RuleOut.from_entity(saved)
