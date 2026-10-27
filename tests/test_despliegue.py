"""Reglas del despliegue de B13 que no deben perderse: se revisan los archivos, sin Docker."""

import re
from pathlib import Path

import pytest
import yaml

RAIZ = Path(__file__).resolve().parents[1]
COMPOSE = yaml.safe_load((RAIZ / "docker-compose.yml").read_text(encoding="utf-8"))
SERVICIOS = COMPOSE["services"]


@pytest.mark.unit
@pytest.mark.req("RNF-12 · Imágenes de contenedor", "RNF-03 · Protección de datos personales")
def test_la_imagen_no_trae_el_env_ni_bases_y_corre_sin_privilegios() -> None:
    ignorados = (RAIZ / ".dockerignore").read_text(encoding="utf-8").split()
    assert {".env", ".env.*", "!.env.example", "**/*.db", "*.pem"} <= set(ignorados)
    dockerfile = (RAIZ / "Dockerfile").read_text(encoding="utf-8")
    assert dockerfile.count("FROM ") >= 3  # uv, construcción y ejecución
    assert "USER realtix" in dockerfile and "HEALTHCHECK" in dockerfile
    assert "get_encoding('cl100k_base')" in dockerfile  # tiktoken descargado en la imagen
    assert "--no-dev" in dockerfile and ".env" not in re.findall(r"COPY\s+(\S+)", dockerfile)


@pytest.mark.unit
@pytest.mark.req("RNF-13 · Orquestación con Compose", "RNF-02 · Escalamiento horizontal")
def test_compose_levanta_todo_y_permite_replicas() -> None:
    assert {"proxy", "backend", "chromadb", "postgres", "generar-realsit"} <= set(SERVICIOS)
    backend = SERVICIOS["backend"]
    assert "container_name" not in backend and "ports" not in backend  # --scale backend=2
    assert backend["depends_on"]["postgres"]["condition"] == "service_healthy"
    for servicio in ("postgres", "chromadb"):  # no se exponen fuera del host (sección 3.11)
        assert all(str(p).startswith("127.0.0.1:") for p in SERVICIOS[servicio]["ports"])


@pytest.mark.unit
@pytest.mark.req("RNF-15 · Volúmenes persistentes")
def test_volumenes_con_nombre_y_realsit_en_solo_lectura() -> None:
    assert {
        "postgres-data",
        "chroma-data",
        "caddy-data",
        "caddy-config",
        "datos-sinteticos",
    } <= set(COMPOSE["volumes"])
    assert "datos-sinteticos:/realsit:ro" in SERVICIOS["backend"]["volumes"]


@pytest.mark.unit
@pytest.mark.req("RNF-14 · Configuración por entorno", "RNF-06 · Horario de atención")
def test_secretos_solo_en_el_env_y_modo_de_evaluacion_apagado_por_defecto() -> None:
    servidor = (RAIZ / "deploy" / "servidor.env").read_text(encoding="utf-8")
    nombres = re.findall(r"^([A-Z_]+)=", servidor, flags=re.MULTILINE)
    assert nombres and not [n for n in nombres if re.search(r"KEY|SECRET|TOKEN|PASSWORD", n)]
    entorno = SERVICIOS["backend"]["environment"]
    assert entorno["MODO_EVALUACION"] == "${REALTIX_MODO_EVALUACION:-false}"
    assert entorno["FALLAS_INYECTABLES"] == "${REALTIX_MODO_EVALUACION:-false}"
    assert entorno["CHROMA_HOST"] == "chromadb" and "@postgres:5432/" in entorno["DATABASE_URL"]


@pytest.mark.unit
@pytest.mark.req("RF-UI-01 · Widget embebible", "RNF-03 · Protección de datos personales")
def test_caddy_https_limites_y_cabeceras() -> None:
    caddy = (RAIZ / "deploy" / "Caddyfile").read_text(encoding="utf-8")
    assert "{$DOMINIO} {" in caddy and "dynamic a" in caddy
    assert "max_size 6MB" in caddy and "max_size 64KB" in caddy
    [hsts] = re.findall(r'Strict-Transport-Security "([^"]+)"', caddy)
    assert hsts == "max-age=31536000"  # sin preload
    assert "fail_duration" not in caddy  # un cuerpo grande no debe apartar la réplica sana
    politicas = re.findall(r"Content-Security-Policy \"([^\"]+)\"", caddy)
    assert len(politicas) == 3 and all("script-src 'self'" in p for p in politicas)
    ancestros = {re.search(r"frame-ancestors ([^\"]+)$", p).group(1) for p in politicas}
    assert ancestros == {"'self'", "'none'", "https://{$DOMINIO}"}
    assert not any("unsafe-inline" in p for p in politicas)


@pytest.mark.unit
@pytest.mark.req("RNF-06 · Horario de atención")
def test_monitor_de_health_cada_15_minutos() -> None:
    flujo = yaml.safe_load(
        (RAIZ / ".github" / "workflows" / "monitor.yml").read_text(encoding="utf-8")
    )
    disparadores = flujo[True]  # PyYAML lee la clave «on» como True
    assert disparadores["schedule"] == [{"cron": "*/15 * * * *"}]
    assert "workflow_dispatch" in disparadores
