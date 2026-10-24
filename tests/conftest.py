"""Fixtures comunes de las pruebas."""

import pytest

from src.config import Settings

OBLIGATORIAS = {
    "REALTIX_ANTHROPIC_API_KEY": "clave-de-prueba-anthropic",
    "OPENAI_API_KEY": "clave-de-prueba-openai",
    "DATABASE_URL": "postgresql://usuario:clave@localhost:5432/pruebas",
    "OVT_HMAC_SECRET": "secreto-de-prueba",
    "TOKEN_FUNCIONARIO": "token-funcionario-de-prueba",
    "TOKEN_ADMIN": "token-admin-de-prueba",
}


@pytest.fixture
def entorno_limpio(monkeypatch: pytest.MonkeyPatch) -> pytest.MonkeyPatch:
    """Quita del entorno toda variable que lea `Settings`, para no depender de la máquina."""
    for nombre in Settings.model_fields:
        monkeypatch.delenv(nombre.upper(), raising=False)
    return monkeypatch


@pytest.fixture
def entorno_valido(entorno_limpio: pytest.MonkeyPatch) -> pytest.MonkeyPatch:
    """Entorno con todas las variables obligatorias y valores ficticios."""
    for nombre, valor in OBLIGATORIAS.items():
        entorno_limpio.setenv(nombre, valor)
    return entorno_limpio
