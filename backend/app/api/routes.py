"""Endpoints de la API REST v1."""

from datetime import date

from fastapi import APIRouter, Depends, Header, Request

from app.api.schemas import (
    DatasetCreateIn,
    IncidentCloseIn,
    LoginIn,
    RuleCreateIn,
    SourceCreateIn,
    UserCreateIn,
    UserUpdateIn,
)
from app.core.exceptions import InvalidCredentialsError, NotFoundError, PermissionDeniedError
from app.core.permissions import has_permission
from app.domain.models import (
    DatasetCreateDTO,
    DataSourceCreateDTO,
    RuleCreateDTO,
    User,
    UserCreateDTO,
    UserOut,
    UserUpdateDTO,
)

router = APIRouter(prefix="/api/v1")


# ---------------------------------------------------------------- dependencias
def get_container(request: Request):
    return request.app.state.container


def current_user(authorization: str | None = Header(default=None), c=Depends(get_container)) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise InvalidCredentialsError("No autenticado")
    try:
        payload = c.tokens.decode(authorization.split(" ", 1)[1])
    except Exception as exc:
        raise InvalidCredentialsError("No autenticado") from exc
    user = c.users.get_by_id(int(payload["sub"]))
    if user is None or not user.is_active:
        raise InvalidCredentialsError("No autenticado")
    return user


def require(action: str):
    def checker(user: User = Depends(current_user)) -> User:
        if not has_permission(user.role, action):
            raise PermissionDeniedError()
        return user

    return checker


# ---------------------------------------------------------------- salud y autenticación
@router.get("/health")
def health():
    return {"status": "ok", "service": "data-health-platform"}


@router.post("/auth/login")
def login(body: LoginIn, c=Depends(get_container)):
    return c.auth_service.authenticate(body.email, body.password)


@router.get("/auth/me")
def me(user: User = Depends(current_user)):
    return UserOut.from_entity(user)


# ---------------------------------------------------------------- usuarios
@router.get("/users")
def list_users(role: str | None = None, only_active: bool = True,
               _: User = Depends(require("users:read")), c=Depends(get_container)):
    return c.user_service.list_users(role=role, only_active=only_active)


@router.post("/users", status_code=201)
def create_user(body: UserCreateIn, _: User = Depends(require("users:create")), c=Depends(get_container)):
    return c.user_service.create_user(UserCreateDTO(**body.model_dump()))


@router.patch("/users/{user_id}")
def update_user(user_id: int, body: UserUpdateIn,
                _: User = Depends(require("users:update")), c=Depends(get_container)):
    return c.user_service.update_user(user_id, UserUpdateDTO(**body.model_dump()))


@router.patch("/users/{user_id}/deactivate")
def deactivate_user(user_id: int, user: User = Depends(require("users:deactivate")),
                    c=Depends(get_container)):
    c.user_service.deactivate_user(user_id, requester_id=user.id)
    return {"id": user_id, "is_active": False}


# ---------------------------------------------------------------- fuentes y conjuntos
@router.get("/sources")
def list_sources(_: User = Depends(require("sources:read")), c=Depends(get_container)):
    return c.source_service.list_sources()


@router.post("/sources", status_code=201)
def create_source(body: SourceCreateIn, _: User = Depends(require("sources:create")), c=Depends(get_container)):
    return c.source_service.create_source(DataSourceCreateDTO(**body.model_dump()))


@router.post("/sources/{source_id}/test-connection")
def test_connection(source_id: int, _: User = Depends(require("sources:read")), c=Depends(get_container)):
    return c.source_service.test_connection(source_id)


@router.delete("/sources/{source_id}")
def delete_source(source_id: int, _: User = Depends(require("sources:delete")), c=Depends(get_container)):
    c.source_service.delete_source(source_id)
    return {"deleted": source_id}


@router.get("/sources/{source_id}/datasets")
def list_datasets(source_id: int, _: User = Depends(require("datasets:read")), c=Depends(get_container)):
    return c.dataset_service.list_by_source(source_id)


@router.post("/sources/{source_id}/datasets", status_code=201)
def create_dataset(source_id: int, body: DatasetCreateIn,
                   _: User = Depends(require("datasets:create")), c=Depends(get_container)):
    return c.dataset_service.register_dataset(source_id, DatasetCreateDTO(**body.model_dump()))


# ---------------------------------------------------------------- reglas y validaciones
@router.post("/datasets/{dataset_id}/rules", status_code=201)
def create_rule(dataset_id: int, body: RuleCreateIn,
                user: User = Depends(require("rules:create")), c=Depends(get_container)):
    return c.rule_service.create_rule(dataset_id, RuleCreateDTO(**body.model_dump()), user.id)


@router.get("/rules")
def list_rules(_: User = Depends(require("datasets:read")), c=Depends(get_container)):
    salida = []
    for rule in c.rules.all():
        last = c.metrics.last_by_rule(rule.id)
        salida.append({
            "id": rule.id, "dataset_id": rule.dataset_id, "rule_type": rule.rule_type,
            "column": rule.column, "threshold": rule.threshold, "frequency_minutes": rule.frequency_minutes,
            "last_value": last.value if last else None, "last_status": last.status if last else None,
        })
    return salida


@router.post("/rules/{rule_id}/run")
def run_rule(rule_id: int, _: User = Depends(require("rules:run")), c=Depends(get_container)):
    return c.runner.run_validation(rule_id)


# ---------------------------------------------------------------- incidentes, reportes y dashboard
@router.get("/incidents")
def list_incidents(status: str | None = None, _: User = Depends(require("incidents:read")),
                   c=Depends(get_container)):
    return c.incidents.list(status=status)


@router.patch("/incidents/{incident_id}/close")
def close_incident(incident_id: int, body: IncidentCloseIn,
                   user: User = Depends(require("incidents:close")), c=Depends(get_container)):
    return c.incident_service.close_incident(incident_id, body.action_taken, user.id)


@router.get("/reports")
def quality_report(source_id: int, start: date, end: date,
                   _: User = Depends(require("reports:read")), c=Depends(get_container)):
    if c.sources.get_by_id(source_id) is None:
        raise NotFoundError("Fuente no encontrada")
    return c.report_service.generate_quality_report(source_id, start, end)


@router.get("/dashboard/summary")
def dashboard_summary(_: User = Depends(require("dashboard:read")), c=Depends(get_container)):
    fuentes = []
    for source in c.sources.list():
        datasets = c.datasets.list_by_source(source.id)
        dataset_ids = {d.id for d in datasets}
        reglas = [r for r in c.rules.all() if r.dataset_id in dataset_ids]
        ultimos = [c.metrics.last_by_rule(r.id) for r in reglas]
        ultimos = [m for m in ultimos if m is not None and m.status != "ERROR"]
        cumplidas = sum(1 for m in ultimos if m.status == "PASSED")
        fuentes.append({
            "id": source.id,
            "name": source.name,
            "type": source.type,
            "datasets": len(datasets),
            "rules": len(reglas),
            "compliance_pct": round(cumplidas / len(ultimos) * 100, 2) if ultimos else None,
            "open_incidents": sum(
                1 for i in c.incidents.list(status="ABIERTO") if i.dataset_id in dataset_ids
            ),
        })
    return {
        "sources": fuentes,
        "open_incidents": len(c.incidents.list(status="ABIERTO")),
        "total_validations": len(c.metrics.items),
    }
