"""Tarifa del impuesto predial unificado (IPU) por año gravable.

`buscar_tarifa_ipu` es la única implementación de la búsqueda de tarifa: la usan el generador de
datos sintéticos, las pruebas y, en B5, la liquidación. Lee `datos/tarifas/ipu_AAAA.yaml` y el SMMLV
de `datos/uvt_smmlv.yaml`; nada de esto se escribe en el código.
"""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Literal

from src.services import notas
from src.services.calendario_tributario import fechas_predial
from src.services.datos_anuales import cargar_datos, porcentaje_pronto_pago, smmlv, uvt
from src.services.errores import AnioSinDatosError, DatoNoPublicadoError

Destino = Literal["residencial", "comercial", "lote"]
_UN_PESO = Decimal(1)


@dataclass(frozen=True)
class TarifaIPU:
    """Resultado de la búsqueda: tarifa por mil, si el predio está obligado, regla y fuente."""

    anio: int
    destino: str
    tarifa_por_mil: Decimal
    obligado: bool
    regla: str
    fuente: str


def _a_pesos(valor: int, unidad: str | None, anio: int) -> int:
    return valor * smmlv(anio) if unidad == "SMMLV" else valor


def _en_rango(avaluo: int, desde: int, hasta: int | None, exclusivo: bool = False) -> bool:
    if avaluo < desde or (exclusivo and avaluo == desde):
        return False
    return hasta is None or avaluo <= hasta


def _fila_general(filas: list[dict[str, Any]], avaluo: int) -> dict[str, Any] | None:
    for fila in filas:
        if _en_rango(avaluo, fila["desde"], fila["hasta"]):
            return fila
    return None


def _filas_por_destino(datos: dict[str, Any], anio: int, destino: str) -> list[dict[str, Any]]:
    """Filas no residenciales de comercial o lote, con el nombre de destino de cada año."""
    if anio == 2026:
        prefijo = {"comercial": "Comercial (62)", "lote": "Urbanizables no urbanizados"}[destino]
        return [f for f in datos["no_residencial"] if f["destino"].startswith(prefijo)]
    nombre = {
        "comercial": "comercial",
        "lote": "urbanizables_no_urbanizados_y_urbanizables_no_edificados",
    }[destino]
    return [f for f in datos["generales"]["no_residencial"] if f["destino"] == nombre]


def _preferenciales(datos: dict[str, Any], anio: int) -> list[dict[str, Any]]:
    pref = datos["preferenciales"]
    if anio == 2026:
        return pref["residencial"]
    return pref["residencial_urbano_y_rural_agropecuario"]


def _generales_residencial(datos: dict[str, Any], anio: int) -> list[dict[str, Any]]:
    return datos["residencial_urbano"] if anio == 2026 else datos["generales"]["residencial"]


def buscar_tarifa_ipu(anio: int, destino: Destino, estrato: int | None, avaluo: int) -> TarifaIPU:
    """Tarifa por mil del predial del año gravable para un predio urbano.

    Residencial de estratos 1 a 3: compara el avalúo con 16, 107 y 135 SMMLV del mismo año; si el
    SMMLV aún no se publica (2027) falla con `DatoNoPublicadoError`. Estratos 1 y 2 por debajo del
    límite de exclusión quedan no obligados (2026: hasta 16 SMMLV; 2027: menos de 16 SMMLV).
    Año sin archivo: `AnioSinDatosError`.
    """
    if avaluo <= 0:
        raise ValueError("El avalúo debe ser mayor que cero.")
    datos = cargar_datos(f"tarifas/ipu_{anio}.yaml", anio, "predial")
    por_seccion = datos.get("fuentes_por_seccion") or {}

    def fuente(seccion: str) -> str:
        """La fuente de la sección que dio la tarifa; sin ella, la del archivo."""
        return str(por_seccion.get(seccion) or datos["fuente"])

    if destino == "residencial":
        if estrato in (1, 2, 3):
            propias = [f for f in _preferenciales(datos, anio) if estrato in f["estratos"]]
            primera = propias[0]
            piso = _a_pesos(primera["desde_valor"], primera["unidad_desde"], anio)
            if estrato in (1, 2) and not _en_rango(avaluo, piso, None, primera["desde_exclusivo"]):
                return TarifaIPU(
                    anio,
                    destino,
                    Decimal(0),
                    False,
                    "excluido: estratos 1 y 2 bajo el límite",
                    fuente("exclusion"),
                )
            for fila in propias:
                desde = _a_pesos(fila["desde_valor"], fila["unidad_desde"], anio)
                hasta = _a_pesos(fila["hasta_valor"], fila["unidad_hasta"], anio)
                if _en_rango(avaluo, desde, hasta, fila["desde_exclusivo"]):
                    return TarifaIPU(
                        anio,
                        destino,
                        Decimal(fila["tarifa_por_mil"]),
                        True,
                        "preferencial de estratos 1 a 3",
                        fuente("preferenciales"),
                    )
        fila = _fila_general(_generales_residencial(datos, anio), avaluo)
        regla, seccion = "rango general residencial", "residencial_urbano"
    else:
        fila = _fila_general(_filas_por_destino(datos, anio, destino), avaluo)
        regla, seccion = f"tarifa no residencial: {destino}", "no_residencial"
    if fila is None:
        raise AnioSinDatosError(anio, f"tarifa del predial para el avalúo {avaluo}")
    return TarifaIPU(anio, destino, Decimal(fila["tarifa_por_mil"]), True, regla, fuente(seccion))


def valor_impuesto(base: int, tarifa_por_mil: Decimal) -> int:
    """Impuesto en pesos enteros: base × tarifa / 1000, con redondeo explícito al peso."""
    return int((Decimal(base) * tarifa_por_mil / 1000).quantize(_UN_PESO, rounding=ROUND_HALF_UP))


def descuento_pronto_pago(valor: int, anio: int) -> int:
    """Descuento por pronto pago sobre el valor a pagar, según el calendario del año."""
    pct = Decimal(porcentaje_pronto_pago(anio))
    return int((Decimal(valor) * pct / 100).quantize(_UN_PESO, rounding=ROUND_HALF_UP))


@dataclass(frozen=True)
class SobretasaAlumbrado:
    """Sobretasa de alumbrado público de 2027 (Acuerdo 1084 de 2026, arts. 13 a 15)."""

    categoria: str
    tarifa_por_mil: Decimal
    valor: int
    tope_uvt: int | None  # None: la UVT de 2027 aún no se publica y no se aplica el tope
    tope_aplicado: bool


@dataclass(frozen=True)
class LiquidacionPredial:
    """Liquidación estimada, con valores exactos (sin aproximar al mil) y sus notas."""

    anio: int
    destino: str
    estrato: int | None
    avaluo: int
    tarifa: TarifaIPU
    impuesto: int
    porcentaje_descuento: int | None  # None: el descuento del año aún no se publica
    descuento: int | None
    total_con_descuento: int | None
    fecha_descuento: str | None
    fecha_sin_descuento: str | None
    sobretasa: SobretasaAlumbrado | None
    fuentes: tuple[str, ...]
    notas: tuple[str, ...]

    @property
    def total_estimado(self) -> int:
        """Impuesto más la sobretasa de alumbrado, si la hay, sin el descuento."""
        return self.impuesto + (self.sobretasa.valor if self.sobretasa else 0)


def _sobretasa_2027(
    destino: Destino, estrato: int | None, avaluo: int
) -> tuple[SobretasaAlumbrado | None, tuple[str, ...]]:
    datos = cargar_datos("tarifas/sobretasa_alumbrado_2027.yaml", 2027, "sobretasa de alumbrado")
    tarifas = {t["categoria"]: t for t in datos["tarifas_por_mil"]}
    topes = {t["categoria"]: t["valor_limite_uvt"] for t in datos["topes_uvt"]}
    if destino == "residencial":
        if estrato in (1, 2, 3):
            try:
                grande = avaluo > 20000 * uvt(2027)
            except DatoNoPublicadoError:  # sin la UVT no se sabe la categoría: no se estima
                return None, (notas.NOTA_SOBRETASA_SIN_UVT,)
            categoria = (
                "residencial_123_mas_de_20000_uvt_y_456"
                if grande
                else "residencial_123_hasta_20000_uvt_y_otros"
            )
        else:
            categoria = "residencial_123_mas_de_20000_uvt_y_456"
        tope_clave = "residenciales"
    else:
        categoria = (
            "comercial_financiero_industrial"
            if destino == "comercial"
            else "dotacional_y_urbanizables"
        )
        tope_clave = "demas_predios"
    tarifa = Decimal(tarifas[categoria]["de_2027_a_2041"])
    valor = valor_impuesto(avaluo, tarifa)
    tope_uvt = int(topes[tope_clave])
    try:
        tope_pesos = tope_uvt * uvt(2027)
    except DatoNoPublicadoError:
        return SobretasaAlumbrado(categoria, tarifa, valor, None, False), (
            notas.NOTA_TOPE_SOBRETASA,
        )
    aplicado = valor > tope_pesos
    return SobretasaAlumbrado(categoria, tarifa, min(valor, tope_pesos), tope_uvt, aplicado), ()


def liquidar_predial(
    anio: int, destino: Destino, estrato: int | None, avaluo: int
) -> LiquidacionPredial:
    """Liquidación estimada del predial del año gravable (RF-IPU-03).

    Los valores son exactos: no se aproximan al múltiplo de mil, que lo hacen la factura y la
    declaración (decisión de Rodolfo, nota de aproximación). Si el año o un dato necesario (SMMLV
    de 2027) no está publicado, falla de forma explícita y no estima.
    """
    tarifa = buscar_tarifa_ipu(anio, destino, estrato, avaluo)
    impuesto = valor_impuesto(avaluo, tarifa.tarifa_por_mil) if tarifa.obligado else 0
    fuentes = [tarifa.fuente]
    avisos = [notas.NOTA_ESTIMACION, notas.NOTA_APROXIMACION_PREDIAL, notas.NOTA_LEY_1995]
    porcentaje: int | None = None
    descuento: int | None = None
    total: int | None = None
    fecha_descuento: str | None = None
    fecha_sin: str | None = None
    try:
        porcentaje = porcentaje_pronto_pago(anio)
        fechas = fechas_predial(anio)
    except AnioSinDatosError:
        avisos.append(notas.NOTA_DESCUENTO_2027)
    else:
        descuento = descuento_pronto_pago(impuesto, anio)
        total = impuesto - descuento
        fecha_descuento, fecha_sin = fechas["pronto_pago"], fechas["sin_descuento"]
        fuentes.append("Resolución SDH-000195 de 2025, arts. 3 y 6")
    sobretasa: SobretasaAlumbrado | None = None
    if anio >= 2027 and tarifa.obligado:
        sobretasa, extra = _sobretasa_2027(destino, estrato, avaluo)
        avisos.extend(extra)
        fuentes.append("Acuerdo 1084 de 2026, arts. 13 a 15")
    if anio >= 2027:
        avisos.append(notas.NOTA_IVIUR_2027)
    return LiquidacionPredial(
        anio=anio,
        destino=destino,
        estrato=estrato,
        avaluo=avaluo,
        tarifa=tarifa,
        impuesto=impuesto,
        porcentaje_descuento=porcentaje,
        descuento=descuento,
        total_con_descuento=total,
        fecha_descuento=fecha_descuento,
        fecha_sin_descuento=fecha_sin,
        sobretasa=sobretasa,
        fuentes=tuple(fuentes),
        notas=tuple(avisos),
    )
