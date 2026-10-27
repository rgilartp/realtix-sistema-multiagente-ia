"""Propuesta del umbral de confianza con los datos de las corridas (B15, sección 8.16). Sin red.

Toma cada turno atendido por los agentes que pasó por la fórmula de la confianza: los respondidos y
las aclaraciones con un nivel menor de 1, y los que escalaron por «confianza insuficiente». Con cada
umbral candidato cuenta:

- los turnos que escalarían, y entre ellos los de un escenario superado (escalamientos de más: una
  respuesta aceptable que no llega al contribuyente) y los de uno no superado (escalamientos que
  evitan una respuesta mala);
- con el umbral actual, cuántos escalaron.

Los turnos con un nivel de 1 que no viene de la fórmula (aclaración, rechazo de acceso) y los que
escalaron por otro motivo no cuentan. Los pesos no cambian (ADR-17). El escalamiento de un escenario
superado solo se infiere: el juez calificó la respuesta que el contribuyente recibió.

Uso: uv run python scripts/proponer_umbral.py --corridas corrida-1,corrida-2 [--actual 0.7]
Escribe `reports/umbral/propuesta.json` y `reports/umbral/propuesta.md`.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.evaluacion.corrida import vigentes  # noqa: E402
from src.evaluacion.ejecutor import leer_resultados  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
CANDIDATOS = [round(0.50 + 0.025 * i, 3) for i in range(13)]  # 0,50 a 0,80


def turnos_con_formula(corrida: str) -> list[dict[str, Any]]:
    """(corrida, escenario, turno, nivel, superado) de los turnos que pasaron por la fórmula."""
    carpeta = RAIZ / "reports" / corrida
    superado = {
        (c["escenario"], c["ensayo"]): bool(c["superado"])
        for c in leer_resultados(carpeta / "calificados.jsonl")
        if c.get("conjunto") == "principal"
    }
    filas = []
    for ensayo in vigentes(leer_resultados(carpeta / "resultados.jsonl")):
        clave = (ensayo["escenario"], ensayo["ensayo"])
        if clave not in superado:
            continue
        for i, turno in enumerate(ensayo["turnos"], 1):
            meta = turno.get("meta") or {}
            nivel, motivo, estado = (
                meta.get("nivel_confianza"),
                meta.get("motivo_escalamiento"),
                turno.get("estado"),
            )
            por_confianza = estado == "escalada" and motivo == "confianza insuficiente"
            atendido = estado in ("respondida", "aclaracion") and nivel is not None and nivel < 1
            if nivel is None or not (por_confianza or atendido):
                continue
            filas.append(
                {
                    "corrida": corrida,
                    "escenario": ensayo["escenario"],
                    "turno": i,
                    "nivel": float(nivel),
                    "escalo": por_confianza,
                    "superado": superado[clave],
                }
            )
    return filas


def tabla(filas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    salida = []
    for umbral in CANDIDATOS:
        escalarian = [f for f in filas if f["nivel"] < umbral]
        salida.append(
            {
                "umbral": umbral,
                "escalarian": len(escalarian),
                "de_escenarios_superados": sum(f["superado"] for f in escalarian),
                "de_escenarios_no_superados": sum(not f["superado"] for f in escalarian),
            }
        )
    return salida


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--corridas", default="corrida-1,corrida-2")
    parser.add_argument("--actual", type=float, default=0.7)
    args = parser.parse_args()
    filas = [f for c in args.corridas.split(",") for f in turnos_con_formula(c.strip())]
    resultado = {
        "corridas": args.corridas.split(","),
        "umbral_actual": args.actual,
        "turnos_con_formula": len(filas),
        "escalaron_por_confianza": sum(f["escalo"] for f in filas),
        "niveles": sorted(round(f["nivel"], 3) for f in filas),
        "por_umbral": tabla(filas),
        "turnos": filas,
    }
    destino = RAIZ / "reports" / "umbral"
    destino.mkdir(parents=True, exist_ok=True)
    (destino / "propuesta.json").write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    lineas = [
        "| Umbral | Escalarían | De escenarios superados | De escenarios no superados |",
        "|---|---|---|---|",
    ]
    for t in resultado["por_umbral"]:
        actual = " (actual)" if abs(t["umbral"] - args.actual) < 1e-9 else ""
        lineas.append(
            f"| {t['umbral']:.3f}{actual} | {t['escalarian']} | {t['de_escenarios_superados']} | "
            f"{t['de_escenarios_no_superados']} |".replace(".", ",")
        )
    texto = (
        f"# Umbral de confianza: datos de {', '.join(resultado['corridas'])}\n\n"
        f"Turnos que pasaron por la fórmula: {len(filas)}; escalaron por confianza con el umbral "
        f"actual: {resultado['escalaron_por_confianza']}.\n\n" + "\n".join(lineas) + "\n"
    )
    (destino / "propuesta.md").write_text(texto, encoding="utf-8")
    print(texto)
    return 0


if __name__ == "__main__":
    sys.exit(main())
