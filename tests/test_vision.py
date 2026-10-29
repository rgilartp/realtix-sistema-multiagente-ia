"""Imagen que se envía al modelo de visión, reducida si hace falta (fotos pesadas)."""

import base64
import io
import os

import pytest
from PIL import Image

from src.agents.vision import BYTES_MAXIMOS_PNG, imagen_para_el_modelo

OCR05 = "RF-OCR-05 · Modelo de visión"


def _abrir(datos: str) -> Image.Image:
    return Image.open(io.BytesIO(base64.b64decode(datos)))


@pytest.mark.unit
@pytest.mark.req(OCR05)
def test_la_plantilla_sigue_igual_en_png_de_1000_px() -> None:
    tipo, datos = imagen_para_el_modelo(Image.new("RGB", (1240, 1754), "white"))
    assert tipo == "image/png" and _abrir(datos).size == (1000, 1415)  # como antes


@pytest.mark.unit
@pytest.mark.req(OCR05)
def test_una_imagen_muy_alta_queda_en_2000_px_de_alto() -> None:
    _, datos = imagen_para_el_modelo(Image.new("RGB", (800, 6000), "white"))
    assert _abrir(datos).size == (267, 2000)


@pytest.mark.unit
@pytest.mark.req(OCR05)
def test_una_foto_pesada_va_en_jpeg_por_debajo_del_limite_de_la_api() -> None:
    foto = Image.frombytes("RGB", (1000, 1800), os.urandom(1000 * 1800 * 3))  # no se comprime
    tipo, datos = imagen_para_el_modelo(foto)
    assert tipo == "image/jpeg" and len(datos) < 5 * 1024 * 1024
    assert len(base64.b64decode(datos)) < BYTES_MAXIMOS_PNG


@pytest.mark.unit
@pytest.mark.req(
    "RF-OCR-04 · Rechazo de documentos ilegibles", "RNF-08 · Tiempos de espera y degradación"
)
def test_una_imagen_con_demasiados_pixeles_se_rechaza_sin_decodificarla(
    tmp_path, monkeypatch
) -> None:
    import src.agents.vision as vision

    assert Image.MAX_IMAGE_PIXELS == vision.PIXELES_MAXIMOS == 25_000_000
    ruta = tmp_path / "grande.png"
    Image.new("L", (300, 200)).save(ruta)
    monkeypatch.setattr(vision, "PIXELES_MAXIMOS", 59_999)  # el límite, bajado para la prueba
    decodificadas = []
    convertir = Image.Image.convert
    monkeypatch.setattr(
        Image.Image,
        "convert",
        lambda img, *a, **k: decodificadas.append(1) or convertir(img, *a, **k),
    )
    with pytest.raises(vision.ImagenDemasiadoGrandeError):
        vision.abrir_documento(ruta, "image/png")
    assert decodificadas == []  # se rechazó con el tamaño del encabezado
    monkeypatch.setattr(vision, "PIXELES_MAXIMOS", 60_000)  # justo en el límite: se abre
    assert vision.abrir_documento(ruta, "image/png").size == (300, 200)
