"""Compara `knowledge_base/` con un commit: filas de datos de las tablas y caracteres por artículo.

Uso: uv run python scripts/curaduria/comparar_kb.py 77f588c
"""

import re
import subprocess
import sys

from comun import KNOWLEDGE_BASE, RAIZ


def _articulos(texto: str) -> dict[str, str]:
    partes = re.split(r"(?m)^## Artículo ([\d.]+)$", texto)
    return dict(zip(partes[1::2], partes[2::2], strict=True))


def _filas_de_datos(texto: str) -> int:
    """Filas de datos de todas las tablas Markdown (sin encabezado ni separador)."""
    total, en_tabla = 0, 0
    for linea in [*texto.splitlines(), ""]:
        if linea.startswith("|"):
            en_tabla += 1
        else:
            total += max(en_tabla - 2, 0)
            en_tabla = 0
    return total


def _antes(commit: str, ruta: str) -> str | None:
    salida = subprocess.run(
        ["git", "show", f"{commit}:{ruta}"], cwd=RAIZ, capture_output=True, text=True, check=False
    )
    return salida.stdout if salida.returncode == 0 else None


def main(commit: str) -> None:
    for ruta in sorted(KNOWLEDGE_BASE.rglob("*.md")):
        relativa = ruta.relative_to(RAIZ).as_posix()
        antes = _antes(commit, relativa)
        if antes is None:
            print(f"{relativa}: archivo nuevo")
            continue
        ahora = ruta.read_text(encoding="utf-8")
        art_antes, art_ahora = _articulos(antes), _articulos(ahora)
        cambios = []
        for numero in art_antes.keys() | art_ahora.keys():
            a, b = art_antes.get(numero, ""), art_ahora.get(numero, "")
            fa, fb = _filas_de_datos(a), _filas_de_datos(b)
            if fa != fb or abs(len(a) - len(b)) > 200:
                cambios.append(f"  art. {numero}: filas {fa}→{fb}; caracteres {len(a)}→{len(b)}")
        if cambios:
            print(f"{relativa}: filas {_filas_de_datos(antes)}→{_filas_de_datos(ahora)}")
            print("\n".join(sorted(cambios, key=lambda c: float(c.split()[1].rstrip(":")))))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "77f588c")
