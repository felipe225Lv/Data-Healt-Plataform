"""CP-06 · PermissionChecker.has_permission()"""

import pytest

from app.core.permissions import PermissionChecker


@pytest.mark.parametrize("rol, accion", [
    ("ADMIN", "sources:create"),
    ("ADMIN", "users:create"),
    ("ANALISTA", "rules:create"),
    ("NEGOCIO", "dashboard:read"),
])
def test_cp06_positivo_permisos_concedidos(rol, accion):
    assert PermissionChecker.has_permission(rol, accion) is True


@pytest.mark.parametrize("rol, accion", [
    ("ANALISTA", "users:create"),
    ("NEGOCIO", "rules:create"),
    ("NEGOCIO", "sources:create"),
    ("INVITADO", "dashboard:read"),
])
def test_cp06_negativo_permisos_denegados(rol, accion):
    assert PermissionChecker.has_permission(rol, accion) is False
