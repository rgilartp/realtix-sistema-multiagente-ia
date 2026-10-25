"""Contrasta `datos/tarifas/ipu_2026.yaml` con el texto del PDF de la resolución de rangos de 2026.

Lee del PDF el art. 1 (30 rangos residenciales urbanos), el art. 2 (predios no residenciales) y el
art. 3 (predios de clubes, destino 66) y compara cada rango y cada tarifa, fila por fila, con el
YAML. Escribe `docs/verificacion/ipu_2026_contraste.json` y termina con código 1 si hay diferencias.
Uso: uv run python scripts/curaduria/contrastar_rangos.py
"""

import json
import re
import sys
from decimal import Decimal

import pypdfium2
import yaml
from comun import DESCARGAS, RAIZ

PDF = DESCARGAS / "resolucion_000194_2025_rangos.pdf"
YAML = RAIZ / "datos" / "tarifas" / "ipu_2026.yaml"
SALIDA = RAIZ / "docs" / "verificacion" / "ipu_2026_contraste.json"
# art. 1: «$ desde $ hasta tarifa»; arts. 2 y 3: «tarifa $ desde [$ hasta]»
_FILA_ART_1 = re.compile(r"\$\s*([\d.]+)\s+\$\s*([\d.]+|-)\s+(\d+(?:,\d+)?)")
_FILA_ART_2_3 = re.compile(r"(?<![\d,.])(\d{1,2}(?:,\d{1,2})?) \$ ([\d.]+)(?: \$ ([\d.]+))?")


def _entero(texto: str | None) -> int | None:
    return None if texto in (None, "-") else int(texto.replace(".", ""))


def _articulo(texto: str, numero: int) -> str:
    inicio = re.search(rf"ART[ÍI]CULO\s+{numero}[º°o]?\.", texto, re.IGNORECASE)
    siguiente = re.search(rf"ART[ÍI]CULO\s+{numero + 1}[º°o]?\.", texto, re.IGNORECASE)
    return texto[inicio.start() : siguiente.start()] if inicio and siguiente else ""


def texto_del_pdf() -> str:
    pdf = pypdfium2.PdfDocument(PDF)
    return "\n".join(pdf[i].get_textpage().get_text_range() for i in range(len(pdf)))


def paginas_con_tablas() -> list[int]:
    """Páginas del PDF que traen filas de las tablas de los arts. 1, 2 y 3 (para las vistas)."""
    pdf = pypdfium2.PdfDocument(PDF)
    paginas = []
    for i in range(len(pdf)):
        texto = pdf[i].get_textpage().get_text_range()
        if _FILA_ART_1.search(texto) or _FILA_ART_2_3.search(texto):
            paginas.append(i + 1)
    return paginas


def _filas_art_1(texto: str) -> list[tuple]:
    return [
        (_entero(a), _entero(b), Decimal(c.replace(",", ".")))
        for a, b, c in _FILA_ART_1.findall(_articulo(texto, 1))
    ]


def _filas_art_2_3(texto: str, numero: int) -> list[tuple]:
    return [
        (_entero(d), _entero(h) if h else None, Decimal(t.replace(",", ".")))
        for t, d, h in _FILA_ART_2_3.findall(_articulo(texto, numero))
    ]


def _comparar(nombre: str, del_pdf: list[tuple], del_yaml: list[tuple]) -> list[str]:
    diferencias = []
    if len(del_pdf) != len(del_yaml):
        diferencias.append(f"{nombre}: el PDF tiene {len(del_pdf)} filas y el YAML {len(del_yaml)}")
    for i, (fila_pdf, fila_yaml) in enumerate(zip(del_pdf, del_yaml, strict=False), 1):
        if fila_pdf != fila_yaml:
            diferencias.append(f"{nombre}, fila {i}: PDF {fila_pdf} contra YAML {fila_yaml}")
    return diferencias


def contrastar() -> dict:
    texto = texto_del_pdf()
    datos = yaml.safe_load(YAML.read_text(encoding="utf-8"))

    def filas(lista: list[dict]) -> list[tuple]:
        return [(f["desde"], f["hasta"], Decimal(f["tarifa_por_mil"])) for f in lista]

    articulo_2 = _filas_art_2_3(texto, 2)
    articulo_3 = _filas_art_2_3(texto, 3)
    resultado = {
        "art_1": _comparar("art. 1", _filas_art_1(texto), filas(datos["residencial_urbano"])),
        "art_2": _comparar("art. 2", articulo_2, filas(datos["no_residencial"])),
        "art_3": _comparar("art. 3", articulo_3, filas(datos["clubes_destino_66"])),
    }
    conteos = {
        "art_1": len(_filas_art_1(texto)),
        "art_2": len(articulo_2),
        "art_3": len(articulo_3),
    }
    diferencias = [d for lista in resultado.values() for d in lista]
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(
        json.dumps(
            {"filas_en_el_pdf": conteos, "diferencias": diferencias}, ensure_ascii=False, indent=1
        )
        + "\n",
        encoding="utf-8",
    )
    return {"filas": conteos, "diferencias": diferencias}


if __name__ == "__main__":
    resultado = contrastar()
    print(
        f"filas leídas del PDF: {resultado['filas']}; {len(resultado['diferencias'])} diferencias"
    )
    for linea in resultado["diferencias"]:
        print(" -", linea)
    sys.exit(1 if resultado["diferencias"] else 0)
