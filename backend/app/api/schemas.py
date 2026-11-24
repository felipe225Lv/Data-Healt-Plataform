"""Esquemas de entrada de la API (validaciones de los DTO del Plan de Pruebas, caja negra)."""

import re
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
NAME_PATTERN = r"^[A-Za-zÁÉÍÓÚáéíóúÑñÜü ]+$"


class LoginIn(BaseModel):
    email: str = Field(max_length=100, pattern=EMAIL_PATTERN)
    password: str = Field(min_length=1)


class UserCreateIn(BaseModel):
    full_name: str = Field(min_length=3, max_length=80, pattern=NAME_PATTERN)
    email: str = Field(max_length=100, pattern=EMAIL_PATTERN)
    password: str = Field(min_length=8, max_length=64)
    role: Literal["ADMIN", "ANALISTA", "NEGOCIO"]

    @field_validator("password")
    @classmethod
    def password_compleja(cls, value: str) -> str:
        reglas = [r"[A-Z]", r"[a-z]", r"[0-9]", r"[@#$%&*!?]"]
        if not all(re.search(r, value) for r in reglas):
            raise ValueError(
                "La contraseña debe tener al menos una mayúscula, una minúscula, un número "
                "y un carácter especial (@#$%&*!?)"
            )
        return value


class UserUpdateIn(BaseModel):
    full_name: str | None = Field(default=None, min_length=3, max_length=80, pattern=NAME_PATTERN)
    role: Literal["ADMIN", "ANALISTA", "NEGOCIO"] | None = None


class SourceCreateIn(BaseModel):
    name: str = Field(min_length=3, max_length=100)
    type: Literal["postgresql", "mysql", "csv", "excel"]
    host: str | None = None
    port: int | None = Field(default=None, ge=1, le=65535)
    database: str | None = None
    username: str | None = None
    password: str | None = None

    @model_validator(mode="after")
    def datos_de_conexion(self):
        if self.type in ("postgresql", "mysql"):
            faltantes = [c for c in ("host", "database", "username", "password") if not getattr(self, c)]
            if faltantes:
                raise ValueError(f"Para {self.type} son obligatorios: {', '.join(faltantes)}")
        return self


class DatasetCreateIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    type: Literal["table", "file", "endpoint"]


class RuleCreateIn(BaseModel):
    rule_type: Literal["completeness", "uniqueness", "validity", "freshness", "volume"]
    column: str | None = None
    threshold: float = Field(ge=0, le=100)
    frequency_minutes: int = Field(ge=5, le=1440)
    min_value: float | None = None
    max_value: float | None = None


class IncidentCloseIn(BaseModel):
    action_taken: str = Field(min_length=10, max_length=500)


class ReportQuery(BaseModel):
    source_id: int
    start: date
    end: date
