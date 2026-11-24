"""Matriz de permisos por rol (RF-09)."""

ADMIN = "ADMIN"
ANALISTA = "ANALISTA"
NEGOCIO = "NEGOCIO"
ROLES = (ADMIN, ANALISTA, NEGOCIO)

_PERMISOS: dict[str, frozenset[str]] = {
    ADMIN: frozenset(
        {
            "users:create", "users:read", "users:update", "users:deactivate",
            "sources:create", "sources:read", "sources:update", "sources:delete",
            "datasets:create", "datasets:read",
            "rules:create", "rules:update", "rules:run",
            "incidents:read", "incidents:close",
            "dashboard:read", "reports:read",
        }
    ),
    ANALISTA: frozenset(
        {
            "sources:read",
            "datasets:create", "datasets:read",
            "rules:create", "rules:update", "rules:run",
            "incidents:read", "incidents:close",
            "dashboard:read", "reports:read",
        }
    ),
    NEGOCIO: frozenset({"dashboard:read", "reports:read", "incidents:read"}),
}


class PermissionChecker:
    """Decide si un rol puede ejecutar una acción."""

    @staticmethod
    def has_permission(role: str, action: str) -> bool:
        return action in _PERMISOS.get(role, frozenset())


def has_permission(role: str, action: str) -> bool:
    return PermissionChecker.has_permission(role, action)
