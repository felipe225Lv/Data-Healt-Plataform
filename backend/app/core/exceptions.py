"""Excepciones de negocio de Data Health Platform.

La API traduce cada una a un código HTTP (ver app/api/routes.py).
"""


class DomainError(Exception):
    """Error base de la lógica de negocio."""

    status_code = 400


class InvalidCredentialsError(DomainError):
    status_code = 401

    def __init__(self, message: str = "Credenciales inválidas"):
        super().__init__(message)


class AccountLockedError(DomainError):
    status_code = 423

    def __init__(self, message: str = "Cuenta bloqueada temporalmente"):
        super().__init__(message)


class NotFoundError(DomainError):
    status_code = 404


class DuplicateEmailError(DomainError):
    status_code = 409

    def __init__(self, message: str = "El correo ya está registrado"):
        super().__init__(message)


class DuplicateNameError(DomainError):
    status_code = 409


class BusinessRuleError(DomainError):
    status_code = 400


class InvalidRuleError(DomainError):
    status_code = 422


class ValidationError(DomainError):
    status_code = 422


class EmptyDatasetError(DomainError):
    status_code = 422

    def __init__(self, message: str = "El conjunto de datos está vacío"):
        super().__init__(message)


class IncidentAlreadyClosedError(DomainError):
    status_code = 409

    def __init__(self, message: str = "El incidente ya fue cerrado"):
        super().__init__(message)


class InvalidDateRangeError(DomainError):
    status_code = 422

    def __init__(self, message: str = "Rango de fechas inválido"):
        super().__init__(message)


class PermissionDeniedError(DomainError):
    status_code = 403

    def __init__(self, message: str = "Permisos insuficientes"):
        super().__init__(message)
