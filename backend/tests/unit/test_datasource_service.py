"""CP-07 a CP-10 · DataSourceService"""

from dataclasses import replace

import pytest

from app.core.exceptions import DuplicateNameError, NotFoundError
from app.domain.models import DataSourceCreateDTO, DataSourceUpdateDTO
from app.services.datasource_service import DataSourceService


@pytest.fixture
def servicio(source_repository, credential_cipher, connector_factory, scheduler):
    return DataSourceService(source_repository, credential_cipher, connector_factory, scheduler)


@pytest.fixture
def dto_fuente():
    return DataSourceCreateDTO(name="ERP Ventas", type="postgresql", host="10.0.0.5", port=5432,
                               database="ventas", username="lector", password="S3creta!")


# ---------------------------------------------------------------- CP-07 create_source
def test_cp07_positivo_registra_fuente_con_clave_cifrada(servicio, source_repository,
                                                         credential_cipher, dto_fuente):
    source_repository.get_by_name.return_value = None
    credential_cipher.encrypt.return_value = "gAAAA_cifrado"
    source_repository.add.side_effect = lambda s: replace(s, id=1)

    resultado = servicio.create_source(dto_fuente)

    assert resultado.id == 1
    assert resultado.name == "ERP Ventas"
    assert not hasattr(resultado, "password")
    assert not hasattr(resultado, "encrypted_password")
    credential_cipher.encrypt.assert_called_once_with("S3creta!")
    entidad = source_repository.add.call_args.args[0]
    assert entidad.encrypted_password == "gAAAA_cifrado"
    assert entidad.encrypted_password != "S3creta!"


def test_cp07_negativo_nombre_duplicado(servicio, source_repository, credential_cipher,
                                        dto_fuente, fuente_postgres):
    source_repository.get_by_name.return_value = fuente_postgres

    with pytest.raises(DuplicateNameError):
        servicio.create_source(dto_fuente)

    source_repository.add.assert_not_called()
    credential_cipher.encrypt.assert_not_called()


# ---------------------------------------------------------------- CP-08 test_connection
def test_cp08_positivo_conexion_exitosa(servicio, source_repository, credential_cipher,
                                        connector_factory, fuente_postgres):
    source_repository.get_by_id.return_value = fuente_postgres
    credential_cipher.decrypt.return_value = "S3creta!"
    conector = connector_factory.create.return_value
    conector.ping.return_value = True

    resultado = servicio.test_connection(1)

    assert resultado.status == "ok"
    conector.close.assert_called_once()
    assert fuente_postgres.last_connection_status == "ok"


def test_cp08_negativo_conexion_fallida(servicio, source_repository, credential_cipher,
                                        connector_factory, fuente_postgres):
    source_repository.get_by_id.return_value = fuente_postgres
    credential_cipher.decrypt.return_value = "S3creta!"
    conector = connector_factory.create.return_value
    conector.ping.side_effect = ConnectionError("timeout con lector:S3creta!@10.0.0.5")

    resultado = servicio.test_connection(1)

    assert resultado.status == "failed"
    assert "No fue posible conectar" in resultado.message
    assert "S3creta!" not in resultado.message
    conector.close.assert_called_once()


# ---------------------------------------------------------------- CP-09 update_source
def test_cp09_positivo_actualiza_con_nueva_contrasena(servicio, source_repository,
                                                      credential_cipher, fuente_postgres):
    source_repository.get_by_id.return_value = fuente_postgres
    source_repository.update.side_effect = lambda s: s
    credential_cipher.encrypt.return_value = "gAAAA_nuevo"

    resultado = servicio.update_source(1, DataSourceUpdateDTO(port=5433, password="Nueva#2026"))

    assert resultado.port == 5433
    credential_cipher.encrypt.assert_called_once_with("Nueva#2026")
    assert fuente_postgres.encrypted_password == "gAAAA_nuevo"


def test_cp09_positivo_actualiza_sin_contrasena(servicio, source_repository,
                                                credential_cipher, fuente_postgres):
    source_repository.get_by_id.return_value = fuente_postgres
    source_repository.update.side_effect = lambda s: s

    resultado = servicio.update_source(1, DataSourceUpdateDTO(host="10.0.0.8"))

    assert resultado.host == "10.0.0.8"
    credential_cipher.encrypt.assert_not_called()
    assert fuente_postgres.encrypted_password == "gAAAA_cifrado"


# ---------------------------------------------------------------- CP-10 delete_source
def test_cp10_positivo_elimina_fuente(servicio, source_repository, scheduler, fuente_postgres):
    source_repository.get_by_id.return_value = fuente_postgres

    resultado = servicio.delete_source(1)

    assert resultado is True
    scheduler.unschedule_source.assert_called_once_with(1)
    source_repository.delete.assert_called_once_with(1)


def test_cp10_negativo_fuente_inexistente(servicio, source_repository, scheduler):
    source_repository.get_by_id.return_value = None

    with pytest.raises(NotFoundError):
        servicio.delete_source(99)

    scheduler.unschedule_source.assert_not_called()
    source_repository.delete.assert_not_called()
