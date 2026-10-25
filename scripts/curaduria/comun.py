"""Utilidades compartidas de la curaduría: rutas, catálogo de fuentes y corte por artículo."""

import re
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[2]
CATALOGO = Path(__file__).with_name("fuentes.yaml")
DESCARGAS = Path(__file__).with_name("descargas")
KNOWLEDGE_BASE = RAIZ / "knowledge_base"

_ARTICULO = re.compile(
    r"^\s*(?:#+\s*)?(?:\*\*)?ART[ÍI]CULO\s+(\d+[A-Za-z]?(?:\.\d+)*)\s*[º°o.\-–:]*",
    re.IGNORECASE | re.MULTILINE,
)


_SALTO_MAXIMO = 10


def cargar_catalogo() -> dict:
    """Lee el catálogo maestro de fuentes."""
    return yaml.safe_load(CATALOGO.read_text(encoding="utf-8"))


def cortar_por_articulo(texto: str) -> list[tuple[str, str]]:
    """Parte un texto en pares (número de artículo, contenido) según los encabezados «ARTÍCULO»."""
    marcas = []
    ultimo: tuple[int, ...] = ()
    for marca in _ARTICULO.finditer(texto):
        clave = tuple(int(n) for n in re.findall(r"\d+", marca.group(1)))
        salto = clave[0] - (ultimo[0] if ultimo else 0)
        # descarta las referencias cruzadas que empiezan una línea: el número no sube o salta mucho
        if clave > ultimo and (len(clave) > 1 or not ultimo or 0 < salto <= _SALTO_MAXIMO):
            marcas.append(marca)
            ultimo = clave
    cortes = []
    for i, marca in enumerate(marcas):
        fin = marcas[i + 1].start() if i + 1 < len(marcas) else len(texto)
        cortes.append((marca.group(1).rstrip("."), texto[marca.start() : fin].strip()))
    return cortes


def filtrar_articulos(cortes: list[tuple[str, str]], articulos: list[str]) -> list[tuple[str, str]]:
    """Conserva solo los artículos pedidos, en el orden en que aparecen."""
    pedidos = {str(a) for a in articulos}
    return [(n, t) for n, t in cortes if n in pedidos]
