"""Prueba la recuperación con los escenarios aprobados y embeddings reales (revisión externa).

Para cada escenario aprobado con `fuentes_esperadas` en `knowledge_base/`, pasa el primer turno por
el orquestador real (Sonnet 5.5, una llamada) y mira si los 5 primeros fragmentos de cada parte
traen la norma y el artículo esperados, con el texto de la parte y con la búsqueda en los términos
de la norma. Escribe `reports/recuperacion.json`.

Gasta una llamada a Sonnet y dos embeddings por parte de cada escenario: se corre una sola vez.
Uso: uv run python scripts/probar_recuperacion.py
"""

import json
import sys
from decimal import Decimal
from pathlib import Path

from langchain_core.callbacks import get_usage_metadata_callback

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.container import Contenedor  # noqa: E402
from src.evaluacion.escenarios import cargar_escenarios  # noqa: E402
from src.evaluacion.humo import sesiones  # noqa: E402
from src.evaluacion.recuperacion import probar_recuperacion  # noqa: E402
from src.integrations.costos import usos_desde_metadatos  # noqa: E402

SALIDA = Path("reports/recuperacion.json")


def main() -> None:
    contenedor = Contenedor()
    deps = contenedor.deps

    def avance(r: dict) -> None:
        marcas = " ".join(
            f"{'✓' if f['con_texto'] else '✗'}{'✓' if f['con_busqueda'] else '✗'} {f['fuente']}"
            for f in r["fuentes"]
        )
        print(f"{r['escenario']:<9} {marcas}")
        for parte in r["partes"]:
            print(f"          búsqueda ({parte['categoria']}): {parte['busqueda']}")

    with get_usage_metadata_callback() as uso:
        reporte = probar_recuperacion(
            cargar_escenarios(), deps.clasificador, deps, sesiones(), avance
        )
    usos = usos_desde_metadatos(uso.usage_metadata)
    reporte["costo_anthropic_usd"] = str(sum((u.costo_usd for u in usos), Decimal(0)))
    reporte["tokens"] = [
        {"modelo": u.modelo, "entrada": u.entrada, "salida": u.salida} for u in usos
    ]
    resumen = reporte["resumen"]
    print("(primera marca: con el texto de la parte; segunda: con la búsqueda)")
    for modo in ("con_texto", "con_busqueda"):
        r = resumen[modo]
        print(
            f"{modo}: {r['aciertos_por_fuente']}/{resumen['fuentes']} fuentes "
            f"({r['tasa_por_fuente']:.1%}); {r['escenarios_con_todas']}/{resumen['escenarios']} "
            f"escenarios con todas sus fuentes ({r['tasa_por_escenario']:.1%})"
        )
    print(f"Costo en Anthropic: US${reporte['costo_anthropic_usd']}")
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(json.dumps(reporte, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
