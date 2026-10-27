"""Verifica las referencias de los escenarios antes de la corrida 1 (ADR-24, A7). Sin red.

Escribe `reports/verificacion_referencias.md` y termina con código 1 si alguna fuente no existe o
alguna cifra no coincide: en ese caso es una parada, y Rodolfo decide (ninguna referencia aprobada
se cambia por cuenta propia).

Uso: uv run python scripts/verificar_referencias.py [--salida reports/verificacion_referencias.md]
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.evaluacion.escenarios import RAIZ, cargar_conjunto  # noqa: E402
from src.evaluacion.referencias import reporte, verificar_escenario  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--salida", type=Path, default=RAIZ / "reports" / "verificacion_referencias.md"
    )
    args = parser.parse_args()
    resultados = [verificar_escenario(e) for e in cargar_conjunto(["principal", "R3", "R4"])]
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    args.salida.write_text(reporte(resultados), encoding="utf-8")
    pendientes = [r for r in resultados if not r.pasa]
    cifras = sum(len(r.verificadas) for r in resultados)
    print(f"{len(resultados)} escenarios y {cifras} cifras verificadas")
    print(f"Escenarios con algo sin resolver: {len(pendientes)}")
    for r in pendientes:
        print(
            f"  {r.escenario}: fuentes {r.fuentes_faltantes or '—'}; cifras {r.sin_resolver or '—'}"
        )
    return 1 if pendientes else 0


if __name__ == "__main__":
    sys.exit(main())
