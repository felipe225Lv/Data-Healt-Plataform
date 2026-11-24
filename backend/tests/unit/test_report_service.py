"""CP-25 · ReportService.generate_quality_report()"""

from datetime import date, datetime, timezone

import pytest

from app.core.exceptions import InvalidDateRangeError
from app.domain.models import MetricResult
from app.services.report_service import ReportService


@pytest.fixture
def servicio(metric_repository, incident_repository):
    return ReportService(metric_repository, incident_repository)


def _resultado(status):
    return MetricResult(rule_id=7, dataset_id=5, value=90.0, status=status,
                        executed_at=datetime(2026, 11, 10, tzinfo=timezone.utc), source_id=1)


def test_cp25_positivo_reporte_con_datos(servicio, metric_repository, incident_repository):
    metric_repository.list_by_source.return_value = [_resultado("PASSED")] * 8 + [_resultado("FAILED")] * 2
    incident_repository.count_by_source.return_value = 2

    reporte = servicio.generate_quality_report(1, date(2026, 11, 1), date(2026, 11, 30))

    assert reporte.total_validations == 10
    assert reporte.compliance_pct == 80.0
    assert reporte.incidents_count == 2
    assert (reporte.start, reporte.end) == (date(2026, 11, 1), date(2026, 11, 30))


def test_cp25_negativo_rango_invalido(servicio, metric_repository, incident_repository):
    with pytest.raises(InvalidDateRangeError):
        servicio.generate_quality_report(1, date(2026, 11, 30), date(2026, 11, 1))

    metric_repository.list_by_source.assert_not_called()
    incident_repository.count_by_source.assert_not_called()
