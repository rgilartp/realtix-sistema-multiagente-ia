"""Pruebas del esqueleto de la matriz de trazabilidad (sección 6.11)."""

import csv
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.trazabilidad import Evidencia, agrupar, escribir

pytestmark = [pytest.mark.unit, pytest.mark.req("RNF-11 · Código versionado")]

RAIZ = Path(__file__).resolve().parents[1]


def test_agrupa_por_requerimiento_sin_duplicados() -> None:
    evidencias = [
        Evidencia("RF-AUT-02 · Restricción a predios propios", "tests/b.py::t"),
        Evidencia("RF-AUT-02 · Restricción a predios propios", "tests/a.py::t"),
        Evidencia("RF-AUT-02 · Restricción a predios propios", "tests/a.py::t"),
        Evidencia("RNF-14 · Configuración por entorno", "tests/c.py::t"),
    ]

    assert agrupar(evidencias) == {
        "RF-AUT-02 · Restricción a predios propios": ["tests/a.py::t", "tests/b.py::t"],
        "RNF-14 · Configuración por entorno": ["tests/c.py::t"],
    }


def test_escribe_markdown_y_csv(tmp_path: Path) -> None:
    ruta_md, ruta_csv = escribir(
        {"RNF-14 · Configuración por entorno": ["tests/c.py::t"]}, tmp_path
    )

    assert "| RNF-14 · Configuración por entorno | 1 | `tests/c.py::t` |" in ruta_md.read_text(
        encoding="utf-8"
    )
    with ruta_csv.open(encoding="utf-8") as archivo:
        assert list(csv.reader(archivo)) == [
            ["requerimiento", "prueba"],
            ["RNF-14 · Configuración por entorno", "tests/c.py::t"],
        ]


def test_recolecta_las_marcas_del_repositorio(tmp_path: Path) -> None:
    resultado = subprocess.run(
        [sys.executable, "scripts/trazabilidad.py", "tests/test_config.py", "--salida", tmp_path],
        cwd=RAIZ,
        capture_output=True,
        text=True,
        check=True,
    )

    assert "1 requerimientos con evidencia" in resultado.stdout
    assert "RNF-14 · Configuración por entorno" in (tmp_path / "trazabilidad.md").read_text(
        encoding="utf-8"
    )
