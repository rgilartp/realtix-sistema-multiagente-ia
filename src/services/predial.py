"""Tarifa del impuesto predial unificado (IPU) por año gravable.

`buscar_tarifa_ipu` es la única implementación de la búsqueda de tarifa: la usan el generador de
datos sintéticos, las pruebas y, en B5, la liquidación. Lee `datos/tarifas/ipu_AAAA.yaml` y el SMMLV
de `datos/uvt_smmlv.yaml`; nada de esto se escribe en el código.
"""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Literal

from src.services.datos_anuales import cargar_datos, porcentaje_pronto_pago, smmlv
from src.services.errores import AnioSinDatosError

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
    fuente = str(datos["fuente"])

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
                    fuente,
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
                        fuente,
                    )
        fila = _fila_general(_generales_residencial(datos, anio), avaluo)
        regla = "rango general residencial"
    else:
        fila = _fila_general(_filas_por_destino(datos, anio, destino), avaluo)
        regla = f"tarifa no residencial: {destino}"
    if fila is None:
        raise AnioSinDatosError(anio, f"tarifa del predial para el avalúo {avaluo}")
    return TarifaIPU(anio, destino, Decimal(fila["tarifa_por_mil"]), True, regla, fuente)


def valor_impuesto(base: int, tarifa_por_mil: Decimal) -> int:
    """Impuesto en pesos enteros: base × tarifa / 1000, con redondeo explícito al peso."""
    return int((Decimal(base) * tarifa_por_mil / 1000).quantize(_UN_PESO, rounding=ROUND_HALF_UP))


def descuento_pronto_pago(valor: int, anio: int) -> int:
    """Descuento por pronto pago sobre el valor a pagar, según el calendario del año."""
    pct = Decimal(porcentaje_pronto_pago(anio))
    return int((Decimal(valor) * pct / 100).quantize(_UN_PESO, rounding=ROUND_HALF_UP))
