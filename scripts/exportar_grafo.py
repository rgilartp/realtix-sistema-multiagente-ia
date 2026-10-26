"""Exporta el grafo implementado a Mermaid: docs/figuras/grafo_implementado.mmd (RF-SYS-01).

Uso: uv run python -m scripts.exportar_grafo [--salida docs/figuras/grafo_implementado.mmd]
"""

import argparse
from pathlib import Path

from src.agents.dependencias import Dependencias
from src.agents.graph import construir_grafo
from src.data.generar.generate_synthetic_data import DatosSinteticos
from src.data.memoria import RealSitEnMemoria

RUTA = Path("docs/figuras/grafo_implementado.mmd")


def mermaid_del_grafo() -> str:
    """Mermaid del grafo compilado, con nodos simulados y sin datos."""
    vacio = DatosSinteticos(fecha_referencia=None, semilla=0)  # type: ignore[arg-type]
    grafo = construir_grafo(Dependencias(RealSitEnMemoria(vacio)))
    return grafo.get_graph().draw_mermaid()


def main() -> None:
    parser = argparse.ArgumentParser(description="Exporta el grafo a Mermaid.")
    parser.add_argument("--salida", type=Path, default=RUTA)
    args = parser.parse_args()
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    args.salida.write_text(mermaid_del_grafo(), encoding="utf-8")
    print(f"Grafo escrito en {args.salida}")


if __name__ == "__main__":
    main()
