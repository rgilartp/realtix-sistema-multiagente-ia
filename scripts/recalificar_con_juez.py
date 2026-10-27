"""Vuelve a calificar con el juez actual las respuestas guardadas de otras corridas (ADR-25).

Prueba contra el exceso de rigor del juez v3: no llama al sistema, solo al juez. Para cada corrida
de origen, guarda las calificaciones nuevas en `reports/<destino>/<origen>/juez.jsonl` y escribe en
`reports/<destino>/comparacion.md` qué escenarios cambian frente a la calificación guardada y qué
afirmaciones sin fuente listó el juez en cada uno. Gasta tokens del juez.

Uso:
  uv run python scripts/recalificar_con_juez.py --destino juez-v3-recalificacion \\
      --origen verif-fix-instrumento:CAD-03 --origen verif-fix-instrumento-2 \\
      --origen verif-fix-categoria-clasificada
(`origen:ID1,ID2` excluye esos escenarios.)
"""

import argparse
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import cargar_configuracion  # noqa: E402
from src.evaluacion.corrida import calificar, vigentes  # noqa: E402
from src.evaluacion.ejecutor import leer_resultados  # noqa: E402
from src.evaluacion.escenarios import cargar_conjunto  # noqa: E402
from src.evaluacion.juez import Juez, huella_del_juez  # noqa: E402
from src.integrations.costos import costo_usd  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent


def _resumen(juez: dict[str, Any] | None) -> str:
    if not juez:
        return "—"
    return f"{juez['veredicto']}{', alucinación' if juez['alucinacion'] else ''}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--destino", required=True)
    parser.add_argument("--origen", action="append", required=True)
    args = parser.parse_args()
    settings = cargar_configuracion()
    juez, huella = Juez(settings), huella_del_juez(settings)
    escenarios = {e["id"]: e for e in cargar_conjunto(["principal", "R3", "R4"])}
    destino = RAIZ / "reports" / args.destino
    filas, entrada, salida = [], 0, 0
    for origen in args.origen:
        nombre, _, excluidos = origen.partition(":")
        fuera = set(filter(None, excluidos.split(",")))
        ensayos = [
            e
            for e in vigentes(leer_resultados(RAIZ / "reports" / nombre / "resultados.jsonl"))
            if e["escenario"] not in fuera
        ]
        antes = {
            c["escenario"]: c
            for c in leer_resultados(RAIZ / "reports" / nombre / "calificados.jsonl")
        }
        carpeta = destino / nombre
        carpeta.mkdir(parents=True, exist_ok=True)

        def contar(registro: dict[str, Any]) -> None:
            nonlocal entrada, salida
            for t in registro["tokens_por_modelo"].values():
                entrada, salida = entrada + t["entrada"], salida + t["salida"]

        ahora = calificar(
            escenarios, ensayos, juez, carpeta / "juez.jsonl", huella=huella, al_juzgar=contar
        )
        for c in ahora:
            previo = antes.get(c["escenario"], {})
            filas.append(
                (
                    nombre,
                    c["escenario"],
                    _resumen(previo.get("juez")),
                    previo.get("superado"),
                    _resumen(c["juez"]),
                    c["superado"],
                    (c["juez"] or {}).get("afirmaciones_sin_fuente") or [],
                )
            )
    costo = costo_usd(settings.modelo_juez, entrada, salida)
    lineas = [
        f"# Recalificación con el juez actual ({args.destino})",
        "",
        f"Huella del juez: `{huella}`. Costo del juez: US${costo:.4f}. Sin llamar al sistema: "
        "las respuestas son las guardadas en cada corrida de origen.",
        "",
        "| Origen | Escenario | Antes | Superado antes | Ahora | Superado ahora | "
        "Afirmaciones sin fuente |",
        "|---|---|---|---|---|---|---|",
    ]
    for origen, esc, antes_, sup_a, ahora_, sup_h, lista in filas:
        marca = " **(cambia)**" if sup_a != sup_h else ""
        celda = "; ".join(f"«{a}»" for a in lista) or "—"
        lineas.append(
            f"| {origen} | {esc}{marca} | {antes_} | {'sí' if sup_a else 'no'} | {ahora_} | "
            f"{'sí' if sup_h else 'no'} | {celda.replace('|', '/')} |"
        )
    cambian = sum(1 for f in filas if f[3] != f[5])
    lineas += ["", f"Cambian {cambian} de {len(filas)} ensayos."]
    (destino / "comparacion.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print("\n".join(lineas))
    return 0


if __name__ == "__main__":
    sys.exit(main())
