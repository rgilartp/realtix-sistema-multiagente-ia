"""Recibos sintéticos del predial (sección 4.5, RF-OCR-06 · Plantilla sintética de recibo).

Cada recibo sale del conjunto sintético (obligación del predial de 2026 de un usuario de prueba) con
los ocho campos de la plantilla, la leyenda «Documento sintético sin validez tributaria» y un JSON
de valores de referencia. No usa logos, escudos ni marcas reales: ni de Bogotá ni de la Secretaría
de Hacienda, ni de Realtix o RealSit. Se generan en PNG y en PDF, con DejaVu Sans (la que trae
matplotlib), así que el resultado es el mismo en cualquier máquina.

Variantes para RF-OCR-04: desenfocado, baja resolución, recortado (y recortado con baja resolución),
y un documento de otro tipo.

Uso: uv run python -m src.data.generar.recibos [--destino datos/recibos]
"""

import argparse
import json
from dataclasses import asdict, dataclass
from functools import cache
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from src.data.generar.generate_synthetic_data import DatosSinteticos, generar_datos
from src.data.models import Contribuyente, ObligacionTributaria, Predio

ANCHO, ALTO = 1240, 1754  # proporción A4 a unos 150 ppp
LEYENDA = "Documento sintético sin validez tributaria"
VIGENCIA = 2026
DESTINO = Path("datos/recibos")
RECIBOS = 10
USUARIO_VARIANTES = "U03"
CAMPOS_EXTRAIBLES = (
    "matricula",
    "vigencia",
    "avaluo",
    "valor_liquidado",
    "descuento",
    "fecha_limite",
)  # fmt: skip  RF-OCR-02, sin el nombre del propietario


@dataclass(frozen=True)
class Recibo:
    """Valores de referencia de un recibo (el JSON que acompaña a cada imagen)."""

    nombre: str
    tipo: str  # recibo_predial u otro_documento
    calidad: str  # legible, desenfocado, baja_resolucion, recortado, recortado_baja_resolucion
    usuario: str | None = None
    matricula: str | None = None
    propietario: str | None = None
    direccion: str | None = None
    vigencia: str | None = None
    avaluo: str | None = None
    tarifa: str | None = None
    valor_liquidado: str | None = None
    descuento: str | None = None
    fecha_limite: str | None = None

    def extraibles(self) -> dict[str, str | None]:
        """Los seis campos que debe extraer el agente OCR (RF-OCR-02)."""
        return {c: getattr(self, c) for c in CAMPOS_EXTRAIBLES}


def pesos(valor: int) -> str:
    return "$" + f"{valor:,}".replace(",", ".")


def por_mil(tarifa: Any) -> str:
    return f"{tarifa.normalize():f}".replace(".", ",") + " por mil"


SISTEMA_DEJAVU = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")


@cache
def ruta_de_la_fuente() -> Path:
    """DejaVu Sans (tiene tildes y eñes): la que trae matplotlib, igual en cualquier máquina, o la
    del sistema. La fuente por defecto de Pillow no tiene tildes."""
    try:
        import matplotlib

        candidata = Path(matplotlib.get_data_path()) / "fonts" / "ttf" / "DejaVuSans.ttf"
        if candidata.is_file():
            return candidata
    except ImportError:
        pass
    if SISTEMA_DEJAVU.is_file():
        return SISTEMA_DEJAVU
    raise FileNotFoundError("No se encontró DejaVu Sans para dibujar los recibos.")


def _fuente(tamano: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(ruta_de_la_fuente()), tamano)


def _ajustada(texto: str, ancho: int, tamano: int = 34) -> ImageFont.FreeTypeFont:
    """La fuente más grande (hasta `tamano`) con la que el texto cabe en `ancho` píxeles."""
    while tamano > 18 and _fuente(tamano).getlength(texto) > ancho:
        tamano -= 2
    return _fuente(tamano)


def lineas_del_recibo(recibo: Recibo) -> list[tuple[str, str]]:
    """(rótulo, valor) de los ocho campos de la plantilla, en orden."""
    return [
        ("Matrícula catastral", recibo.matricula or ""),
        ("Propietario", recibo.propietario or ""),
        ("Dirección del predio", recibo.direccion or ""),
        ("Vigencia fiscal", recibo.vigencia or ""),
        ("Avalúo catastral", recibo.avaluo or ""),
        ("Tarifa", recibo.tarifa or ""),
        ("Valor liquidado", recibo.valor_liquidado or ""),
        ("Descuento por pronto pago", recibo.descuento or ""),
        ("Fecha límite de pago", recibo.fecha_limite or ""),
    ]


def textos_del_documento(recibo: Recibo) -> list[str]:
    """Todo el texto que se dibuja (la prueba revisa que no haya marcas reales)."""
    if recibo.tipo == "otro_documento":
        return [*ENCABEZADO_OTRO, *(f"{r}: {v}" for r, v in LINEAS_OTRO), LEYENDA, LEYENDA]
    return [*ENCABEZADO_RECIBO, *(f"{r}: {v}" for r, v in lineas_del_recibo(recibo)), LEYENDA,
            LEYENDA]  # fmt: skip


ENCABEZADO_RECIBO = (
    "RECIBO SINTÉTICO DEL IMPUESTO PREDIAL UNIFICADO",
    "Entorno simulado de pruebas del sistema multiagente de IA",
)
ENCABEZADO_OTRO = (
    "CONSTANCIA SINTÉTICA DE INSCRIPCIÓN",
    "Taller comunitario de huerta urbana (entorno simulado de pruebas)",
)
LINEAS_OTRO = (
    ("Participante", "Persona de prueba"),
    ("Taller", "Huerta urbana, nivel básico"),
    ("Sesiones", "8 sesiones de 2 horas"),
    ("Código de inscripción", "TALLER-0042"),
    ("Estado", "Inscripción confirmada"),
)


def dibujar(recibo: Recibo) -> Image.Image:
    """La imagen legible del documento, sin logos ni marcas."""
    imagen = Image.new("RGB", (ANCHO, ALTO), "white")
    d = ImageDraw.Draw(imagen)
    gris, negro, rojo = (90, 90, 90), (20, 20, 20), (170, 30, 30)
    d.rectangle((40, 40, ANCHO - 40, ALTO - 40), outline=gris, width=3)
    d.rectangle((40, 40, ANCHO - 40, 150), fill=(235, 235, 235), outline=gris, width=3)
    d.text((70, 60), LEYENDA.upper(), font=_fuente(34), fill=rojo)
    d.text((70, 108), "No es un documento oficial", font=_fuente(26), fill=rojo)
    if recibo.tipo == "otro_documento":
        encabezado, lineas = ENCABEZADO_OTRO, list(LINEAS_OTRO)
    else:
        encabezado, lineas = ENCABEZADO_RECIBO, lineas_del_recibo(recibo)
    d.text((70, 200), encabezado[0], font=_fuente(40), fill=negro)
    d.text((70, 260), encabezado[1], font=_fuente(28), fill=gris)
    y = 360
    for rotulo, valor in lineas:
        d.line((70, y - 18, ANCHO - 70, y - 18), fill=(210, 210, 210), width=2)
        d.text((70, y), rotulo, font=_fuente(30), fill=gris)
        d.text((560, y), valor, font=_ajustada(valor, ANCHO - 70 - 560), fill=negro)
        y += 120
    d.rectangle(
        (40, ALTO - 150, ANCHO - 40, ALTO - 40), fill=(235, 235, 235), outline=gris, width=3
    )
    d.text((70, ALTO - 120), LEYENDA, font=_fuente(34), fill=rojo)
    return imagen


def degradar(imagen: Image.Image, calidad: str) -> Image.Image:
    """Variantes de RF-OCR-04."""
    if calidad == "desenfocado":
        return imagen.filter(ImageFilter.GaussianBlur(radius=6))
    if calidad == "baja_resolucion":
        return imagen.resize((ANCHO * 3 // 10, ALTO * 3 // 10), Image.Resampling.BILINEAR)
    if calidad == "recortado":
        return imagen.crop((0, 0, ANCHO, ALTO * 55 // 100))
    if calidad == "recortado_baja_resolucion":
        recorte = imagen.crop((0, 0, ANCHO, ALTO * 55 // 100))
        return recorte.resize((recorte.width * 3 // 10, recorte.height * 3 // 10))
    return imagen


def recibo_de(
    nombre: str,
    usuario: str,
    contribuyente: Contribuyente,
    predio: Predio,
    obligacion: ObligacionTributaria,
    calidad: str = "legible",
) -> Recibo:
    return Recibo(
        nombre=nombre,
        tipo="recibo_predial",
        calidad=calidad,
        usuario=usuario,
        matricula=predio.matricula_catastral,
        propietario=contribuyente.nombre,
        direccion=predio.direccion,
        vigencia=str(obligacion.vigencia_fiscal),
        avaluo=pesos(obligacion.base_gravable),
        tarifa=por_mil(obligacion.tarifa_por_mil),
        valor_liquidado=pesos(obligacion.valor_liquidado),
        descuento=pesos(obligacion.descuento_pronto_pago),
        fecha_limite=obligacion.fecha_limite_pago.strftime("%d/%m/%Y"),
    )


def recibos_del_conjunto(datos: DatosSinteticos, cantidad: int = RECIBOS) -> list[Recibo]:
    """Los recibos legibles de los usuarios fijos con predial de 2026 por pagar o pagado (no los
    excluidos), en orden de matrícula, y las variantes de U03 y el documento de otro tipo."""
    contribuyentes = {c.id_contribuyente: c for c in datos.contribuyentes}
    predios = {p.matricula_catastral: p for p in datos.predios}
    obligaciones = sorted(
        (
            o
            for o in datos.obligaciones
            if o.tipo_tributo == "IPU"
            and o.vigencia_fiscal == VIGENCIA
            and o.valor_liquidado > 0
            and o.matricula_catastral.startswith("50C-900")  # usuarios fijos (sección 4.2)
        ),
        key=lambda o: o.matricula_catastral,
    )
    recibos: list[Recibo] = []
    vistos: dict[str, int] = {}
    base_u03: tuple[Any, ...] | None = None
    for o in obligaciones[:cantidad]:
        predio = predios[o.matricula_catastral]
        usuario = f"U{int(o.matricula_catastral[-4:-2]):02d}"
        vistos[usuario] = vistos.get(usuario, 0) + 1
        sufijo = "" if vistos[usuario] == 1 else f"_{vistos[usuario]}"
        contribuyente = contribuyentes[predio.id_contribuyente]
        recibos.append(
            recibo_de(f"recibo_valido_{usuario}{sufijo}", usuario, contribuyente, predio, o)
        )
        if usuario == USUARIO_VARIANTES and not sufijo:
            base_u03 = (usuario, contribuyente, predio, o)
    if base_u03 is not None:
        for calidad, nombre in (
            ("desenfocado", "recibo_desenfocado_U03"),
            ("baja_resolucion", "recibo_baja_resolucion_U03"),
            ("recortado", "recibo_solo_recortado_U03"),
            ("recortado_baja_resolucion", "recibo_recortado_U03"),
        ):
            recibos.append(recibo_de(nombre, *base_u03, calidad=calidad))
    recibos.append(Recibo(nombre="documento_otro_tipo", tipo="otro_documento", calidad="legible"))
    return recibos


def imagen_de(recibo: Recibo) -> Image.Image:
    return degradar(dibujar(recibo), recibo.calidad)


def guardar(recibo: Recibo, destino: Path) -> dict[str, Path]:
    """PNG, PDF y JSON de referencia del recibo."""
    destino.mkdir(parents=True, exist_ok=True)
    imagen = imagen_de(recibo)
    rutas = {
        "png": destino / f"{recibo.nombre}.png",
        "pdf": destino / f"{recibo.nombre}.pdf",
        "json": destino / f"{recibo.nombre}.json",
    }
    imagen.save(rutas["png"], "PNG", optimize=True)
    imagen.save(rutas["pdf"], "PDF", resolution=150.0)
    referencia = {**asdict(recibo), "extraibles": recibo.extraibles(), "leyenda": LEYENDA}
    rutas["json"].write_text(json.dumps(referencia, ensure_ascii=False, indent=2) + "\n", "utf-8")
    return rutas


def generar_recibos(destino: Path = DESTINO, semilla: int = 42) -> list[Recibo]:
    recibos = recibos_del_conjunto(generar_datos(semilla))
    for recibo in recibos:
        guardar(recibo, destino)
    return recibos


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera los recibos sintéticos (sección 4.5).")
    parser.add_argument("--destino", type=Path, default=DESTINO)
    args = parser.parse_args()
    recibos = generar_recibos(args.destino)
    print(f"{len(recibos)} documentos en {args.destino}")


if __name__ == "__main__":
    main()
