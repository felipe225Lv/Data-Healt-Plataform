"""CP-02 a CP-05 · UserService"""

import pytest

from app.core.exceptions import BusinessRuleError, DuplicateEmailError, NotFoundError
from app.domain.models import User, UserCreateDTO, UserUpdateDTO
from app.services.user_service import UserService


def _usuario(user_id=10, role="ANALISTA", activo=True):
    return User(id=user_id, full_name="Laura Gómez", email="laura@pyme.co",
                password_hash="hash_bcrypt", role=role, is_active=activo)


@pytest.fixture
def servicio(user_repository, password_hasher):
    return UserService(user_repository, password_hasher)


@pytest.fixture
def dto_creacion():
    return UserCreateDTO(full_name="Laura Gómez", email="laura@pyme.co",
                         password="Clave#2026", role="ANALISTA")


# ---------------------------------------------------------------- CP-02 create_user
def test_cp02_positivo_crea_usuario_con_hash(servicio, user_repository, password_hasher, dto_creacion):
    user_repository.get_by_email.return_value = None
    password_hasher.hash.return_value = "hash_bcrypt"
    user_repository.add.side_effect = lambda u: User(**{**u.__dict__, "id": 10})

    resultado = servicio.create_user(dto_creacion)

    assert resultado.id == 10
    assert resultado.email == "laura@pyme.co"
    assert resultado.role == "ANALISTA"
    assert resultado.is_active is True
    assert not hasattr(resultado, "password")
    assert not hasattr(resultado, "password_hash")
    password_hasher.hash.assert_called_once_with("Clave#2026")
    entidad_enviada = user_repository.add.call_args.args[0]
    assert entidad_enviada.password_hash == "hash_bcrypt"


def test_cp02_negativo_correo_duplicado(servicio, user_repository, password_hasher, dto_creacion):
    user_repository.get_by_email.return_value = _usuario()

    with pytest.raises(DuplicateEmailError):
        servicio.create_user(dto_creacion)

    user_repository.add.assert_not_called()
    password_hasher.hash.assert_not_called()


# ---------------------------------------------------------------- CP-03 update_user
def test_cp03_positivo_actualiza_nombre_y_rol(servicio, user_repository):
    user_repository.get_by_id.return_value = _usuario()
    user_repository.update.side_effect = lambda u: u

    resultado = servicio.update_user(10, UserUpdateDTO(full_name="Laura Gómez Ríos", role="NEGOCIO"))

    assert resultado.full_name == "Laura Gómez Ríos"
    assert resultado.role == "NEGOCIO"
    assert resultado.email == "laura@pyme.co"
    user_repository.update.assert_called_once()


def test_cp03_negativo_usuario_inexistente(servicio, user_repository):
    user_repository.get_by_id.return_value = None

    with pytest.raises(NotFoundError):
        servicio.update_user(99, UserUpdateDTO(full_name="Nadie"))

    user_repository.update.assert_not_called()


# ---------------------------------------------------------------- CP-04 deactivate_user
def test_cp04_positivo_desactiva_otro_usuario(servicio, user_repository):
    usuario = _usuario()
    user_repository.get_by_id.return_value = usuario

    resultado = servicio.deactivate_user(user_id=10, requester_id=1)

    assert resultado is True
    assert usuario.is_active is False
    user_repository.update.assert_called_once_with(usuario)
    user_repository.delete.assert_not_called()


def test_cp04_negativo_autodesactivacion(servicio, user_repository):
    admin = _usuario(user_id=1, role="ADMIN")
    user_repository.get_by_id.return_value = admin

    with pytest.raises(BusinessRuleError, match="No puede desactivar su propia cuenta"):
        servicio.deactivate_user(user_id=1, requester_id=1)

    assert admin.is_active is True


# ---------------------------------------------------------------- CP-05 list_users
def test_cp05_positivo_listado_filtrado(servicio, user_repository):
    user_repository.list.return_value = [
        User(id=1, full_name="A", email="a@pyme.co", password_hash="h", role="ANALISTA"),
        User(id=2, full_name="B", email="b@pyme.co", password_hash="h", role="ANALISTA"),
    ]

    resultado = servicio.list_users(role="ANALISTA", only_active=True)

    assert len(resultado) == 2
    assert [u.email for u in resultado] == ["a@pyme.co", "b@pyme.co"]
    user_repository.list.assert_called_once_with(role="ANALISTA", is_active=True)
