"""Recibos sintéticos con un formato más realista, para probar el OCR (RF-OCR-04 y RF-OCR-06).

Los de `recibos.py` son una plantilla vertical de una columna. Estos son apaisados, con las
secciones de un recibo predial (identificación del predio, liquidación y pago) y un código de pago
inventado, con los datos del mismo recibo sintético y su leyenda. No usan logos, escudos ni marcas
reales.

- `completo`: el recibo entero, apaisado (no es un A4 vertical, pero no le falta nada).
- `recortado`: el mismo recibo sin la sección del pago (falta la fecha límite).
- `foto`: una foto sintética de un paisaje con una casa, sin texto: no es un recibo.
"""

import random

from PIL import Image, ImageDraw, ImageFilter

from src.data.generar.recibos import LEYENDA, Recibo, _ajustada, _fuente

ANCHO, ALTO = 1754, 1240  # A4 apaisado, a unos 150 ppp
GRIS, NEGRO, ROJO, BANDA = (90, 90, 90), (20, 20, 20), (170, 30, 30), (225, 232, 240)


def _seccion(d: ImageDraw.ImageDraw, caja: tuple[int, int, int, int], titulo: str,
             filas: list[tuple[str, str]]) -> None:  # fmt: skip
    x0, y0, x1, y1 = caja
    d.rectangle(caja, outline=GRIS, width=3)
    d.rectangle((x0, y0, x1, y0 + 56), fill=BANDA, outline=GRIS, width=3)
    d.text((x0 + 20, y0 + 12), titulo, font=_fuente(30), fill=NEGRO)
    y = y0 + 90
    for rotulo, valor in filas:
        d.text((x0 + 20, y), rotulo, font=_fuente(24), fill=GRIS)
        d.text((x0 + 20, y + 32), valor, font=_ajustada(valor, x1 - x0 - 40, 34), fill=NEGRO)
        y += 100


def dibujar_apaisado(recibo: Recibo) -> Image.Image:
    """El recibo legible y completo, apaisado y en tres secciones."""
    imagen = Image.new("RGB", (ANCHO, ALTO), "white")
    d = ImageDraw.Draw(imagen)
    d.rectangle((30, 30, ANCHO - 30, ALTO - 30), outline=GRIS, width=3)
    d.rectangle((30, 30, ANCHO - 30, 130), fill=(240, 240, 240), outline=GRIS, width=3)
    d.text((60, 46), LEYENDA.upper(), font=_fuente(32), fill=ROJO)
    d.text((60, 88), "No es un documento oficial", font=_fuente(24), fill=ROJO)
    d.text(
        (60, 160), "RECIBO SINTÉTICO DEL IMPUESTO PREDIAL UNIFICADO", font=_fuente(40), fill=NEGRO
    )
    d.text((60, 214), f"Vigencia fiscal {recibo.vigencia}", font=_fuente(28), fill=GRIS)
    _seccion(d, (60, 280, 860, 760), "Identificación del predio", [
        ("Matrícula catastral", recibo.matricula or ""),
        ("Dirección del predio", recibo.direccion or ""),
        ("Avalúo catastral", recibo.avaluo or ""),
        ("Tarifa", recibo.tarifa or ""),
    ])  # fmt: skip
    _seccion(d, (900, 280, ANCHO - 60, 760), "Liquidación", [
        ("Vigencia fiscal", recibo.vigencia or ""),
        ("Valor liquidado", recibo.valor_liquidado or ""),
        ("Descuento por pronto pago", recibo.descuento or ""),
    ])  # fmt: skip
    _seccion(d, (60, 800, ANCHO - 60, 1110), "Pago", [
        ("Fecha límite de pago", recibo.fecha_limite or ""),
    ])  # fmt: skip
    azar = random.Random(7)  # código de pago inventado: barras sin ningún significado
    x = 900
    while x < ANCHO - 100:
        grosor = azar.choice((3, 5, 8))
        d.rectangle((x, 900, x + grosor, 1060), fill=NEGRO)
        x += grosor + azar.choice((4, 6, 9))
    d.text((900, 1066), "Código de pago sintético", font=_fuente(22), fill=GRIS)
    d.text((60, ALTO - 100), LEYENDA, font=_fuente(30), fill=ROJO)
    return imagen


def recortar(imagen: Image.Image) -> Image.Image:
    """Sin la sección del pago: la foto cortó la parte de abajo."""
    return imagen.crop((0, 0, ANCHO, 820))  # el lado corto queda sobre los 800 px


def foto_que_no_es_recibo(semilla: int = 3) -> Image.Image:
    """Una foto sintética de un paisaje: cielo, montañas, pasto y una casa, con grano."""
    azar = random.Random(semilla)
    imagen = Image.new("RGB", (1600, 1200))
    d = ImageDraw.Draw(imagen)
    for y in range(700):  # cielo en degradado
        tono = int(150 + 80 * y / 700)
        d.line((0, y, 1600, y), fill=(tono - 60, tono - 20, 255))
    d.ellipse((1250, 120, 1400, 270), fill=(255, 225, 120))
    d.polygon([(0, 700), (300, 380), (650, 700)], fill=(70, 110, 90))
    d.polygon([(450, 700), (900, 300), (1350, 700)], fill=(60, 95, 80))
    d.rectangle((0, 700, 1600, 1200), fill=(80, 150, 70))
    d.rectangle((620, 620, 980, 900), fill=(200, 160, 120), outline=(90, 60, 40), width=6)
    d.polygon([(590, 630), (800, 470), (1010, 630)], fill=(150, 50, 40))
    d.rectangle((760, 760, 840, 900), fill=(90, 60, 40))
    d.rectangle((660, 680, 730, 740), fill=(180, 210, 230))
    d.rectangle((870, 680, 940, 740), fill=(180, 210, 230))
    for _ in range(400):  # flores y piedras
        x, y = azar.randrange(1600), azar.randrange(900, 1200)
        d.ellipse(
            (x, y, x + 8, y + 8),
            fill=azar.choice([(240, 240, 90), (230, 120, 160), (120, 120, 120)]),
        )
    ruido = Image.effect_noise((1600, 1200), 18).convert("RGB")
    return Image.blend(imagen, ruido, 0.08).filter(ImageFilter.SHARPEN)
