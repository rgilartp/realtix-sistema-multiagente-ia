"""Presupuesto de las corridas 1 a 3 y de las mejoras R1 a R4 (ADR-24). Sin red.

Usa los precios oficiales de `src/integrations/costos.py` (comprobados en la página de cada
proveedor en octubre de 2026) y los costos unitarios medidos: el turno del sistema en B9 y en la
mini corrida (se toma el mayor, para no quedarse corto), la calificación del juez y el caso de
RAGAS en la mini corrida, y la clasificación del orquestador y la respuesta del agente en B7. Los
conteos de turnos salen de los escenarios. Escribe `reports/presupuesto.md`.

Uso: uv run python scripts/estimar_costos.py
"""

import json
import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.evaluacion.componentes import escenarios_de_agente  # noqa: E402
from src.evaluacion.escenarios import RAIZ, cargar_conjunto, cargar_escenarios  # noqa: E402
from src.integrations.costos import PRECIOS, PRESUPUESTO_USD, costo_usd  # noqa: E402

REPORTS = RAIZ / "reports"
# Gasto hasta B11 (docs/resumenes/b11.md) y de B12 antes de las corridas: dos validaciones del juez
# (A4), las pruebas de RAGAS con gpt-4o-mini y gpt-4.1-mini y su depuración, y la mini corrida.
GASTO_PREVIO = {"anthropic": Decimal("1.21"), "openai": Decimal("0.08")}
GASTO_B12 = {"anthropic": Decimal("0.21"), "openai": Decimal("0.08")}
RESERVA_CORRECCIONES = {"anthropic": Decimal("2.00"), "openai": Decimal("0.20")}
# B7 (reports/b07_humo.json): una llamada al orquestador y una respuesta de un agente con RAG.
ORQUESTADOR_B7 = costo_usd("claude-sonnet-5-5", 2199, 118)
AGENTE_B7 = costo_usd("claude-haiku-5-5", 21900, 1585)
TURNO_B9 = Decimal("0.0996762") / 12  # reports/b09_latencia.json: 12 turnos por la API


def _redondear(x: Decimal) -> Decimal:
    return x.quantize(Decimal("0.01"), ROUND_HALF_UP)


def _coma(x: Decimal) -> str:
    return str(x).replace(".", ",")


def unitarios() -> dict[str, Decimal]:
    mini = REPORTS / "mini-corrida"
    texto = (mini / "calificados.jsonl").read_text(encoding="utf-8")
    calificados = [json.loads(linea) for linea in texto.splitlines() if linea]
    turnos = sum(len(c["turnos"]) for c in calificados)
    metricas = json.loads((mini / "metricas.json").read_text())
    principal = metricas["conjuntos"]["principal"]["costo_usd"]
    ragas = metricas["ragas"]
    return {
        "turno": max(TURNO_B9, Decimal(principal["sistema"]) / turnos),
        "juez": Decimal(principal["juez"]) / len(calificados),
        "ragas_caso": Decimal(ragas["costo_usd"]) / ragas["casos"],
        "orquestador": ORQUESTADOR_B7,
        "agente": AGENTE_B7,
    }


def conteos() -> dict[str, int]:
    principales = cargar_escenarios()
    r3 = cargar_conjunto(["R3"])
    r4 = cargar_conjunto(["R4"])
    # RAGAS evalúa todo ensayo de un turno que recupere fragmentos, con sesión o sin ella; se
    # cuentan todos los de los agentes, aunque algunos respondan solo con datos del adaptador.
    un_turno_con_rag = [
        e for e in principales
        if len(e["turnos"]) == 1 and e["grupo"] in ("ipu", "ica", "general", "multiagente")
    ]  # fmt: skip
    return {
        "escenarios": len(principales),
        "turnos": sum(len(e["turnos"]) for e in principales),
        "r1": 10,
        "r3": len(r3),
        "turnos_r3": sum(len(e["turnos"]) for e in r3),
        "r4": len(r4),
        "turnos_r4": sum(len(e["turnos"]) for e in r4),
        "enrutamiento": 100,
        "agentes": len(escenarios_de_agente(principales)),
        "ragas_casos": len(un_turno_con_rag),
    }


def presupuesto() -> tuple[list[tuple[str, Decimal, Decimal]], dict[str, Decimal], dict[str, int]]:
    u, n = unitarios(), conteos()
    sistema = n["turnos"] * u["turno"] + n["escenarios"] * u["juez"]
    componentes = n["enrutamiento"] * u["orquestador"] + n["agentes"] * (u["agente"] + u["juez"])
    ragas = n["ragas_casos"] * u["ragas_caso"]
    r1 = 3 * n["r1"] * (u["turno"] + u["juez"])
    r3 = 5 * (n["turnos_r3"] * u["turno"] + n["r3"] * u["juez"])
    r4 = 5 * (n["turnos_r4"] * u["turno"] + n["r4"] * u["juez"])
    filas = [
        ("Gastado hasta B11", GASTO_PREVIO["anthropic"], GASTO_PREVIO["openai"]),
        ("B12: validación de evaluadores, pruebas de RAGAS y mini corrida", *GASTO_B12.values()),
        ("Corrida 1: 60 × 1 ensayo, juez y componentes", sistema + componentes, Decimal(0)),
        ("Corrida 2: 60 × 1 ensayo y juez", sistema, Decimal(0)),
        ("Corrida 3: 60 × 3, juez, componentes y RAGAS × 3", 3 * sistema + componentes, 3 * ragas),
        ("Reserva para las correcciones (escenarios afectados)", *RESERVA_CORRECCIONES.values()),
    ]  # fmt: skip
    mejoras = [
        (
            "R2 · muestra de 30 estratificada (usa los veredictos ya pagados)",
            Decimal(0),
            Decimal(0),
        ),
        ("R4 · 2 de seguridad, en las corridas 1 y 2 y × 3 en la 3", r4, Decimal(0)),
        ("R3 · 3 encadenados, en las corridas 1 y 2 y × 3 en la 3", r3, Decimal(0)),
        ("R1 · 10 variantes × 3 ensayos, solo en la corrida 3", r1, 3 * n["r1"] * u["ragas_caso"]),
    ]
    return filas + mejoras, u, n


def main() -> None:
    filas, u, n = presupuesto()
    base = filas[:6]
    sin_mejoras = [sum(f[i] for f in base) for i in (1, 2)]
    con_mejoras = [sum(f[i] for f in filas) for i in (1, 2)]
    lineas = [
        "# Presupuesto de las corridas (B12)",
        "",
        "Generado por `scripts/estimar_costos.py`. Precios oficiales en US$ por millón de tokens "
        "(entrada / salida), comprobados en octubre de 2026 en la página de cada proveedor:",
        "",
        *[f"- `{m}`: {_coma(p[0])} / {_coma(p[1])}" for m, p in PRECIOS.items()],
        "",
        "Costos unitarios medidos (se toma el mayor de B9 y de la mini corrida para el turno):",
        "",
        f"- turno del sistema: US${_coma(round(u['turno'], 4))}; calificación del juez: "
        f"US${_coma(round(u['juez'], 4))};",
        f"- caso de RAGAS (`gpt-4.1-mini` y embeddings): US${_coma(round(u['ragas_caso'], 4))};",
        f"- clasificación del orquestador: US${_coma(round(u['orquestador'], 4))}; respuesta de "
        f"un agente: US${_coma(round(u['agente'], 4))}.",
        "",
        f"Conteos: {n['escenarios']} escenarios con {n['turnos']} turnos; {n['enrutamiento']} "
        f"consultas de enrutamiento; {n['agentes']} escenarios de agente; unos {n['ragas_casos']} "
        f"casos de RAGAS por ensayo; R3 con {n['turnos_r3']} turnos y R4 con {n['turnos_r4']}.",
        "",
        "| Concepto | Anthropic (US$) | OpenAI (US$) |",
        "|---|---|---|",
    ]
    for i, (concepto, a, o) in enumerate(filas):
        lineas.append(f"| {concepto} | {_redondear(a)} | {_redondear(o)} |".replace(".", ","))
        if i == 5:
            lineas.append(
                f"| **Subtotal sin mejoras** | **{_redondear(sin_mejoras[0])}** | "
                f"**{_redondear(sin_mejoras[1])}** |".replace(".", ",")
            )
    total_a = f"{_coma(_redondear(con_mejoras[0]))} de {PRESUPUESTO_USD['anthropic']}"
    total_o = f"{_coma(_redondear(con_mejoras[1]))} de {PRESUPUESTO_USD['openai']}"
    lineas.append(f"| **Total con R1 a R4** | **{total_a}** | **{total_o}** |")
    margen = PRESUPUESTO_USD["anthropic"] - con_mejoras[0]
    caben = all(con_mejoras[i] <= PRESUPUESTO_USD[p] for i, p in ((0, "anthropic"), (1, "openai")))
    lineas += [
        "",
        f"Las cuatro mejoras {'caben' if caben else 'NO caben'}: margen de "
        f"US${_coma(_redondear(margen))} en Anthropic. Si una corrida real se acerca al tope, el "
        "orden de prioridad es R2, R4, R3 y R1. `scripts/evaluar.py --tope-usd` detiene una "
        "corrida que supere lo previsto.",
        "",
    ]
    salida = REPORTS / "presupuesto.md"
    salida.write_text("\n".join(lineas), encoding="utf-8")
    print("\n".join(lineas[-14:]))


if __name__ == "__main__":
    main()
