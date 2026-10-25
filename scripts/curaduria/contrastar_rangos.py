"""Contrasta `datos/tarifas/ipu_2026.yaml` con el texto del PDF de la resolución de rangos de 2026.

Lee el art. 1 (30 rangos residenciales urbanos) y el art. 2 (no residenciales) del PDF y compara
cada rango y cada tarifa con el YAML. Escribe `docs/verificacion/ipu_2026_contraste.json` y termina
con código 1 si hay diferencias.
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
_FILA = re.compile(r"\$\s*([\d.]+)\s+\$\s*([\d.]+|-)\s+(\d+(?:,\d+)?)")


def _entero(texto: str) -> int | None:
    return None if texto == "-" else int(texto.replace(".", ""))


def _articulo(texto: str, numero: int) -> str:
    inicio = re.search(rf"ART[ÍI]CULO\s+{numero}[º°o]?\.", texto, re.IGNORECASE)
    siguiente = re.search(rf"ART[ÍI]CULO\s+{numero + 1}[º°o]?\.", texto, re.IGNORECASE)
    return texto[inicio.start() : siguiente.start()] if inicio and siguiente else ""


def contrastar() -> list[str]:
    pdf = pypdfium2.PdfDocument(PDF)
    texto = "\n".join(pdf[i].get_textpage().get_text_range() for i in range(len(pdf)))
    datos = yaml.safe_load(YAML.read_text(encoding="utf-8"))
    diferencias = []
    filas_pdf = [
        (_entero(a), _entero(b), Decimal(c.replace(",", ".")))
        for a, b, c in _FILA.findall(_articulo(texto, 1))
    ]
    en_yaml = len(datos["residencial_urbano"])
    if len(filas_pdf) != en_yaml:
        diferencias.append(f"art. 1: el PDF tiene {len(filas_pdf)} rangos y el YAML {en_yaml}")
    for i, (pdf_fila, fila) in enumerate(
        zip(filas_pdf, datos["residencial_urbano"], strict=False), 1
    ):
        esperado = (fila["desde"], fila["hasta"], Decimal(fila["tarifa_por_mil"]))
        if pdf_fila != esperado:
            diferencias.append(f"art. 1, rango {i}: PDF {pdf_fila} contra YAML {esperado}")
    texto_no_res = _articulo(texto, 2)
    for fila in datos["no_residencial"]:
        for clave in ("desde", "hasta"):
            valor = fila[clave]
            formato = f"{valor:,}".replace(",", ".") if valor else None
            if valor and valor > 1 and formato not in texto_no_res:
                diferencias.append(
                    f"art. 2, {fila['destino']}: {clave} {formato} no está en el PDF"
                )
        tarifa = fila["tarifa_por_mil"].replace(".", ",")
        if not re.search(rf"(?<![\d.,]){tarifa}(?![\d.,])", texto_no_res):
            diferencias.append(f"art. 2, {fila['destino']}: tarifa {tarifa} no está en el PDF")
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(
        json.dumps(
            {"rangos_en_el_pdf": len(filas_pdf), "diferencias": diferencias},
            ensure_ascii=False,
            indent=1,
        )
        + "\n",
        encoding="utf-8",
    )
    return diferencias


if __name__ == "__main__":
    resultado = contrastar()
    print(f"{len(resultado)} diferencias")
    for linea in resultado:
        print(" -", linea)
    sys.exit(1 if resultado else 0)
