"""Aprueba las respuestas de referencia de los escenarios (ADR-22): llena `aprobado_por`.

No aprueba los escenarios con algo pendiente ni los excluidos con `--excluir`; el resto del archivo
no cambia. Después de aprobar, regenera la hoja de revisión.

Uso: uv run python scripts/aprobar_referencias.py --por "Nombre" [--excluir ID ...]
"""

import argparse
import sys
from pathlib import Path

# Permite correr el script por su ruta (`python scripts/...`) además de `python -m scripts....`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.evaluacion.escenarios import (  # noqa: E402
    HOJA_REVISION,
    INDICE,
    aprobar_referencias,
    cargar_escenarios,
    hoja_de_revision,
    indice,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--por", required=True, help="nombre de quien aprueba")
    parser.add_argument("--excluir", nargs="*", default=[], metavar="ID", help="no aprobar estos")
    args = parser.parse_args(argv)
    try:
        aprobados, excluidos, pendientes = aprobar_referencias(args.por, frozenset(args.excluir))
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2
    escenarios = cargar_escenarios()
    HOJA_REVISION.write_text(hoja_de_revision(escenarios), encoding="utf-8")
    INDICE.write_text(indice(escenarios), encoding="utf-8")
    print(f"Aprobados por {args.por}: {len(aprobados)}")
    if excluidos:
        print(f"Excluidos por ti ({len(excluidos)}): {', '.join(excluidos)}")
    if pendientes:
        print(f"Sin aprobar por tener algo pendiente ({len(pendientes)}): {', '.join(pendientes)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
