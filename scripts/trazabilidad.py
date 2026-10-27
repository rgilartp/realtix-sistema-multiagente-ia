"""Matriz de trazabilidad: cruza los 65 requerimientos con sus pruebas, escenarios y resultados.

Recolecta las marcas `@pytest.mark.req(...)` sin ejecutar las pruebas, las anotaciones de la web y
la lista `rf` de cada escenario, y escribe `reports/trazabilidad.md` y `.csv` (sección 6.11). Con
`--junit` (salida de `pytest --junitxml`) y `--resultados` (`calificados.jsonl` de una corrida),
califica cada requerimiento: 100 si pasan todas sus evidencias, 80 si pasan con una limitación
documentada en `--observaciones` (YAML: ID -> limitación) y 0 si falla alguna. Sin resultados, queda
«sin calificar». El cumplimiento global es el promedio de los calificados.

Uso: uv run python scripts/trazabilidad.py [rutas de pruebas] [--salida reports]
     [--junit junit.xml] [--resultados reports/corrida-3/calificados.jsonl] [--observaciones f.yaml]
"""

import argparse
import csv
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
import yaml

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))


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


# Pruebas de la web (Playwright, B11): cada flujo de `web/tests/*.spec.js` declara su nombre y
# sus requerimientos (`nombre: "…", flujo: …, req: ["RF-… · nombre corto", …]`), que la prueba
# lleva como anotación `req`.
FLUJO_WEB = re.compile(r'nombre:\s*"([^"]+)",\s*flujo:\s*\w+,\s*req:\s*\[([^\]]*)\]')
TEXTO = re.compile(r'"([^"]+)"')


def recolectar_web(raiz: Path = RAIZ / "web" / "tests") -> list[Evidencia]:
    """Evidencias de las pruebas de la web, leídas de sus anotaciones `req`."""
    evidencias = []
    for archivo in sorted(raiz.glob("*.spec.js")):
        ruta = archivo.relative_to(RAIZ).as_posix()
        for nombre, lista in FLUJO_WEB.findall(archivo.read_text(encoding="utf-8")):
            evidencias += [Evidencia(r, f"{ruta}::{nombre}") for r in TEXTO.findall(lista)]
    return evidencias


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


# -- Matriz completa (B12) -------------------------------------------------------------------

FILA_ANEXO = re.compile(r"^\| ((?:RF-[A-Z]+-\d{2})|(?:RNF-\d{2})) · ([^|]+?) \|", re.MULTILINE)
ID_DEL_REQUERIMIENTO = re.compile(r"^((?:RF-[A-Z]+-\d{2})|(?:RNF-\d{2}))")


def requerimientos_del_anexo(
    ruta: Path = RAIZ / "docs" / "ESPECIFICACION_TECNICA.md",
) -> dict[str, str]:
    """ID -> nombre corto, de la tabla del Anexo A."""
    texto = ruta.read_text(encoding="utf-8")
    anexo = texto[texto.index("## Anexo A") :]
    return {i: n.strip() for i, n in FILA_ANEXO.findall(anexo)}


def id_de(requerimiento: str) -> str:
    encontrado = ID_DEL_REQUERIMIENTO.match(requerimiento)
    return encontrado.group(1) if encontrado else requerimiento


def resultados_junit(ruta: Path) -> dict[str, bool]:
    """Prueba (`ruta::nombre`) -> pasó, de un reporte JUnit de pytest."""
    salida: dict[str, bool] = {}
    for caso in ET.parse(ruta).getroot().iter("testcase"):
        clase = caso.get("classname", "")
        partes = clase.split(".")
        modulo = [p for p in partes if not p[:1].isupper()]
        clases = [p for p in partes if p[:1].isupper()]
        nodo = "/".join(modulo) + ".py::" + "::".join([*clases, caso.get("name", "")])
        fallo = any(caso.find(t) is not None for t in ("failure", "error"))
        if caso.find("skipped") is None:
            salida[nodo] = not fallo
    return salida


def resultados_de_escenarios(ruta: Path) -> dict[str, bool]:
    """Escenario -> superado en todos sus ensayos, de `calificados.jsonl`."""
    por_escenario: dict[str, bool] = {}
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        if linea.strip():
            c = json.loads(linea)
            por_escenario[c["escenario"]] = (
                por_escenario.get(c["escenario"], True) and c["superado"]
            )
    return por_escenario


def calificacion(resultados: list[bool | None], observacion: str | None) -> int | None:
    conocidos = [r for r in resultados if r is not None]
    if not conocidos:
        return None
    if not all(conocidos):
        return 0
    return 80 if observacion else 100


def matriz_completa(
    evidencias: list[Evidencia],
    escenarios: list[dict[str, Any]],
    pruebas_ok: dict[str, bool] | None = None,
    escenarios_ok: dict[str, bool] | None = None,
    observaciones: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Una fila por requerimiento del Anexo A, con sus evidencias y su calificación."""
    pruebas_ok, escenarios_ok, observaciones = (
        pruebas_ok or {},
        escenarios_ok or {},
        observaciones or {},
    )
    pruebas = agrupar([Evidencia(id_de(e.requerimiento), e.prueba) for e in evidencias])
    filas = []
    for id_, nombre in requerimientos_del_anexo().items():
        suyos = [e for e in escenarios if id_ in e.get("rf", [])]
        resultados = [pruebas_ok.get(p) for p in pruebas.get(id_, [])]
        resultados += [escenarios_ok.get(e["id"]) for e in suyos]
        superados = [e["id"] for e in suyos if escenarios_ok.get(e["id"])]
        caso = suyos[0]["dado_cuando_entonces"] if suyos else None
        filas.append(
            {
                "requerimiento": f"{id_} · {nombre}",
                "pruebas": pruebas.get(id_, []),
                "escenarios": [e["id"] for e in suyos],
                "caso": caso,
                "obtenido": (
                    f"{len(superados)} de {len(suyos)} escenarios superados"
                    if suyos and escenarios_ok
                    else None
                ),
                "observacion": observaciones.get(id_),
                "calificacion": calificacion(resultados, observaciones.get(id_)),
            }
        )
    return filas


def escribir_completa(filas: list[dict[str, Any]], salida: Path) -> tuple[Path, Path]:
    """La matriz como manual de pruebas, en Markdown y en CSV."""
    salida.mkdir(parents=True, exist_ok=True)
    calificadas = [f["calificacion"] for f in filas if f["calificacion"] is not None]
    global_ = f"{sum(calificadas) / len(calificadas):.1f} %" if calificadas else "sin calificar"
    lineas = [
        "# Matriz de trazabilidad",
        "",
        "Generada por `scripts/trazabilidad.py`; no se edita a mano. Calificación: 100 (pasan "
        "todas sus evidencias), 80 (pasan con una limitación documentada) o 0 (falla alguna).",
        "",
        f"Cumplimiento global: {global_.replace('.', ',')} ({len(calificadas)} de {len(filas)} "
        "requerimientos calificados).",
        "",
        "| Requerimiento | Caso (dado, cuando, entonces) | Obtenido | Evidencias | Calificación |",
        "|---|---|---|---|---|",
    ]
    for f in filas:
        caso = f["caso"]
        texto_caso = (
            f"Dado: {caso['dado']}. Cuando: {caso['cuando']}. Entonces: {caso['entonces']}"
            if caso
            else "—"
        )
        evidencias = [f"`{p}`" for p in f["pruebas"]] + [f"escenario {e}" for e in f["escenarios"]]
        nota = f" ({f['observacion']})" if f["observacion"] else ""
        valor = "sin calificar" if f["calificacion"] is None else f"{f['calificacion']} %{nota}"
        lineas.append(
            "| "
            + " | ".join(
                str(c).replace("|", "\\|").replace("\n", " ")
                for c in (
                    f["requerimiento"],
                    texto_caso,
                    f["obtenido"] or "—",
                    "<br>".join(evidencias) or "—",
                    valor,
                )
            )
            + " |"
        )
    ruta_md = salida / "trazabilidad.md"
    ruta_csv = salida / "trazabilidad.csv"
    ruta_md.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    with ruta_csv.open("w", newline="", encoding="utf-8") as archivo:
        escritor = csv.writer(archivo)
        escritor.writerow(["requerimiento", "tipo", "evidencia", "calificacion"])
        for f in filas:
            valor = "" if f["calificacion"] is None else f["calificacion"]
            for p in f["pruebas"]:
                escritor.writerow([f["requerimiento"], "prueba", p, valor])
            for e in f["escenarios"]:
                escritor.writerow([f["requerimiento"], "escenario", e, valor])
            if not f["pruebas"] and not f["escenarios"]:
                escritor.writerow([f["requerimiento"], "", "", valor])
    return ruta_md, ruta_csv


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("rutas", nargs="*", default=["tests"])
    parser.add_argument("--salida", type=Path, default=Path("reports"))
    parser.add_argument("--junit", type=Path, help="reporte JUnit de pytest")
    parser.add_argument("--resultados", type=Path, help="calificados.jsonl de una corrida")
    parser.add_argument("--observaciones", type=Path, help="YAML: ID -> limitación documentada")
    args = parser.parse_args(argv)

    from src.evaluacion.escenarios import cargar_escenarios

    evidencias = recolectar(args.rutas)
    if args.rutas == ["tests"]:  # la matriz completa suma las pruebas de la web
        evidencias += recolectar_web()
    filas = matriz_completa(
        evidencias,
        cargar_escenarios(),
        resultados_junit(args.junit) if args.junit else None,
        resultados_de_escenarios(args.resultados) if args.resultados else None,
        yaml.safe_load(args.observaciones.read_text(encoding="utf-8"))
        if args.observaciones
        else None,
    )
    ruta_md, ruta_csv = escribir_completa(filas, args.salida)
    con_evidencia = len(agrupar(evidencias))
    print(f"{con_evidencia} requerimientos con evidencia; matriz en {ruta_md} y {ruta_csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
