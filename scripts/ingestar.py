"""Ingesta y reingesta idempotente de `knowledge_base/` en Chroma (sección 5.5 y RF-OBS-04).

Reporta, por colección, los fragmentos, los que se embebieron, los que reutilizaron su embedding
(mismo texto con otro id o con otros metadatos), los borrados, los tokens y el costo
de los embeddings (`text-embedding-3-large`). Correrla otra vez sin cambios no gasta nada. Con
`--simular` solo cuenta tokens y costo, sin llamar a OpenAI ni escribir en Chroma.

Uso: uv run python scripts/ingestar.py [--simular]
Requiere el Chroma de Compose: docker compose up -d chromadb
"""

import argparse
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.container import Contenedor  # noqa: E402
from src.integrations.ingesta import ingestar  # noqa: E402
from src.integrations.segmentacion import version_del_corpus  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--simular", action="store_true", help="solo cuenta tokens y costo")
    args = parser.parse_args()
    contenedor = Contenedor()
    reportes = ingestar(
        contenedor.cliente_chroma(),
        contenedor.embeddings,
        simular=args.simular,
        modelo=contenedor.settings.modelo_embeddings,
    )
    print(f"Versión del corpus: {version_del_corpus()}{' (simulación)' if args.simular else ''}")
    columnas = f"{'Colección':<20}{'Fragmentos':>11}{'Embebidos':>11}{'Reutilizados':>14}"
    print(f"{columnas}{'Borrados':>10}{'Tokens':>10}  Costo")
    for r in reportes:
        print(
            f"{r.coleccion:<20}{r.fragmentos:>11}{r.embebidos:>11}{r.reutilizados:>14}"
            f"{r.borrados:>10}{r.tokens:>10}  US${r.costo_usd:.4f}"
        )
    total = sum((r.costo_usd for r in reportes), Decimal(0))
    print(f"Total: {sum(r.tokens for r in reportes)} tokens, US${total:.4f}")


if __name__ == "__main__":
    main()
