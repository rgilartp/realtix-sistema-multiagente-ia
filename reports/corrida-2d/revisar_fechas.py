"""Comprobaciones de las sondas que no dependen de la pregunta, sobre todas las respuestas de una
corrida y sin llamar modelos (regla de la 2d): expresiones que relacionan una fecha con el día de la
consulta, referencias internas, y fechas dadas por vencidas (iguales o posteriores al reloj del
escenario) o por pendientes (anteriores). Escribe `revision_fechas.json` y `revision_fechas.md` en
la carpeta de la corrida. Se corre desde la raíz del repositorio:

    uv run python reports/<corrida>/revisar_fechas.py <corrida>
"""

import json
import os
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(os.environ.get("RAIZ_REPO") or Path(__file__).resolve().parents[2])
sys.path.insert(0, str(RAIZ / "reports" / "verif-fechas-por-codigo"))
sys.path.insert(0, str(RAIZ))

from sondas import (  # noqa: E402
    OTRAS_RELATIVAS,
    PENDIENTE,
    fechas_de,
    normal,
    oraciones,
    vencio_afirmativo,
)

from src.evaluacion.escenarios import cargar_conjunto  # noqa: E402
from src.services.expresiones_relativas import expresiones_relativas  # noqa: E402


def revisar(texto: str, hoy: date) -> dict[str, list[str]]:
    encontradas = expresiones_relativas(texto)
    internas = [e for e in encontradas if e.startswith(("fragmento", "consultar"))]
    relativas = [e for e in encontradas if e not in internas]
    relativas += [m.group(0) for m in OTRAS_RELATIVAS.finditer(normal(texto))]
    futuras, pasadas = [], []
    for o in oraciones(texto):
        fechas = [f for f, _ in fechas_de(o, hoy.year)]
        if any(f >= hoy for f in fechas) and vencio_afirmativo(o):
            futuras.append(o[:200])
        if any(f < hoy for f in fechas) and PENDIENTE.search(o):
            pasadas.append(o[:200])
    return {
        "relativas": relativas,
        "referencias_internas": internas,
        "futura_dada_por_vencida": futuras,
        "pasada_dada_por_pendiente": pasadas,
    }


def main() -> int:
    corrida = sys.argv[1]
    carpeta = RAIZ / "reports" / corrida
    relojes = {e["id"]: e["reloj"] for e in cargar_conjunto(["principal", "R1", "R3", "R4"])}
    hallazgos = []
    revisadas = 0
    for linea in (carpeta / "resultados.jsonl").read_text(encoding="utf-8").splitlines():
        ensayo = json.loads(linea)
        hoy = date.fromisoformat(relojes[ensayo["escenario"]][:10])
        for n, turno in enumerate(ensayo["turnos"], 1):
            revisadas += 1
            r = revisar(turno.get("respuesta") or "", hoy)
            if any(r.values()):
                hallazgos.append({"escenario": ensayo["escenario"], "turno": n, **r})
    (carpeta / "revision_fechas.json").write_text(
        json.dumps(
            {"respuestas_revisadas": revisadas, "con_hallazgos": hallazgos},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",  # fmt: skip
        encoding="utf-8",
    )
    lineas = [
        f"# Revisión de fechas de la {corrida} (sin modelos)",
        "",
        f"{revisadas} respuestas revisadas; {len(hallazgos)} con algo señalado.",
        "",
        "| Escenario | Turno | Relativas | Referencias internas | Futura vencida | "
        "Pasada pendiente |",
        "|---|---|---|---|---|---|",
    ]
    for h in hallazgos:
        lineas.append(
            f"| {h['escenario']} | {h['turno']} | {', '.join(h['relativas']) or '—'} | "
            f"{', '.join(h['referencias_internas']) or '—'} | "
            f"{len(h['futura_dada_por_vencida'])} | {len(h['pasada_dada_por_pendiente'])} |"
        )
    (carpeta / "revision_fechas.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print(f"{revisadas} respuestas; {len(hallazgos)} con algo señalado")
    return 0


if __name__ == "__main__":
    sys.exit(main())
