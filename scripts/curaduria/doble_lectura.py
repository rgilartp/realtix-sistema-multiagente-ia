"""Doble lectura de la tabla de ICA de 2027: compara la transcripción con el texto del OCR.

Para cada fila busca el código CIIU en el OCR de su página. Estados: `coincide` (el código y la
tarifa aparecen en la misma línea), `tarifa_distinta` (el OCR leyó otro número), `ocr_sin_tarifa`
(leyó el código pero no la tarifa) y `sin_lectura_ocr` (no leyó el código). Los tres últimos se
revisan en la vista lado a lado contra la imagen.
Además compara con el texto digital del Régimen Legal (`regimen_legal`: coincide, distinta o
ausente). Escribe `docs/verificacion/ica_2027_doble_lectura.json`.
Uso: uv run python scripts/curaduria/doble_lectura.py
"""

import json
import re

import pypdfium2
import yaml
from comun import DESCARGAS, RAIZ

ICA_2027 = RAIZ / "datos" / "tarifas" / "ica_2027.yaml"
SALIDA_265 = RAIZ / "docs" / "verificacion" / "ica_2026_doble_lectura.json"
SALIDA = RAIZ / "docs" / "verificacion" / "ica_2027_doble_lectura.json"


def _lineas_ocr(pagina: int) -> list[str]:
    ruta = DESCARGAS / "ocr_1084" / f"pagina_{pagina:03d}.txt"
    return ruta.read_text(encoding="utf-8").splitlines() if ruta.exists() else []


def _tablas_acuerdo_65() -> tuple[dict[str, str], dict[str, tuple[str, str, str]]]:
    """Lee del texto digital del Régimen Legal (art. 3 del Acuerdo 65, con el art. 21 del 1084)."""
    texto = (RAIZ / "knowledge_base/normativa_ica/acuerdo_65_2002.md").read_text(encoding="utf-8")
    fijas = {
        m.group(2): m.group(3)
        for m in re.finditer(r"(?m)^\| (.+?) \| (\d{3,6}) \| (\d{1,2}) \|$", texto)
    }
    progresivas = {
        m.group(2): (m.group(3), m.group(4), m.group(5))
        for m in re.finditer(
            r"(?m)^\| (.+?) \| (\d{3,6}) \| (\d{1,2}) \| (\d{1,2}) \| (\d{1,2}) \|$", texto
        )
    }
    return fijas, progresivas


def tarifas_regimen_legal() -> dict[str, str]:
    """CIIU y tarifa de las actividades de tarifa fija del art. 21 del Acuerdo 1084."""
    return _tablas_acuerdo_65()[0]


def progresivas_regimen_legal() -> dict[str, tuple[str, str, str]]:
    """CIIU y tarifas (hasta 2027, 2028 y desde 2029) de las actividades financieras progresivas."""
    return _tablas_acuerdo_65()[1]


def comparar() -> list[dict]:
    datos = yaml.safe_load(ICA_2027.read_text(encoding="utf-8"))
    digital = tarifas_regimen_legal()
    digital = tarifas_regimen_legal()
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
        if codigo not in digital:
            texto_digital = "ausente"
        else:
            texto_digital = "coincide" if digital[codigo] == tarifa else "distinta"
        resultados.append(
            {
                "ciiu": codigo,
                "tarifa": tarifa,
                "pagina_pdf": fila["pagina_pdf"],
                "estado": estado,
                "regimen_legal": texto_digital,
            }
        )
    return resultados


def tarifas_registro_distrital() -> dict[str, list[str]]:
    """Lee del PDF del Registro Distrital 7103 la tabla de la Resolución SDH-000265 de 2021.

    El texto del PDF a veces junta filas sin salto de línea; por eso se parte la tabla por el inicio
    de cada fila (grupo, CIIU y descripción) y se toma la última serie de tarifas de cada tramo.
    """
    pdf = pypdfium2.PdfDocument(DESCARGAS / "registro_distrital_7103.pdf")
    texto = "\n".join(pdf[i].get_textpage().get_text_range() for i in range(len(pdf)))
    texto = texto.replace("\r", "")
    tabla = texto[texto.index("304 161 Actividades de apoyo a la agricultura") :]
    tabla = re.sub(r"(?m)^REGISTRO DISTRITAL[^\n]*\n?", "", tabla)
    tabla = re.sub(r"\s+", " ", tabla.replace("\ufffe", "").replace("\uf0ad", ""))
    inicios = list(
        re.finditer(r"(?<![\d,])(\d{3}) ((?:/ )?\d{1,5}(?:/\s?\d{4})?) (?=[A-ZÁÉÍÓÚÑ¿(])", tabla)
    )
    serie = r"((?:\d{1,2}(?:,\d{1,2})? ){2,3}\d{1,2}(?:,\d{1,2})?)"
    filas: dict[str, list[str]] = {}
    for actual, siguiente in zip(inicios, [*inicios[1:], None], strict=True):
        tramo = tabla[actual.end() : siguiente.start() if siguiente else len(tabla)]
        tarifas = re.search(serie + r"\s*$", tramo.strip() + " ") or re.search(serie, tramo)
        if tarifas:
            filas[actual.group(2)] = [t.replace(",", ".") for t in tarifas.group(1).split()]
    return filas


def comparar_resolucion_265() -> list[dict]:
    """Compara la tarifa de 2024 de cada CIIU entre la compilación de Hacienda y el Registro."""
    from construir_ica_2026 import CIIU_CORREGIDO, _filas_resolucion, _tarifa

    _, filas = _filas_resolucion()
    registro = tarifas_registro_distrital()
    resultados = []
    for fila in filas:
        if len(fila) < 6 or not all(re.fullmatch(r"[\d ,]+", x) for x in fila[3:]):
            continue
        codigo, hacienda = fila[1], _tarifa(fila[-1])
        leida = registro.get(codigo)  # los dos textos traen igual los códigos mal escritos
        codigo = CIIU_CORREGIDO.get(codigo, (codigo,))[0]
        if leida is None:
            estado = "sin_lectura_en_el_registro"
        else:
            estado = "coincide" if _tarifa(leida[-1]) == hacienda else "distinta"
        resultados.append({"ciiu": codigo, "tarifa_2024_hacienda": hacienda, "estado": estado})
    return resultados


if __name__ == "__main__":
    resultados = comparar()
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(json.dumps(resultados, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for estado in ("coincide", "tarifa_distinta", "ocr_sin_tarifa", "sin_lectura_ocr"):
        print("OCR", estado, sum(r["estado"] == estado for r in resultados))
    for estado in ("coincide", "distinta", "ausente"):
        print("Régimen Legal", estado, sum(r["regimen_legal"] == estado for r in resultados))
    res_265 = comparar_resolucion_265()
    SALIDA_265.write_text(
        json.dumps(res_265, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    for estado in ("coincide", "distinta", "sin_lectura_en_el_registro"):
        print("Resolución 265", estado, sum(r["estado"] == estado for r in res_265))
