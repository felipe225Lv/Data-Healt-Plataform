"""CP-01 · AuthService.authenticate()"""

from datetime import datetime, timezone

import pytest
from freezegun import freeze_time

from app.core.exceptions import AccountLockedError, InvalidCredentialsError
from app.services.auth_service import AuthService


@pytest.fixture
def servicio(user_repository, password_hasher, token_provider, usuario_analista):
    user_repository.get_by_email.return_value = usuario_analista
    token_provider.create_access_token.return_value = "jwt.simulado"
    return AuthService(user_repository, password_hasher, token_provider)


def test_cp01_positivo_credenciales_validas(servicio, password_hasher, token_provider, usuario_analista):
    password_hasher.verify.return_value = True

    respuesta = servicio.authenticate("analista@pyme.co", "Clave#2026")

    assert respuesta.access_token == "jwt.simulado"
    assert respuesta.token_type == "bearer"
    assert usuario_analista.failed_attempts == 0
    token_provider.create_access_token.assert_called_once_with(subject=3, role="ANALISTA")


def test_cp01_negativo_contrasena_incorrecta(servicio, user_repository, password_hasher,
                                             token_provider, usuario_analista):
    password_hasher.verify.return_value = False

    with pytest.raises(InvalidCredentialsError):
        servicio.authenticate("analista@pyme.co", "ClaveErronea1!")

    assert usuario_analista.failed_attempts == 1
    user_repository.update.assert_called_once_with(usuario_analista)
    token_provider.create_access_token.assert_not_called()


@freeze_time("2026-11-01 10:00:00")
def test_cp01_negativo_bloqueo_tras_5_intentos(servicio, user_repository, password_hasher, usuario_analista):
    usuario_analista.failed_attempts = 4
    password_hasher.verify.return_value = False

    with pytest.raises(AccountLockedError):
        servicio.authenticate("analista@pyme.co", "ClaveErronea1!")

    assert usuario_analista.locked_until == datetime(2026, 11, 1, 10, 15, tzinfo=timezone.utc)
    user_repository.update.assert_called_once_with(usuario_analista)
