"""Prueba de humo de la configuración (RNF-14)."""

from datetime import time

import pytest

from src.config import ConfiguracionIncompletaError, cargar_configuracion
from src.container import Contenedor

pytestmark = [pytest.mark.unit, pytest.mark.req("RNF-14 · Configuración por entorno")]


def test_carga_con_las_obligatorias(entorno_valido: pytest.MonkeyPatch) -> None:
    settings = cargar_configuracion(env_file=None)

    assert settings.realtix_anthropic_api_key.get_secret_value() == "clave-de-prueba-anthropic"
    assert settings.modelo_orquestador == "claude-sonnet-5-5"
    assert settings.modelo_ipu == "claude-haiku-5-5"
    assert settings.modelo_juez == "claude-opus-5-5"
    assert settings.horario_inicio == time(8, 0)
    assert settings.horario_fin == time(17, 0)
    assert settings.modo_evaluacion is False
    assert settings.fallas_inyectables is False
    assert settings.tamano_maximo_archivo_mb == 5


def test_valores_iniciales_de_la_confianza(entorno_valido: pytest.MonkeyPatch) -> None:
    settings = cargar_configuracion(env_file=None)

    assert settings.umbral_confianza == 0.7
    assert (settings.peso_similitud, settings.peso_suficiencia, settings.peso_cobertura) == (
        0.4,
        0.4,
        0.2,
    )
    assert settings.max_reclasificaciones == 2


def test_falta_una_obligatoria_da_un_mensaje_claro(entorno_valido: pytest.MonkeyPatch) -> None:
    entorno_valido.delenv("REALTIX_ANTHROPIC_API_KEY")

    with pytest.raises(ConfiguracionIncompletaError) as error:
        cargar_configuracion(env_file=None)

    mensaje = str(error.value)
    assert "Faltan variables de entorno obligatorias: REALTIX_ANTHROPIC_API_KEY." in mensaje
    assert ".env.example" in mensaje


def test_sin_entorno_lista_todas_las_faltantes(entorno_limpio: pytest.MonkeyPatch) -> None:
    with pytest.raises(ConfiguracionIncompletaError) as error:
        cargar_configuracion(env_file=None)

    for nombre in ("OPENAI_API_KEY", "DATABASE_URL", "OVT_HMAC_SECRET", "TOKEN_ADMIN"):
        assert nombre in str(error.value)


def test_los_secretos_no_se_imprimen(entorno_valido: pytest.MonkeyPatch) -> None:
    settings = cargar_configuracion(env_file=None)

    assert "clave-de-prueba-anthropic" not in repr(settings)


def test_pesos_que_no_suman_uno_se_rechazan(entorno_valido: pytest.MonkeyPatch) -> None:
    entorno_valido.setenv("PESO_COBERTURA", "0.5")

    with pytest.raises(ConfiguracionIncompletaError, match="PESO_SIMILITUD"):
        cargar_configuracion(env_file=None)


def test_origenes_cors_separados_por_comas(entorno_valido: pytest.MonkeyPatch) -> None:
    entorno_valido.setenv("CORS_ORIGENES", "https://a.example, https://b.example")

    assert cargar_configuracion(env_file=None).cors_origenes == [
        "https://a.example",
        "https://b.example",
    ]


def test_el_contenedor_usa_la_configuracion_inyectada(entorno_valido: pytest.MonkeyPatch) -> None:
    settings = cargar_configuracion(env_file=None)

    assert Contenedor(settings).settings is settings
