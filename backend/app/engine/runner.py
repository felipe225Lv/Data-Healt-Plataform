"""Ejecución de una regla de calidad sobre su conjunto de datos (RF-04, RF-11, RF-19)."""

from app.core import clock
from app.core.exceptions import InvalidRuleError, NotFoundError
from app.domain.models import Anomaly, MetricResult
from app.engine.metrics import calculate_completeness, calculate_uniqueness, calculate_validity

PASSED = "PASSED"
FAILED = "FAILED"
ERROR = "ERROR"
QUALITY_RULE_FAILED = "QUALITY_RULE_FAILED"


class ValidationRunner:
    def __init__(self, rule_repository, dataset_repository, source_repository,
                 connector_factory, credential_cipher, metric_repository, incident_service):
        self.rules = rule_repository
        self.datasets = dataset_repository
        self.sources = source_repository
        self.connectors = connector_factory
        self.cipher = credential_cipher
        self.metrics = metric_repository
        self.incidents = incident_service

    def run_validation(self, rule_id: int) -> MetricResult:
        rule = self.rules.get_by_id(rule_id)
        if rule is None:
            raise NotFoundError("Regla no encontrada")
        dataset = self.datasets.get_by_id(rule.dataset_id)
        source_id = getattr(dataset, "source_id", None)

        try:
            source = self.sources.get_by_id(source_id)
            password = self.cipher.decrypt(source.encrypted_password) if source.encrypted_password else None
            connector = self.connectors.create(source, password)
            try:
                values = connector.fetch_column(dataset.name, rule.column)
            finally:
                connector.close()
            value = self._measure(rule, values)
        except Exception as exc:  # una fuente caída no detiene el monitoreo (RF-19)
            result = MetricResult(rule.id, rule.dataset_id, None, ERROR, clock.now(),
                                  detail=f"{type(exc).__name__}: {exc}", source_id=source_id)
            self.metrics.add(result)
            return result

        status = PASSED if value >= rule.threshold else FAILED
        result = MetricResult(rule.id, rule.dataset_id, value, status, clock.now(), source_id=source_id)
        self.metrics.add(result)

        if status == FAILED:
            self.incidents.create_incident(
                Anomaly(
                    type=QUALITY_RULE_FAILED,
                    dataset_id=rule.dataset_id,
                    dataset_name=getattr(dataset, "name", None),
                    source_id=source_id,
                    rule_id=rule.id,
                    value=value,
                    detail=f"Regla {rule.rule_type} sobre '{rule.column}': {value}% (umbral {rule.threshold}%)",
                )
            )
        return result

    @staticmethod
    def _measure(rule, values: list) -> float:
        if rule.rule_type == "completeness":
            return calculate_completeness(values)
        if rule.rule_type == "validity":
            return calculate_validity(values, rule.min_value, rule.max_value)
        if rule.rule_type == "uniqueness":
            records = [{rule.column: v} for v in values]
            return calculate_uniqueness(records, [rule.column]).uniqueness_pct
        raise InvalidRuleError(f"El tipo de regla '{rule.rule_type}' no se ejecuta por columna")
