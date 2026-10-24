"""Matriz de trazabilidad: cruza las pruebas marcadas con `req` y los requerimientos.

Esqueleto de B1: recolecta las marcas `@pytest.mark.req(...)` sin ejecutar las pruebas y escribe
`reports/trazabilidad.md` y `reports/trazabilidad.csv`. En B12 se suman los escenarios (su lista
`rf`), los resultados de las corridas y la calificación de cada requerimiento (sección 6.11).

Uso: uv run python scripts/trazabilidad.py [rutas de pruebas] [--salida reports]
"""

import argparse
import csv
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import pytest


@dataclass(frozen=True)
class Evidencia:
    """Una prueba automática que verifica un requerimiento."""

    requerimiento: str
    prueba: str


class _RecolectorDeMarcas:
    """Complemento de pytest que guarda las marcas `req` de cada prueba recolectada."""

    def __init__(self) -> None:
        self.evidencias: list[Evidencia] = []

    def pytest_collection_modifyitems(self, items: list[pytest.Item]) -> None:
        for item in items:
            for marca in item.iter_markers(name="req"):
                for requerimiento in marca.args:
                    self.evidencias.append(Evidencia(str(requerimiento), item.nodeid))


def recolectar(rutas: list[str]) -> list[Evidencia]:
    """Recolecta (sin ejecutar) las pruebas de `rutas` y devuelve sus evidencias."""
    recolector = _RecolectorDeMarcas()
    codigo = pytest.main(
        ["--collect-only", "-q", "-p", "no:cacheprovider", *rutas], plugins=[recolector]
    )
    if codigo not in (pytest.ExitCode.OK, pytest.ExitCode.NO_TESTS_COLLECTED):
        raise RuntimeError(f"pytest no pudo recolectar las pruebas (código {codigo})")
    return recolector.evidencias


def agrupar(evidencias: list[Evidencia]) -> dict[str, list[str]]:
    """Agrupa las pruebas por requerimiento, ordenadas."""
    por_requerimiento: dict[str, set[str]] = defaultdict(set)
    for evidencia in evidencias:
        por_requerimiento[evidencia.requerimiento].add(evidencia.prueba)
    return {req: sorted(pruebas) for req, pruebas in sorted(por_requerimiento.items())}


def escribir(matriz: dict[str, list[str]], salida: Path) -> tuple[Path, Path]:
    """Escribe la matriz en Markdown y en CSV dentro de `salida`."""
    salida.mkdir(parents=True, exist_ok=True)
    ruta_md = salida / "trazabilidad.md"
    ruta_csv = salida / "trazabilidad.csv"

    lineas = [
        "# Matriz de trazabilidad",
        "",
        "Pruebas automáticas marcadas con `req`. Los escenarios, los resultados y la calificación",
        "se agregan en B12.",
        "",
        "| Requerimiento | Pruebas | Evidencias |",
        "|---|---|---|",
    ]
    for requerimiento, pruebas in matriz.items():
        lista = "<br>".join(f"`{prueba}`" for prueba in pruebas)
        lineas.append(f"| {requerimiento} | {len(pruebas)} | {lista} |")
    ruta_md.write_text("\n".join(lineas) + "\n", encoding="utf-8")

    with ruta_csv.open("w", newline="", encoding="utf-8") as archivo:
        escritor = csv.writer(archivo)
        escritor.writerow(["requerimiento", "prueba"])
        for requerimiento, pruebas in matriz.items():
            for prueba in pruebas:
                escritor.writerow([requerimiento, prueba])
    return ruta_md, ruta_csv


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("rutas", nargs="*", default=["tests"])
    parser.add_argument("--salida", type=Path, default=Path("reports"))
    args = parser.parse_args(argv)

    matriz = agrupar(recolectar(args.rutas))
    ruta_md, ruta_csv = escribir(matriz, args.salida)
    print(f"{len(matriz)} requerimientos con evidencia; matriz en {ruta_md} y {ruta_csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
