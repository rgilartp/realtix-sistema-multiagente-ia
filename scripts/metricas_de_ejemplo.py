"""Métricas de ejemplo para las pruebas y las capturas de la consola (B11). No son resultados.

Arma un registro de interacciones a partir de una matriz de confusión de ejemplo y lo pasa por
`calcular_metricas`, el mismo cálculo de `/admin/metricas`: la exactitud, el total etiquetado, la
precisión, la exhaustividad y el F1 salen de los mismos pares, como en el sistema real. Las
duraciones son las de la medición de B9 (`reports/b09_latencia.json`), repetidas en orden.

Escribe `web/tests/metricas_de_ejemplo.json`.
Uso: uv run python scripts/metricas_de_ejemplo.py
"""

import json
import sys
from itertools import cycle
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.agents.state import CATEGORIAS  # noqa: E402
from src.services.metricas import calcular_metricas  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "web" / "tests" / "metricas_de_ejemplo.json"
# (categoría esperada, categoría del sistema) -> conversaciones de ejemplo
MATRIZ = {
    ("ipu", "ipu"): 15,
    ("ica", "ica"): 9,
    ("ica", "general"): 1,
    ("general", "general"): 7,
    ("ocr", "ocr"): 7,
    ("fuera_de_alcance", "fuera_de_alcance"): 3,
    ("fuera_de_alcance", "general"): 2,
}
SIN_ETIQUETA = 4  # turnos sin categoría esperada (horario) o de conversaciones sin escenario
ESCALADAS = 6


def interacciones_de_ejemplo() -> tuple[list[dict], dict[str, str | None]]:
    duraciones = cycle(
        r["duracion_ms"]
        for r in json.loads((RAIZ / "reports" / "b09_latencia.json").read_text("utf-8"))[
            "resultados"
        ]
    )
    etiquetas: dict[str, str | None] = {}
    interacciones: list[dict] = []
    n = 0
    for (esperada, predicha), cuantas in MATRIZ.items():
        for _ in range(cuantas):
            n += 1
            escenario = f"EJ-{n:02d}"
            etiquetas[escenario] = esperada
            interacciones.append(
                {
                    "id_conversacion": f"conv-{n:02d}",
                    "escenario_id": escenario,
                    "categoria": predicha,
                    "duracion_ms": next(duraciones),
                    "estado": "respondida",
                    "escalada": n <= ESCALADAS,
                }  # fmt: skip
            )
    for i in range(SIN_ETIQUETA):
        interacciones.append(
            {
                "id_conversacion": f"conv-sin-{i}",
                "escenario_id": None,
                "categoria": None,
                "duracion_ms": next(duraciones),
                "estado": "fuera_de_horario",
                "escalada": False,
            }  # fmt: skip
        )
    return interacciones, etiquetas


def main() -> None:
    interacciones, etiquetas = interacciones_de_ejemplo()
    metricas = calcular_metricas(interacciones, etiquetas, CATEGORIAS)
    SALIDA.write_text(json.dumps(metricas, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"Exactitud {metricas['exactitud']} con {metricas['turnos_etiquetados']} conversaciones "
        f"etiquetadas; escrito {SALIDA.relative_to(RAIZ)}"
    )


if __name__ == "__main__":
    main()
