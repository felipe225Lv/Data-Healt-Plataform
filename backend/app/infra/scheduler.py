"""Programador de validaciones.

Guarda qué reglas deben ejecutarse y cada cuánto. En esta versión las
validaciones se lanzan desde la API (POST /rules/{id}/run); el registro de
tareas queda listo para conectarlo a Celery beat.
"""


class InMemoryScheduler:
    def __init__(self):
        self.jobs: dict[int, int] = {}
        self.unscheduled_sources: list[int] = []
        self.alert_retries: list[int] = []

    def schedule_rule(self, rule_id: int, frequency_minutes: int) -> None:
        self.jobs[rule_id] = frequency_minutes

    def reschedule_rule(self, rule_id: int, frequency_minutes: int) -> None:
        self.jobs[rule_id] = frequency_minutes

    def unschedule_source(self, source_id: int) -> None:
        self.unscheduled_sources.append(source_id)

    def retry_alert(self, incident_id: int) -> None:
        self.alert_retries.append(incident_id)
