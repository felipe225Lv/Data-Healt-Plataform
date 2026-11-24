"""Reporte básico del estado de calidad de una fuente en un periodo (RF-16)."""

from datetime import date

from app.core.exceptions import InvalidDateRangeError
from app.domain.models import QualityReport


class ReportService:
    def __init__(self, metric_repository, incident_repository):
        self.metrics = metric_repository
        self.incidents = incident_repository

    def generate_quality_report(self, source_id: int, start: date, end: date) -> QualityReport:
        if start > end:
            raise InvalidDateRangeError()
        results = self.metrics.list_by_source(source_id, start, end)
        total = len(results)
        passed = sum(1 for r in results if r.status == "PASSED")
        failed = sum(1 for r in results if r.status == "FAILED")
        return QualityReport(
            source_id=source_id,
            start=start,
            end=end,
            total_validations=total,
            passed=passed,
            failed=failed,
            compliance_pct=round(passed / total * 100, 2) if total else 0.0,
            incidents_count=self.incidents.count_by_source(source_id, start, end),
        )
