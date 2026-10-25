"""Reglas de secretos: ajustes de Claude Code y .gitignore (RNF-14)."""

import json
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]

pytestmark = [pytest.mark.unit, pytest.mark.req("RNF-14 · Configuración por entorno")]


def _denegados() -> list[str]:
    ajustes = json.loads((RAIZ / ".claude" / "settings.json").read_text(encoding="utf-8"))
    return ajustes["permissions"]["deny"]


def _ignorado(ruta: str) -> bool:
    resultado = subprocess.run(
        ["git", "check-ignore", "--no-index", "-q", ruta],
        cwd=RAIZ,
        check=False,
    )
    return resultado.returncode == 0


@pytest.mark.parametrize("regla", ["Read(./.env)", "Read(~/.ssh/**)"])
def test_settings_niega_leer_secretos(regla: str) -> None:
    assert regla in _denegados()


@pytest.mark.parametrize(
    "regla",
    [
        "Bash(env)",
        "Bash(printenv)",
        "Bash(export -p)",
        "Bash(set)",
        "Bash(docker compose config)",
        "Bash(docker inspect*)",
        "Bash(docker exec * printenv*)",
        "Bash(gh repo edit*)",
        "Bash(gh api --method PATCH *)",
        "Bash(gh api --method PUT *)",
        "mcp__ide__getDiagnostics",
        "mcp__claude-vscode__getDiagnostics",
    ],
)
def test_settings_niega_mostrar_entorno_y_editar_repo(regla: str) -> None:
    assert regla in _denegados()


@pytest.mark.parametrize("ruta", [".env", "deploy/.env", "llave.pem", "llave.key", "llave.p12"])
def test_gitignore_ignora_secretos(ruta: str) -> None:
    assert _ignorado(ruta)


def test_gitignore_no_ignora_env_example() -> None:
    assert not _ignorado(".env.example")
