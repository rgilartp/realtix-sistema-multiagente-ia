"""Prueba de humo con modelos reales y primera medición de latencia (B7, RNF-01).

Gasta tokens reales: se corre una sola vez por bloque. Escribe `reports/b07_humo.json`.

Uso: uv run python scripts/medir_latencia.py [--salida reports/b07_humo.json]
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.container import Contenedor  # noqa: E402
from src.evaluacion.humo import correr_humo  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--salida", type=Path, default=Path("reports/b07_humo.json"))
    args = parser.parse_args()

    def avance(r: dict) -> None:
        estado = f"escaló ({r['motivo_escalamiento']})" if r["escalado"] else "respondió"
        print(f"{r['escenario']:<9} {r['tipo']:<17} {r['duracion_ms']:>9.1f} ms  {estado}")

    reporte = correr_humo(Contenedor().deps, args.salida, avance)
    resumen = reporte["resumen"]
    for tipo, datos in resumen["latencia"].items():
        print(f"{tipo}: mediana {datos['mediana_ms']} ms, máximo {datos['maximo_ms']} ms")
    for modelo, t in resumen["tokens"].items():
        print(f"{modelo}: {t['entrada']} tokens de entrada, {t['salida']} de salida")
    print(f"Costo total: US${resumen['costo_total_usd']}")


if __name__ == "__main__":
    main()
