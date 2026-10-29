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


@pytest.mark.unit
@pytest.mark.req("RF-OBS-05 · Ejecución repetible de pruebas")
def test_recolecta_los_requerimientos_de_las_pruebas_de_la_web() -> None:
    from scripts.trazabilidad import recolectar_web

    evidencias = recolectar_web()
    requerimientos = {e.requerimiento for e in evidencias}
    for esperado in ("RF-UI-01 · Widget embebible", "RF-UI-03 · Identificación del interlocutor",
                     "RF-UI-04 · Carga desde la conversación"):  # fmt: skip
        assert esperado in requerimientos
    assert all(e.prueba.startswith("web/tests/web.spec.js::") for e in evidencias)


@pytest.mark.unit
@pytest.mark.req("RF-OBS-05 · Ejecución repetible de pruebas")
def test_califica_con_100_80_y_0() -> None:
    from scripts.trazabilidad import calificacion

    assert calificacion([True, True], None) == 100
    assert calificacion([True, True, None], None) is None  # una evidencia no se ejecutó
    assert calificacion([True, False, None], None) == 0
    assert calificacion([True], "medido en un solo ensayo") == 80
    assert calificacion([True, False], None) == 0
    assert calificacion([None], None) is None


@pytest.mark.unit
@pytest.mark.req("RF-OBS-05 · Ejecución repetible de pruebas")
def test_matriz_completa_cruza_pruebas_escenarios_y_resultados(tmp_path: Path) -> None:
    from scripts.trazabilidad import (
        escribir_completa,
        matriz_completa,
        resultados_de_escenarios,
        resultados_junit,
    )

    junit = tmp_path / "junit.xml"
    junit.write_text(
        '<testsuites><testsuite><testcase classname="tests.test_a" name="test_x"/>'
        '<testcase classname="tests.test_a" name="test_y"><failure/></testcase>'
        "</testsuite></testsuites>",
        encoding="utf-8",
    )
    calificados = tmp_path / "calificados.jsonl"
    calificados.write_text(
        '{"escenario": "E-01", "superado": true}\n{"escenario": "E-01", "superado": true}\n',
        encoding="utf-8",
    )
    assert resultados_junit(junit) == {
        "tests/test_a.py::test_x": True,
        "tests/test_a.py::test_y": False,
    }
    escenario = {
        "id": "E-01",
        "rf": ["RF-AUT-02"],
        "dado_cuando_entonces": {"dado": "d", "cuando": "c", "entonces": "e"},
    }
    filas = matriz_completa(
        [
            Evidencia("RF-AUT-02 · Restricción a predios propios", "tests/test_a.py::test_x"),
            Evidencia("RNF-14 · Configuración por entorno", "tests/test_a.py::test_y"),
        ],
        [escenario],
        resultados_junit(junit),
        resultados_de_escenarios(calificados),
    )
    por_id = {f["requerimiento"].split(" ·")[0]: f for f in filas}
    assert len(filas) == 65
    assert por_id["RF-AUT-02"]["calificacion"] == 100
    assert por_id["RF-AUT-02"]["obtenido"] == "1 de 1 escenarios superados"
    assert por_id["RNF-14"]["calificacion"] == 0
    ruta_md, _ = escribir_completa(filas, tmp_path)
    assert "Cumplimiento global: 50,0 %" in ruta_md.read_text(encoding="utf-8")


@pytest.mark.unit
@pytest.mark.req("RF-OBS-05 · Ejecución repetible de pruebas")
def test_cada_flujo_de_la_web_pasa_si_pasan_todas_sus_variantes(tmp_path: Path) -> None:
    from scripts.trazabilidad import resultados_de_flujos, resultados_junit_web

    junit = tmp_path / "web.xml"
    junit.write_text(
        '<testsuites><testsuite name="a.spec.js">'
        '<testcase name="flujo A" classname="a.spec.js"/>'
        '<testcase name="flujo A (390 px)" classname="a.spec.js"/>'
        '<testcase name="flujo B" classname="a.spec.js"/>'
        '<testcase name="flujo B (390 px)" classname="a.spec.js"><failure/></testcase>'
        '<testcase name="flujo C" classname="a.spec.js"><skipped/></testcase>'
        '<testcase name="flujo AB" classname="a.spec.js"><failure/></testcase>'
        '<testcase name="flujo A (modo oscuro, 1280 px)" classname="a.spec.js"/>'
        '<testcase name="flujo C (RNF-07)" classname="a.spec.js"><failure/></testcase>'
        "</testsuite></testsuites>",
        encoding="utf-8",
    )
    web = resultados_junit_web(junit)
    assert web["web/tests/a.spec.js::flujo A (390 px)"] is True
    assert "web/tests/a.spec.js::flujo C" not in web  # omitida: sin resultado
    evidencias = [
        Evidencia("RF-UI-01 · Widget embebible", f"web/tests/a.spec.js::flujo {n}")
        for n in ("A", "B", "C")
    ]
    assert resultados_de_flujos(web, evidencias) == {
        "web/tests/a.spec.js::flujo A": True,  # «flujo AB» no es una variante de «flujo A»
        "web/tests/a.spec.js::flujo B": False,
    }  # «flujo C (RNF-07)» es otro flujo, no una variante de «flujo C»


@pytest.mark.unit
@pytest.mark.req("RF-OBS-05 · Ejecución repetible de pruebas")
def test_la_disponibilidad_es_evidencia_de_rnf_06(tmp_path: Path) -> None:
    from scripts.trazabilidad import (
        DISPONIBILIDAD,
        combinar,
        matriz_completa,
        resultado_de_disponibilidad,
    )

    def rnf_06(cumple: bool) -> int | None:
        ruta = tmp_path / "disponibilidad.json"
        ruta.write_text(f'{{"cumple_meta": {str(cumple).lower()}}}', encoding="utf-8")
        filas = matriz_completa([DISPONIBILIDAD], [], resultado_de_disponibilidad(ruta))
        return next(f for f in filas if f["requerimiento"].startswith("RNF-06"))["calificacion"]

    assert rnf_06(True) == 100
    assert rnf_06(False) == 0
    sin_resultado = matriz_completa([DISPONIBILIDAD], [], {})
    assert (
        next(f for f in sin_resultado if f["requerimiento"].startswith("RNF-06"))["calificacion"]
        is None
    )
    # Una prueba que aparece en dos reportes (la suite y la corrida con modelos reales) pasa solo
    # si pasa en los dos.
    assert combinar({"t::a": True, "t::b": True}, {"t::b": False, "t::c": True}) == {
        "t::a": True,
        "t::b": False,
        "t::c": True,
    }
