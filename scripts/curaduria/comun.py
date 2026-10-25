"""Utilidades compartidas de la curaduría: rutas, catálogo de fuentes y corte por artículo."""

import re
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[2]
CATALOGO = Path(__file__).with_name("fuentes.yaml")
DESCARGAS = Path(__file__).with_name("descargas")
KNOWLEDGE_BASE = RAIZ / "knowledge_base"

_ARTICULO = re.compile(
    r"^\s*(?:#+\s*)?(?:\*\*)?(?:ART[ÍI]CULO|Art[íi]culo)\s+(\d+(?:\.\d+)*)[º°o]?\s*[.\-–:]*",
    re.MULTILINE,
)


_SALTO_MAXIMO = 10


def cargar_catalogo() -> dict:
    """Lee el catálogo maestro de fuentes."""
    return yaml.safe_load(CATALOGO.read_text(encoding="utf-8"))


def _sigue(previa: tuple[int, ...], clave: tuple[int, ...]) -> bool:
    if clave <= previa:
        return False
    return len(clave) > 1 or len(previa) > 1 or clave[0] - previa[0] <= _SALTO_MAXIMO


def _cadena_mas_larga(candidatas: list) -> list:
    """Elige la sucesión creciente más larga de encabezados y descarta las referencias sueltas."""
    mejor: list[int] = []  # longitud de la cadena que termina en cada candidata
    anterior: list[int] = []
    for i, (_, clave) in enumerate(candidatas):
        largo, previo = 1, -1
        for j in range(i):
            if mejor[j] + 1 > largo and _sigue(candidatas[j][1], clave):
                largo, previo = mejor[j] + 1, j
        mejor.append(largo)
        anterior.append(previo)
    if not candidatas:
        return []
    i = max(range(len(candidatas)), key=lambda k: mejor[k])
    cadena = []
    while i != -1:
        cadena.append(candidatas[i][0])
        i = anterior[i]
    return cadena[::-1]


def cortar_por_articulo(texto: str) -> list[tuple[str, str]]:
    """Parte un texto en pares (número de artículo, contenido) según los encabezados «ARTÍCULO»."""
    candidatas = [
        (m, tuple(int(n) for n in re.findall(r"\d+", m.group(1))))
        for m in _ARTICULO.finditer(texto)
    ]
    marcas = _cadena_mas_larga(candidatas)
    cortes = []
    for i, marca in enumerate(marcas):
        fin = marcas[i + 1].start() if i + 1 < len(marcas) else len(texto)
        cortes.append((marca.group(1).rstrip("."), texto[marca.start() : fin].strip()))
    return cortes


def filtrar_articulos(cortes: list[tuple[str, str]], articulos: list[str]) -> list[tuple[str, str]]:
    """Conserva solo los artículos pedidos, en el orden en que aparecen."""
    pedidos = {str(a) for a in articulos}
    return [(n, t) for n, t in cortes if n in pedidos]
