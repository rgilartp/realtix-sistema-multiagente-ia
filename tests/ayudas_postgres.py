"""Ayudas de las pruebas que usan PostgreSQL: la URL y qué hacer si no responde."""

import os

import pytest

URL_POSTGRES_COMPOSE = "postgresql://realtix:realtix_dev@localhost:5432/realtix"  # .env.example


def url_postgres_pruebas() -> str:
    """Base de PostgreSQL de las pruebas: `DATABASE_URL_PRUEBAS` o la de Compose."""
    return os.environ.get("DATABASE_URL_PRUEBAS", URL_POSTGRES_COMPOSE)


def exigir_postgres(motivo: Exception) -> None:
    """PostgreSQL no responde: en la CI (`POSTGRES_OBLIGATORIO=1`) falla; en local se salta."""
    mensaje = f"PostgreSQL no responde ({type(motivo).__name__}): `docker compose up -d postgres`."
    if os.environ.get("POSTGRES_OBLIGATORIO") == "1":
        pytest.fail(mensaje, pytrace=False)
    pytest.skip(mensaje)
