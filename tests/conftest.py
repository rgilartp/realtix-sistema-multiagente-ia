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


# -- Base sintética de RealSit (B3) ----------------------------------------------------------

SEMILLA = 42


@pytest.fixture(scope="session")
def datos_sinteticos():
    """Datos sintéticos con la semilla 42, generados una sola vez por sesión."""
    from src.data.generar.generate_synthetic_data import generar_datos

    return generar_datos(SEMILLA)


@pytest.fixture(scope="session")
def base_sintetica(tmp_path_factory: pytest.TempPathFactory, datos_sinteticos):
    """Ruta de la base SQLite generada con los datos anteriores."""
    from src.data.generar.generate_synthetic_data import poblar_base

    ruta = tmp_path_factory.mktemp("realsit") / "realsit_sintetico.db"
    poblar_base(ruta, datos_sinteticos)
    return ruta


@pytest.fixture(params=["sintetico", "memoria"])
def adaptador(request: pytest.FixtureRequest, base_sintetica, datos_sinteticos):
    """El contrato corre contra las dos implementaciones: SQLite sintética y en memoria."""
    from src.data.adapter import MockRealSitAdapter
    from src.data.memoria import RealSitEnMemoria

    if request.param == "sintetico":
        return MockRealSitAdapter(base_sintetica)
    return RealSitEnMemoria(datos_sinteticos)
