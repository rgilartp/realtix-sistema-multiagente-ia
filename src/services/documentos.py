"""Recibos del predial: legibilidad, validación de los campos y contraste con la cuenta (RF-OCR-02 a
RF-OCR-04). Sin LangGraph ni modelos.

- **Legibilidad (antes del modelo):** baja resolución, recorte y desenfoque se detectan por código y
  el documento se rechaza sin gastar una llamada. Los umbrales están calibrados con la plantilla
  sintética (RF-OCR-06): lado corto de 800 px, proporción A4 con un margen del 15 % y la varianza
  de los bordes (un recibo legible da unos 1.970, uno desenfocado unos 180). Con fotos reales
  habría que calibrarlos de nuevo.
- **Campos:** los seis de RF-OCR-02, normalizados (matrícula, vigencia, pesos y fecha). Uno que
  falta o no tiene el formato esperado hace el documento ilegible o incompleto.
- **Contraste:** compara el avalúo y el valor liquidado del recibo con la obligación del predial de
  esa vigencia en la cuenta; no modifica nada (ADR-05).
"""

import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Literal

from PIL import Image, ImageFilter, ImageStat

from src.services.obligaciones import CuentaTributo

Problema = Literal["desenfocado", "baja_resolucion", "recortado", "no_es_recibo", "ilegible",
                   "incompleto"]  # fmt: skip
LADO_CORTO_MINIMO = 800
PROPORCION_A4 = 1754 / 1240
MARGEN_PROPORCION = 0.15
NITIDEZ_MINIMA = 800.0
ANCHO_DE_REFERENCIA = 1240
MATRICULA = re.compile(r"^50C-\d{7}$")
CAMPOS = ("matricula", "vigencia", "avaluo", "valor_liquidado", "descuento", "fecha_limite")


def nitidez(imagen: Image.Image) -> float:
    """Varianza de los bordes de la imagen en gris, llevada al ancho de la plantilla."""
    gris = imagen.convert("L")
    if gris.width != ANCHO_DE_REFERENCIA:
        alto = max(1, round(gris.height * ANCHO_DE_REFERENCIA / gris.width))
        gris = gris.resize((ANCHO_DE_REFERENCIA, alto))
    return float(ImageStat.Stat(gris.filter(ImageFilter.FIND_EDGES)).var[0])


def problemas_de_legibilidad(imagen: Image.Image) -> list[Problema]:
    """Los problemas que se ven sin leer el documento, en el orden en que se informan."""
    problemas: list[Problema] = []
    proporcion = imagen.height / imagen.width
    if abs(proporcion - PROPORCION_A4) / PROPORCION_A4 > MARGEN_PROPORCION:
        problemas.append("recortado")
    if min(imagen.size) < LADO_CORTO_MINIMO:
        problemas.append("baja_resolucion")
    elif nitidez(imagen) < NITIDEZ_MINIMA:  # una imagen pequeña ya se informa por resolución
        problemas.append("desenfocado")
    return problemas


@dataclass(frozen=True)
class CamposRecibo:
    """Los seis campos de RF-OCR-02, ya normalizados."""

    matricula: str
    vigencia: int
    avaluo: int
    valor_liquidado: int
    descuento: int
    fecha_limite: date

    def como_texto(self) -> dict[str, str]:
        def pesos(valor: int) -> str:
            return "$" + f"{valor:,}".replace(",", ".")

        return {
            "matricula": self.matricula,
            "vigencia": str(self.vigencia),
            "avaluo": pesos(self.avaluo),
            "valor_liquidado": pesos(self.valor_liquidado),
            "descuento": pesos(self.descuento),
            "fecha_limite": self.fecha_limite.strftime("%d/%m/%Y"),
        }


def a_pesos(texto: str | None) -> int | None:
    """«$2.135.000» o «2135000» -> 2135000; con centavos o letras, `None`."""
    if texto is None:
        return None
    limpio = re.sub(r"[\s$]|COP", "", str(texto), flags=re.IGNORECASE)
    if not re.fullmatch(r"\d{1,3}(?:[.,]\d{3})*|\d+", limpio):
        return None
    return int(re.sub(r"[.,]", "", limpio))


def a_fecha(texto: str | None) -> date | None:
    """«10/07/2026», «10-07-2026» o «2026-07-10»."""
    if not texto:
        return None
    for formato in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(str(texto).strip(), formato).date()
        except ValueError:
            continue
    return None


def validar_campos(crudos: dict[str, Any]) -> tuple[CamposRecibo | None, list[str]]:
    """Normaliza los campos leídos; devuelve también los que faltan o no tienen formato válido."""
    matricula = str(crudos.get("matricula") or "").strip().upper().replace(" ", "")
    vigencia = str(crudos.get("vigencia") or "").strip()
    valores = {
        "matricula": matricula if MATRICULA.match(matricula) else None,
        "vigencia": int(vigencia) if re.fullmatch(r"20\d{2}", vigencia) else None,
        "avaluo": a_pesos(crudos.get("avaluo")),
        "valor_liquidado": a_pesos(crudos.get("valor_liquidado")),
        "descuento": a_pesos(crudos.get("descuento")),
        "fecha_limite": a_fecha(crudos.get("fecha_limite")),
    }
    invalidos = [c for c in CAMPOS if valores[c] is None]
    if invalidos:
        return None, invalidos
    return CamposRecibo(**valores), []  # type: ignore[arg-type]


@dataclass(frozen=True)
class Contraste:
    encontrada: bool  # hay una obligación del predial de esa vigencia en la cuenta
    coinciden: bool
    diferencias: tuple[tuple[str, int, int], ...]  # (campo, del recibo, registrado)
    vencidas: int
    pendientes: int
    saldo: int


def contrastar(campos: CamposRecibo, cuenta: CuentaTributo) -> Contraste:
    """Compara el avalúo y el valor liquidado con la obligación del predial de esa vigencia."""
    situacion = next(
        (s for s in cuenta.obligaciones if s.obligacion.vigencia_fiscal == campos.vigencia), None
    )
    if situacion is None:
        return Contraste(False, False, (), cuenta.vencidas, cuenta.pendientes, cuenta.saldo)
    obligacion = situacion.obligacion
    diferencias = tuple(
        (campo, recibo, registrado)
        for campo, recibo, registrado in (
            ("avaluo", campos.avaluo, obligacion.base_gravable),
            ("valor_liquidado", campos.valor_liquidado, obligacion.valor_liquidado),
        )
        if recibo != registrado
    )
    return Contraste(
        True, not diferencias, diferencias, cuenta.vencidas, cuenta.pendientes, cuenta.saldo
    )
