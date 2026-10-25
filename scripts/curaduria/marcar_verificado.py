"""Registra la verificación de las tablas de `datos/`.

Llena `verificado_por` (solo el nombre, sin fecha) en cada YAML de `datos/` que no esté pendiente y
marca la casilla de esa tabla en `docs/verificacion_curaduria.md`. Es idempotente.
Uso: uv run python scripts/curaduria/marcar_verificado.py --por "<nombre>"
"""

import argparse
import json
import re
from pathlib import Path

import yaml
from comun import RAIZ

_CLAVE = re.compile(r"^verificado_por:.*$", re.MULTILINE)


def _pendiente(ruta: Path) -> bool:
    datos = yaml.safe_load(ruta.read_text(encoding="utf-8"))
    return isinstance(datos, dict) and datos.get("estado") == "pendiente"


def marcar(por: str, raiz: Path = RAIZ) -> list[str]:
    """Marca los YAML y el documento de verificación; devuelve las rutas verificadas."""
    verificadas = []
    for ruta in sorted((raiz / "datos").rglob("*.yaml")):
        texto = ruta.read_text(encoding="utf-8")
        if not _CLAVE.search(texto) or _pendiente(ruta):
            continue
        ruta.write_text(
            _CLAVE.sub(f"verificado_por: {json.dumps(por, ensure_ascii=False)}", texto),
            encoding="utf-8",
        )
        verificadas.append(ruta.relative_to(raiz).as_posix())
    documento = raiz / "docs" / "verificacion_curaduria.md"
    contenido = documento.read_text(encoding="utf-8")
    for ruta in verificadas:
        patron = re.compile(
            rf"^- \[[ x]\] (`{re.escape(ruta)}`.*?)( Verificado por .*\.)?$", re.MULTILINE
        )
        contenido = patron.sub(rf"- [x] \1 Verificado por {por}.", contenido)
    documento.write_text(contenido, encoding="utf-8")
    return verificadas


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--por", required=True, help="nombre de quien verificó las tablas")
    args = parser.parse_args()
    for ruta in marcar(args.por):
        print("verificada:", ruta)


if __name__ == "__main__":
    main()
