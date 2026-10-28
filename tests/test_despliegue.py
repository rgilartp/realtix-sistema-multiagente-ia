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
    assert {".env", ".env.*", "**/.env", "**/.env.*", "!.env.example", "**/*.db"} <= set(ignorados)
    assert {"**/*.pem", "**/*.key", "**/*.p12"} <= set(ignorados)  # también en subcarpetas
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
@pytest.mark.req("RF-UI-01 · Widget embebible", "RNF-12 · Imágenes de contenedor")
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
def test_monitor_de_health_cada_15_minutos_en_horario_habil() -> None:
    flujo = yaml.safe_load(
        (RAIZ / ".github" / "workflows" / "monitor.yml").read_text(encoding="utf-8")
    )
    disparadores = flujo[True]  # PyYAML lee la clave «on» como True
    # Lunes a viernes, de 13:00 a 21:45 UTC (8:00 a 16:45 en Bogotá): cabe en el plan gratuito.
    assert disparadores["schedule"] == [{"cron": "*/15 13-21 * * 1-5"}]
    assert "workflow_dispatch" in disparadores


@pytest.mark.unit
@pytest.mark.req("RNF-13 · Orquestación con Compose")
def test_los_scripts_de_despliegue_tienen_sintaxis_valida() -> None:
    import subprocess

    for script in sorted((RAIZ / "deploy").glob("*.sh")):
        resultado = subprocess.run(["bash", "-n", str(script)], capture_output=True, text=True)
        assert resultado.returncode == 0, (script.name, resultado.stderr)
    assert 'user: "0"' not in (RAIZ / "docker-compose.yml").read_text(encoding="utf-8")


def _paquetes_de_la_imagen() -> set[str]:
    """Lo que instala `uv sync --frozen --no-dev`: las dependencias principales del lock, con las
    indirectas y los extras, sin ningún grupo."""
    import tomllib

    paquetes = {p["name"]: p for p in tomllib.loads((RAIZ / "uv.lock").read_text())["package"]}
    pendientes = list(paquetes["realtix-sistema-multiagente-ia"]["dependencies"])
    vistos: set[str] = set()
    while pendientes:
        dependencia = pendientes.pop()
        paquete = paquetes[dependencia["name"]]
        for extra in dependencia.get("extra", []):
            pendientes += paquete.get("optional-dependencies", {}).get(extra, [])
        if dependencia["name"] not in vistos:
            vistos.add(dependencia["name"])
            pendientes += paquete.get("dependencies", [])
    return vistos


@pytest.mark.unit
@pytest.mark.req("RNF-13 · Orquestación con Compose", "RNF-12 · Imágenes de contenedor")
def test_chroma_sin_puerto_en_el_servidor_y_la_evaluacion_fuera_de_la_imagen() -> None:
    # ADR-26: los avisos de chromadb, ragas y diskcache no tienen versión corregida.
    servidor = (RAIZ / "deploy" / "compose.servidor.yml").read_text(encoding="utf-8")
    assert re.search(r"^  chromadb:\n    ports: !reset \[\]$", servidor, flags=re.MULTILINE)
    desplegar = (RAIZ / "deploy" / "desplegar.sh").read_text(encoding="utf-8")
    assert "-f docker-compose.yml -f deploy/compose.servidor.yml" in desplegar
    imagen = _paquetes_de_la_imagen()
    assert {"chromadb", "certifi", "psycopg-binary"} <= imagen  # el recorrido sigue extras
    assert not {"ragas", "diskcache"} & imagen
    dockerfile = (RAIZ / "Dockerfile").read_text(encoding="utf-8")
    assert "uv sync --frozen --no-dev" in dockerfile
    assert not re.search(r"--(all-groups|group|only-group)\b", dockerfile)


@pytest.mark.unit
@pytest.mark.req("RNF-13 · Orquestación con Compose")
def test_los_dos_archivos_de_compose_del_servidor_son_validos() -> None:
    import shutil
    import subprocess

    if shutil.which("docker") is None:
        pytest.skip("sin Docker")
    archivos = ["-f", "docker-compose.yml", "-f", "deploy/compose.servidor.yml"]
    entorno = ["--env-file", ".env.example", "--env-file", "deploy/servidor.env"]
    resultado = subprocess.run(  # -q: valida sin imprimir la configuración resuelta
        ["docker", "compose", *archivos, *entorno, "config", "-q"],
        cwd=RAIZ,
        capture_output=True,
        text=True,
    )
    assert resultado.returncode == 0, resultado.stderr
