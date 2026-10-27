"""Reportes de una corrida en `reports/corrida-N/` (sección 6.10), sin fechas ni horas.

`metricas.json`, `reporte.md`, `matriz_confusion.png`, `latencias.png`, `costos.md` y el esqueleto
de `fallas.md`, con una fila por ensayo no superado y las columnas de causa técnica y familia de
MAST por llenar (sección 6.6). Los conjuntos R1, R3 y R4 van en secciones aparte.
"""

import json
from pathlib import Path
from typing import Any

from src.agents.state import CATEGORIAS

BAHCECI = {
    "faithfulness": 0.9263,
    "answer_relevancy": 0.9131,
    "context_precision": 0.7520,
    "context_recall": 0.8660,
}
NOMBRES_RAGAS = {
    "context_precision": "Precisión del contexto",
    "context_recall": "Exhaustividad del contexto",
    "faithfulness": "Fidelidad",
    "answer_relevancy": "Relevancia de la respuesta",
}
TITULOS = {
    "principal": "Los 60 escenarios",
    "R1": "R1 · Generalización (variantes parafraseadas)",
    "R3": "R3 · Escenarios encadenados",
    "R4": "R4 · Seguridad",
}
SIN_FECHA = {"Date": None, "Software": None}  # las figuras no guardan cuándo se generaron


def _pct(x: float | None) -> str:
    return "—" if x is None else f"{x * 100:.1f} %".replace(".", ",")


def _num(x: float | None) -> str:
    return "—" if x is None else f"{x:.2f}".replace(".", ",")


def _ms(x: float | None) -> str:
    return "—" if x is None else f"{x:,.0f}".replace(",", ".")


def _intervalo(par: list[float] | None) -> str:
    return "—" if not par else f"{_pct(par[0])} a {_pct(par[1])}"


def _celda(texto: Any) -> str:
    return str(texto).replace("|", "\\|").replace("\n", " ")


def _fila(*celdas: Any) -> str:
    return "| " + " | ".join(_celda(c) for c in celdas) + " |"


def _encabezado(*titulos: str) -> list[str]:
    return [_fila(*titulos), "|" + "---|" * len(titulos)]


def _pyplot() -> Any:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def figura_matriz(matriz: dict[str, dict[str, int]], ruta: Path, titulo: str) -> None:
    plt = _pyplot()
    nombres = [*CATEGORIAS, "sin_categoria"]
    filas = [c for c in nombres if c in matriz]
    columnas = [c for c in nombres if any(matriz[f].get(c) for f in filas)] or filas
    datos = [[matriz[f].get(c, 0) for c in columnas] for f in filas]
    figura, eje = plt.subplots(figsize=(7, 5.5))
    imagen = eje.imshow(datos, cmap="Blues")
    eje.set_xticks(range(len(columnas)), columnas, rotation=30, ha="right")
    eje.set_yticks(range(len(filas)), filas)
    eje.set_xlabel("Categoría predicha")
    eje.set_ylabel("Categoría esperada")
    eje.set_title(titulo)
    maximo = max((max(f) for f in datos), default=0)
    for i, fila in enumerate(datos):
        for j, valor in enumerate(fila):
            color = "white" if maximo and valor > maximo / 2 else "black"
            eje.text(j, i, str(valor), ha="center", va="center", color=color)
    figura.colorbar(imagen, ax=eje)
    figura.tight_layout()
    figura.savefig(ruta, dpi=150, metadata=SIN_FECHA)
    plt.close(figura)


def figura_latencias(calificados: list[dict[str, Any]], ruta: Path) -> None:
    plt = _pyplot()
    series = {}
    for tipo, meta in (("simple", 8000), ("rag", 15000)):
        valores = [
            t["latencia_servidor_ms"]
            for c in calificados
            if c["tipo_latencia"] == tipo
            for t in c["turnos"]
            if t.get("latencia_servidor_ms")
        ]
        if valores:
            series[tipo] = (valores, meta)
    figura, eje = plt.subplots(figsize=(7, 4))
    if series:
        eje.boxplot([v for v, _ in series.values()], tick_labels=list(series))
        for i, (_, meta) in enumerate(series.values(), 1):
            eje.hlines(meta, i - 0.3, i + 0.3, colors="red", linestyles="dashed")
    eje.set_ylabel("Latencia del servidor (ms)")
    eje.set_title("Latencia por tipo de consulta (meta de RNF-01 en rojo)")
    figura.tight_layout()
    figura.savefig(ruta, dpi=150, metadata=SIN_FECHA)
    plt.close(figura)


def _seccion(nombre: str, m: dict[str, Any]) -> list[str]:
    titulo = f"## {TITULOS.get(nombre, nombre)}"
    if not m.get("ensayos"):
        return [titulo, "", "Sin ensayos.", ""]
    tm, te, j = m["tasa_meta"], m["tasa_estricta"], m["juez"]
    lineas = [titulo, "", f"{m['escenarios']} escenarios, {m['ensayos']} ensayos.", ""]
    lineas += _encabezado("Tasa", "Valor", "Wilson 95 % (n = escenarios)", "Bootstrap 95 %")
    for etiqueta, t in (("Meta (correcta o parcial, sin alucinación)", tm), ("Estricta", te)):
        lineas.append(
            _fila(
                etiqueta, _pct(t["tasa"]), _intervalo(t["wilson95"]), _intervalo(t["bootstrap95"])
            )
        )
    lineas.append("")
    c = m.get("consistencia_meta") or {}
    if c.get("k", 1) > 1:
        k = c["k"]
        lineas += [
            f"Consistencia: pass@1 {_pct(c['pass@1'])}, pass@{k} {_pct(c[f'pass@{k}'])} y "
            f"pass^{k} {_pct(c[f'pass^{k}'])}.",
            "",
        ]
    lineas += [
        f"Verificaciones de código superadas: {_pct(m['codigo_pasa'])}. Juez: {j['correcta']} "
        f"correctas, {j['parcialmente correcta']} parciales y {j['incorrecta']} incorrectas; "
        f"alucinación en {_pct(j['alucinacion'])}, cita en {_pct(j['cito_norma'])}, cita que "
        f"sustenta en {_pct(j['cita_sustenta'])}, cobertura completa en "
        f"{_pct(j['cobertura_completa'])} y claridad media de {_num(j['claridad_media'])}.",
        "",
    ]
    lineas += _encabezado(
        "Latencia", "Turnos", "p50 servidor", "p95 servidor", "p50 cliente", "p95 cliente",
        "Meta", "Bajo la meta",
    )  # fmt: skip
    for tipo, lat in m["latencia"].items():
        lineas.append(
            _fila(
                tipo,
                lat["turnos"],
                _ms(lat["servidor_p50_ms"]),
                _ms(lat["servidor_p95_ms"]),
                _ms(lat["cliente_p50_ms"]),
                _ms(lat["cliente_p95_ms"]),
                _ms(lat["meta_ms"]),
                lat["cumplen_meta"],
            )  # fmt: skip
        )
    return [*lineas, ""]


def _tabla_enrutamiento(titulo: str, metricas: dict[str, Any]) -> list[str]:
    lineas = [f"### {titulo}", ""]
    lineas += _encabezado("Categoría", "Soporte", "Precisión", "Exhaustividad", "F1")
    for cat, v in metricas["por_categoria"].items():
        if v["soporte"] or v["precision"] is not None:
            lineas.append(
                _fila(
                    cat, v["soporte"], _pct(v["precision"]), _pct(v["exhaustividad"]), _pct(v["f1"])
                )
            )
    return [*lineas, ""]


def reporte_md(corrida: str, datos: dict[str, Any]) -> str:
    lineas = [
        f"# Reporte de la {corrida}",
        "",
        "Generado por `scripts/evaluar.py` a partir de `resultados.jsonl` y `juez.jsonl`; no se "
        "edita a mano. Un escenario se supera si pasa todas las verificaciones de código y el juez "
        "lo califica correcta o parcialmente correcta, sin alucinación (sección 6.4). El intervalo "
        "de Wilson usa n = escenarios, porque los ensayos de un mismo escenario no son "
        "independientes (ADR-24).",
        "",
        f"Huella del juez: `{datos.get('huella_juez', '—')}`.",
        "",
    ]
    for nombre, m in datos["conjuntos"].items():
        lineas += _seccion(nombre, m)
    principal = datos["conjuntos"].get("principal") or {}
    if principal.get("ensayos"):
        lineas += ["## Enrutamiento", "", "![Matriz de confusión](matriz_confusion.png)", ""]
        lineas += _tabla_enrutamiento("Nivel de sistema (primer turno)", principal["enrutamiento"])
    comp = (datos.get("componentes") or {}).get("enrutamiento")
    if comp:
        lineas += _tabla_enrutamiento(
            f"Componentes ({comp['consultas']} consultas): exactitud {_pct(comp['exactitud'])}, "
            f"kappa {_num(comp['kappa'])}, clase mayoritaria "
            f"{_pct(comp['exactitud_clase_mayoritaria'])} y F1 macro {_pct(comp['f1_macro'])}",
            comp,
        )
    agentes = (datos.get("componentes") or {}).get("agentes")
    if agentes:
        lineas += [
            f"Agentes directo contra su nodo: {agentes['superados']} de {agentes['escenarios']} "
            f"correctos o parciales sin alucinación ({_pct(agentes['tasa'])}).",
            "",
        ]
    ragas = datos.get("ragas")
    if ragas:
        lineas += ["## RAGAS", "", f"{ragas['casos']} casos; evaluador `{ragas['modelo']}`.", ""]
        lineas += _encabezado("Métrica", "Promedio", "Bahçeci y colaboradores")
        for clave, nombre in NOMBRES_RAGAS.items():
            lineas.append(_fila(nombre, _pct(ragas["promedios"].get(clave)), _pct(BAHCECI[clave])))
        lineas.append("")
    trazas = datos.get("trazas")
    if trazas:
        lineas += [
            "## Trazas (RNF-05)",
            "",
            f"{trazas['ejecuciones_revisadas']} ejecuciones revisadas; "
            f"{trazas['con_identificadores']} con identificadores de los usuarios de prueba.",
            "",
        ]
    lineas += ["![Latencias](latencias.png)", ""]
    return "\n".join(lineas)


def fallas_md(corrida: str, calificados: list[dict[str, Any]]) -> str:
    lineas = [
        f"# Fallas de la {corrida}",
        "",
        "Esqueleto generado por `scripts/evaluar.py`: una fila por ensayo no superado. La causa "
        "técnica (enrutamiento, recuperación, prompt, datos, umbral o infraestructura) y la "
        "familia de MAST (diseño del sistema, desalineación entre agentes o verificación de la "
        "tarea) se "
        "llenan en el análisis (sección 6.6).",
        "",
        *_encabezado("Conjunto", "Escenario", "Ensayo", "Fallaron", "Juez", "Causa", "MAST"),
    ]
    for c in calificados:
        if c["superado"]:
            continue
        verificaciones = c["codigo"]["verificaciones"]
        fallidas = "; ".join(v["detalle"] for v in verificaciones if not v["pasa"])
        j = c["juez"]
        juez = "—"
        if j:
            juez = f"{j['veredicto']}{', alucinación' if j['alucinacion'] else ''}: "
            juez += j["justificacion"]
        lineas.append(
            _fila(
                c["conjunto"],
                c["escenario"],
                c["ensayo"],
                fallidas or c["error"] or "—",
                juez,
                "",
                "",
            )
        )
    return "\n".join(lineas) + "\n"


def costos_md(corrida: str, costos: dict[str, str]) -> str:
    lineas = [
        f"# Costos de la {corrida}",
        "",
        "Con los tokens reales y los precios de `src/integrations/costos.py` (ecuación 9).",
        "",
        *_encabezado("Concepto", "Costo (US$)"),
    ]
    lineas += [_fila(k, f"{float(v):.4f}".replace(".", ",")) for k, v in costos.items()]
    return "\n".join(lineas) + "\n"


def guardar_reportes(
    destino: Path, corrida: str, datos: dict[str, Any], calificados: list[dict[str, Any]]
) -> None:
    destino.mkdir(parents=True, exist_ok=True)
    texto = json.dumps(datos, ensure_ascii=False, indent=2) + "\n"
    (destino / "metricas.json").write_text(texto, encoding="utf-8")
    (destino / "reporte.md").write_text(reporte_md(corrida, datos), encoding="utf-8")
    (destino / "fallas.md").write_text(fallas_md(corrida, calificados), encoding="utf-8")
    (destino / "costos.md").write_text(
        costos_md(corrida, datos.get("costos", {})), encoding="utf-8"
    )
    principal = datos["conjuntos"].get("principal") or {}
    if principal.get("ensayos"):
        matriz = principal["enrutamiento"]["matriz"]
        figura_matriz(matriz, destino / "matriz_confusion.png", "Enrutamiento, nivel de sistema")
    comp = (datos.get("componentes") or {}).get("enrutamiento")
    if comp:
        figura_matriz(
            comp["matriz"],
            destino / "matriz_confusion_componentes.png",
            "Enrutamiento, componentes",
        )
    figura_latencias(calificados, destino / "latencias.png")
