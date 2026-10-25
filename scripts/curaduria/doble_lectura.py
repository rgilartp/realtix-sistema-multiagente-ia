"""Doble lectura de la tabla de ICA de 2027: compara la transcripción con el texto del OCR.

Para cada fila busca el código CIIU en el OCR de su página. Estados: `coincide` (el código y la
tarifa aparecen en la misma línea), `tarifa_distinta` (el OCR leyó otro número), `ocr_sin_tarifa`
(leyó el código pero no la tarifa) y `sin_lectura_ocr` (no leyó el código). Los tres últimos se
revisan en la vista lado a lado contra la imagen.
Escribe `docs/verificacion/ica_2027_doble_lectura.json`.
Uso: uv run python scripts/curaduria/doble_lectura.py
"""

import json
import re

import yaml
from comun import DESCARGAS, RAIZ

ICA_2027 = RAIZ / "datos" / "tarifas" / "ica_2027.yaml"
SALIDA = RAIZ / "docs" / "verificacion" / "ica_2027_doble_lectura.json"


def _lineas_ocr(pagina: int) -> list[str]:
    ruta = DESCARGAS / "ocr_1084" / f"pagina_{pagina:03d}.txt"
    return ruta.read_text(encoding="utf-8").splitlines() if ruta.exists() else []


def comparar() -> list[dict]:
    datos = yaml.safe_load(ICA_2027.read_text(encoding="utf-8"))
    resultados = []
    for fila in datos["por_actividad"]:
        codigo, tarifa = fila["ciiu"], fila["tarifa_por_mil"]
        con_codigo = [
            linea
            for linea in _lineas_ocr(fila["pagina_pdf"])
            if re.search(rf"(?<!\d){codigo}(?!\d)", linea)
        ]
        # lo que el OCR leyó después del código: las tarifas son números sueltos de 1 o 2 cifras
        leidos = [
            n
            for linea in con_codigo
            for n in re.findall(r"(?<![\d.])\d{1,2}(?![\d.])", linea.split(codigo, 1)[-1])
        ]
        if not con_codigo:
            estado = "sin_lectura_ocr"
        elif tarifa in leidos:
            estado = "coincide"
        elif leidos:
            estado = "tarifa_distinta"
        else:
            estado = "ocr_sin_tarifa"
        resultados.append(
            {"ciiu": codigo, "tarifa": tarifa, "pagina_pdf": fila["pagina_pdf"], "estado": estado}
        )
    return resultados


if __name__ == "__main__":
    resultados = comparar()
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(json.dumps(resultados, ensure_ascii=False, indent=1), encoding="utf-8")
    for estado in ("coincide", "tarifa_distinta", "ocr_sin_tarifa", "sin_lectura_ocr"):
        print(estado, sum(r["estado"] == estado for r in resultados))
