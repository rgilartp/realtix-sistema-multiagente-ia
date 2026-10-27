"""Muestra de calibración estratificada (R2), kappa (A6), componentes y reportes, sin red."""

import csv
import json
from pathlib import Path

import pytest

from src.evaluacion.calibracion import (
    COLUMNAS_EVALUADORES,
    calcular_kappa,
    elegir,
    exportar,
    exportar_para_evaluadores,
    importar_calificaciones,
)
from src.evaluacion.componentes import escenarios_de_agente, metricas_de_enrutamiento
from src.evaluacion.corrida import metricas_por_conjunto
from src.evaluacion.escenarios import cargar_escenarios
from src.evaluacion.reportes import guardar_reportes

RNF16 = "RNF-16 · Tasa de respuestas correctas"


def calificado(i: int, aprobado: bool, conjunto: str = "principal") -> dict:
    veredicto = "correcta" if aprobado else "incorrecta"
    return {
        "escenario": f"IPU-{i:02d}" if i <= 15 else f"ICA-{i - 15:02d}",
        "ensayo": 1,
        "id_conversacion": f"c{i}",
        "conjunto": conjunto,
        "grupo": "ipu",
        "tipo_latencia": "simple",
        "categoria_esperada": "ipu",
        "categoria": "ipu" if i % 4 else "general",
        "con_recuperacion": False,
        "codigo": {
            "pasa": aprobado,
            "verificaciones": [{"tipo": "x", "detalle": "d", "pasa": aprobado}],
        },
        "juez": {
            "veredicto": veredicto,
            "alucinacion": False,
            "cito_norma": True,
            "cita_sustenta": True,
            "cobertura_completa": aprobado,
            "claridad": 4,
            "justificacion": "j",
        },  # fmt: skip
        "superado": aprobado,
        "superado_estricto": aprobado,
        "turnos": [
            {
                "latencia_servidor_ms": 4000 + i,
                "latencia_cliente_ms": 4100 + i,
                "estado": "respondida",
            }
        ],
        "tokens_sistema": {"claude-haiku-5-5": {"entrada": 1000, "salida": 100}},
        "tokens_juez": {"claude-opus-5-5": {"entrada": 3000, "salida": 200}},
        "error": None,
    }


@pytest.mark.unit
@pytest.mark.req(RNF16)
def test_muestra_estratificada_mitad_y_mitad_y_repetible() -> None:
    calificados = [calificado(i, i % 3 != 0) for i in range(1, 26)]  # 17 aprobados, 8 no
    calificados += [calificado(i, False, "R4") for i in range(1, 5)]  # otro conjunto: no entra
    muestra = elegir(calificados, tamano=10)
    assert muestra == elegir(calificados, tamano=10)  # semilla fija
    assert sum(c["superado"] for c in muestra) == 5 and len(muestra) == 10
    assert all(c["conjunto"] == "principal" for c in muestra)
    completa = elegir(calificados, tamano=20)  # solo hay 8 no aprobados: se completa
    assert len(completa) == 20 and sum(not c["superado"] for c in completa) == 8


@pytest.mark.unit
@pytest.mark.req(RNF16)
def test_exporta_sin_el_veredicto_y_calcula_el_kappa(tmp_path: Path) -> None:
    escenarios = {e["id"]: e for e in cargar_escenarios()}
    muestra = [calificado(i, i % 2 == 0) for i in range(1, 7)]
    ensayos = {
        c["id_conversacion"]: {
            "turnos": [{"usuario": "¿Pregunta?", "respuesta": "Usuario de Prueba 03 respondió."}]
        }
        for c in muestra
    }
    ruta = exportar(muestra, ensayos, escenarios, tmp_path, "huella-123")
    texto = ruta.read_text(encoding="utf-8")
    assert "correcta" not in texto.split("\n")[0] and "Usuario de Prueba 03" not in texto
    assert (tmp_path / "huella_juez.txt").read_text().strip() == "huella-123"
    assert "veredicto" not in (tmp_path / "clave.json").read_text(encoding="utf-8")
    with ruta.open(encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    for fila, c in zip(filas, muestra, strict=True):
        v = "correcta" if c["superado"] else "incorrecta"
        fila.update(
            {col: (v if col.endswith("veredicto") else "no") for col in COLUMNAS_EVALUADORES}
        )
    filas[0]["dayanna_veredicto"] = "parcial"
    with ruta.open("w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=list(filas[0]))
        escritor.writeheader()
        escritor.writerows(filas)
    archivo_juez = tmp_path / "juez.jsonl"
    archivo_juez.write_text(
        "".join(
            json.dumps({"id_conversacion": c["id_conversacion"], "veredicto": c["juez"]}) + "\n"
            for c in muestra
        ),
        encoding="utf-8",
    )
    k = calcular_kappa(tmp_path, archivo_juez)
    assert k["juez_frente_al_consenso"]["binario"]["kappa"] == pytest.approx(1.0)
    assert k["entre_evaluadores"]["ponderado_3_niveles"]["kappa"] < 1.0
    assert k["muestra"] == 6


@pytest.mark.unit
@pytest.mark.req(RNF16)
def test_calcular_kappa_exige_la_muestra_completa(tmp_path: Path) -> None:
    escenarios = {e["id"]: e for e in cargar_escenarios()}
    muestra = [calificado(1, True)]
    exportar(
        muestra, {"c1": {"turnos": [{"usuario": "?", "respuesta": "r"}]}}, escenarios, tmp_path, "h"
    )
    with pytest.raises(ValueError, match="Faltan calificaciones"):
        calcular_kappa(tmp_path, tmp_path / "juez.jsonl")


@pytest.mark.unit
@pytest.mark.req(
    "RF-OBS-02 · Matriz de confusión de enrutamiento", "RF-OBS-03 · Métricas de precisión y tiempo"
)
def test_metricas_de_enrutamiento_de_componentes() -> None:
    filas = [{"esperada": "ipu", "predicha": "ipu"}] * 8 + [
        {"esperada": "ica", "predicha": "ipu"}
    ] * 2
    m = metricas_de_enrutamiento(filas)
    assert m["exactitud"] == pytest.approx(0.8) and m[
        "exactitud_clase_mayoritaria"
    ] == pytest.approx(0.8)
    assert m["matriz"]["ica"]["ipu"] == 2 and m["por_categoria"]["ipu"][
        "precision"
    ] == pytest.approx(0.8)
    assert m["kappa"] == pytest.approx(0.0)  # no supera al azar: la advertencia de Powers


@pytest.mark.unit
@pytest.mark.req("RF-OBS-05 · Ejecución repetible de pruebas")
def test_escenarios_de_agente_son_de_un_turno_y_responden() -> None:
    elegidos = escenarios_de_agente(cargar_escenarios())
    assert elegidos and all(len(e["turnos"]) == 1 for e in elegidos)
    assert {e["categoria_esperada"] for e in elegidos} <= {"ipu", "ica", "general"}
    assert not {e["id"] for e in elegidos} & {"ROB-02", "MULTI-01", "ACC-03", "AMB-01"}


@pytest.mark.unit
@pytest.mark.req(RNF16, "RF-OBS-02 · Matriz de confusión de enrutamiento")
def test_reportes_sin_fechas_y_con_conjuntos_aparte(tmp_path: Path) -> None:
    calificados = [calificado(i, i % 3 != 0) for i in range(1, 13)] + [calificado(1, True, "R4")]
    datos = {
        "commit_evaluado": "805f2ef",
        "huella_juez": "h",
        "conjuntos": metricas_por_conjunto(calificados),
        "costos": {"Total": "0.5"},
    }
    guardar_reportes(tmp_path, "corrida de prueba", datos, calificados)
    reporte = (tmp_path / "reporte.md").read_text(encoding="utf-8")
    assert "Commit evaluado: `805f2ef`" in reporte and "Huella del juez: `h`" in reporte
    datos_con_constancias = datos | {"constancias": "El modo de evaluación se apagó al terminar."}
    guardar_reportes(tmp_path / "con", "corrida de prueba", datos_con_constancias, calificados)
    con = (tmp_path / "con" / "reporte.md").read_text(encoding="utf-8")
    assert "## Constancias de la corrida" in con and "se apagó al terminar" in con
    assert "## Escenarios del nivel de sistema" in reporte and "## R4 · Seguridad" in reporte
    assert "Wilson" in reporte and "Estricta" in reporte
    assert (tmp_path / "matriz_confusion.png").exists() and (tmp_path / "latencias.png").exists()
    assert "IPU-03" in (tmp_path / "fallas.md").read_text(encoding="utf-8")
    import re

    for archivo in ("reporte.md", "fallas.md", "costos.md", "metricas.json"):
        assert not re.search(r"\d{4}-\d{2}-\d{2}", (tmp_path / archivo).read_text(encoding="utf-8"))
    assert b"CreationDate" not in (tmp_path / "matriz_confusion.png").read_bytes()
    # Con el análisis ya escrito, volver a generar no lo borra: el esqueleto va aparte.
    (tmp_path / "fallas.md").write_text("# Fallas\n\nAnálisis de la corrida.\n", encoding="utf-8")
    guardar_reportes(tmp_path, "corrida de prueba", datos, calificados)
    assert "Análisis" in (tmp_path / "fallas.md").read_text(encoding="utf-8")
    assert "IPU-03" in (tmp_path / "fallas_esqueleto.md").read_text(encoding="utf-8")


@pytest.mark.unit
@pytest.mark.req("RNF-05 · Registro auditable", "RNF-03 · Protección de datos personales")
def test_verificador_de_trazas_encuentra_documentos_y_nombres() -> None:
    from types import SimpleNamespace

    from src.evaluacion.trazas_eval import revisar_ejecuciones

    limpia = SimpleNamespace(
        id="1", name="nodo_ipu", inputs={"x": "[DOCUMENTO]"}, outputs={}, extra={}, error=None
    )
    con_cedula = SimpleNamespace(
        id="2", name="nodo_ipu", inputs={"x": "CC-1000000003"}, outputs={}, extra={}, error=None
    )
    con_puntos = SimpleNamespace(
        id="3", name="x", inputs={}, outputs={"y": "cédula 1.000.000.003"}, extra={}, error=None
    )
    con_nombre = SimpleNamespace(
        id="4", name="x", inputs={}, outputs={"y": "usuario de  prueba 03"}, extra={}, error=None
    )
    r = revisar_ejecuciones([limpia, con_cedula, con_puntos, con_nombre])
    assert r["ejecuciones_revisadas"] == 4 and r["con_identificadores"] == 3 and not r["pasa"]
    assert "1000000003" not in json.dumps(r)  # el reporte no copia el identificador
    assert revisar_ejecuciones([limpia])["pasa"] and not revisar_ejecuciones([])["pasa"]


@pytest.mark.unit
@pytest.mark.req("RF-OBS-05 · Ejecución repetible de pruebas")
def test_el_commit_evaluado_es_obligatorio_contra_el_despliegue_y_no_cambia(tmp_path: Path) -> None:
    from argparse import Namespace

    from scripts.evaluar import _commit_de_la_corrida

    def args(**kw: object) -> Namespace:
        return Namespace(**({"api": None, "commit": None, "solo_reporte": False} | kw))

    assert _commit_de_la_corrida(args(), tmp_path) is None  # local, sin commit
    with pytest.raises(SystemExit, match="Falta --commit"):
        _commit_de_la_corrida(args(api="https://x"), tmp_path)
    metricas = json.dumps({"commit_evaluado": "aaa"})
    (tmp_path / "metricas.json").write_text(metricas, encoding="utf-8")
    assert _commit_de_la_corrida(args(api="https://x", commit="aaa"), tmp_path) == "aaa"
    with pytest.raises(SystemExit, match="no de bbb"):
        _commit_de_la_corrida(args(api="https://x", commit="bbb"), tmp_path)
    assert _commit_de_la_corrida(args(solo_reporte=True), tmp_path) == "aaa"


@pytest.mark.unit
@pytest.mark.req(RNF16, "RNF-03 · Protección de datos personales")
def test_material_de_cada_evaluador_sin_veredicto_y_con_las_fuentes_del_juez(
    tmp_path: Path,
) -> None:
    """B15: un HTML de lectura por evaluador con las mismas fuentes que ve el juez v3,
    anonimizadas y sin su veredicto; una hoja con listas; y la importación a `muestra.csv`."""
    from openpyxl import load_workbook

    escenarios = {e["id"]: e for e in cargar_escenarios()}
    muestra = [calificado(i, i % 2 == 0) for i in range(1, 5)]
    turno = {
        "usuario": "¿Pregunta inventada?",
        "respuesta": "Respuesta de Usuario de Prueba 03.",
        "aviso_ia": "Aviso inventado.",
        "meta": {
            "contextos": ["Norma inventada, art. 1\nTexto inventado del fragmento."],
            "herramientas": [{"herramienta": "h", "resultado": {"saldo": "$1.234.000"}}],
            "notas": ["Nota inventada del sistema."],
        },
    }
    ensayos = {c["id_conversacion"]: {"turnos": [turno]} for c in muestra}
    exportar(muestra, ensayos, escenarios, tmp_path, "h")
    rutas = exportar_para_evaluadores(muestra, ensayos, escenarios, tmp_path)
    lectura = (tmp_path / "rodolfo" / "calibracion_rodolfo.html").read_text(encoding="utf-8")
    for esperado in ("M04", "Texto inventado del fragmento", "$1.234.000", "Nota inventada",
                     "Aviso inventado", "Respuesta de referencia", "Veredictos"):  # fmt: skip
        assert esperado in lectura
    for prohibido in ("Usuario de Prueba 03", "justificacion", "superado", "IPU-0"):
        assert prohibido not in lectura
    assert len(rutas) == 5
    clave = json.loads((tmp_path / "clave.json").read_text(encoding="utf-8"))
    assert clave["_reparto"] == {"aprobadas_por_el_juez": 2, "no_aprobadas_por_el_juez": 2}
    for persona in ("rodolfo", "dayanna", "consenso"):
        ruta = tmp_path / persona / f"calificaciones_{persona}.xlsx"
        libro = load_workbook(ruta)
        hoja = libro["Calificaciones"]
        assert len(hoja.data_validations.dataValidation) == 2
        for fila in range(2, 6):
            hoja.cell(fila, 2, "parcialmente correcta" if persona == "dayanna" else "correcta")
            hoja.cell(fila, 3, "no")
        libro.save(ruta)
    assert importar_calificaciones(tmp_path) == 4
    with (tmp_path / "muestra.csv").open(encoding="utf-8") as f:
        fila = next(csv.DictReader(f))
    assert (
        fila["dayanna_veredicto"] == "parcialmente correcta" and fila["rodolfo_alucinacion"] == "no"
    )


@pytest.mark.unit
@pytest.mark.req("RF-ESC-01 · Cálculo del nivel de confianza")
def test_la_propuesta_del_umbral_separa_los_escalamientos_de_superados_y_no_superados() -> None:
    """B15: con cada umbral candidato, cuántos turnos escalarían y de qué escenarios (toy data)."""
    import importlib.util

    from src.evaluacion.escenarios import RAIZ

    ruta = RAIZ / "scripts" / "proponer_umbral.py"
    especificacion = importlib.util.spec_from_file_location("proponer_umbral", ruta)
    assert especificacion and especificacion.loader
    modulo = importlib.util.module_from_spec(especificacion)
    especificacion.loader.exec_module(modulo)
    filas = [
        {"nivel": 0.62, "superado": False},
        {"nivel": 0.71, "superado": True},
        {"nivel": 0.90, "superado": True},
    ]
    por_umbral = {t["umbral"]: t for t in modulo.tabla(filas)}
    assert por_umbral[0.7] == {
        "umbral": 0.7,
        "escalarian": 1,
        "de_escenarios_superados": 0,
        "de_escenarios_no_superados": 1,
    }
    assert por_umbral[0.75]["de_escenarios_superados"] == 1
