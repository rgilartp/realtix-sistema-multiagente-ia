"""OCR en español del Acuerdo 1084 de 2026 (PDF escaneado), página por página.

Guarda las imágenes y el texto de cada página en `descargas/ocr_1084/` (carpeta ignorada por git);
El OCR sirve de contraste y de imagen para las vistas: el texto de `knowledge_base/` sale del texto
digital del Régimen Legal. Requiere Tesseract con el idioma español (`tesseract-ocr-spa`).
Uso: uv run python scripts/curaduria/ocr_1084.py
"""

import subprocess

import pypdfium2
from comun import DESCARGAS

PDF = DESCARGAS / "acuerdo_1084_2026_pdf.pdf"
SALIDA = DESCARGAS / "ocr_1084"
_ESCALA = 300 / 72  # 300 ppp


def ocr() -> int:
    SALIDA.mkdir(exist_ok=True)
    pdf = pypdfium2.PdfDocument(PDF)
    for i in range(len(pdf)):
        base = SALIDA / f"pagina_{i + 1:03d}"
        if base.with_suffix(".txt").exists():
            continue
        pdf[i].render(scale=_ESCALA).to_pil().convert("L").save(base.with_suffix(".png"))
        subprocess.run(
            ["tesseract", str(base.with_suffix(".png")), str(base), "-l", "spa", "--psm", "6"],
            check=True,
            capture_output=True,
        )
    return len(pdf)


if __name__ == "__main__":
    print(f"{ocr()} páginas leídas")
