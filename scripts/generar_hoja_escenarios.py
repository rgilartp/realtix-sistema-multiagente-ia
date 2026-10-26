"""Genera la hoja de revisión de las referencias y el índice de los escenarios.

Escribe `docs/revision_referencias.md` y `tests/escenarios/INDICE.md` a partir de los YAML de
`tests/escenarios/`. Con `--verificar` no escribe: falla si alguno de los dos está desactualizado.

Uso: uv run python scripts/generar_hoja_escenarios.py [--verificar]
"""

import argparse
import sys
from pathlib import Path

# Permite correr el script por su ruta (`python scripts/...`) además de `python -m scripts....`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.evaluacion.escenarios import (  # noqa: E402
    HOJA_REVISION,
    INDICE,
    cargar_escenarios,
    hoja_de_revision,
    indice,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--verificar", action="store_true", help="solo comprobar, sin escribir")
    args = parser.parse_args(argv)
    escenarios = cargar_escenarios()
    esperado = {HOJA_REVISION: hoja_de_revision(escenarios), INDICE: indice(escenarios)}
    desactualizados = [
        ruta for ruta, texto in esperado.items()
        if not ruta.exists() or ruta.read_text(encoding="utf-8") != texto
    ]  # fmt: skip
    if args.verificar:
        for ruta in desactualizados:
            print(f"Desactualizado: {ruta}", file=sys.stderr)
        return 1 if desactualizados else 0
    for ruta, texto in esperado.items():
        ruta.write_text(texto, encoding="utf-8")
        print(f"Escrito: {ruta}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
