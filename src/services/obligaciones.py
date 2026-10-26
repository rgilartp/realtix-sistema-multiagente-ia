"""Situación del contribuyente en un tributo: obligaciones, saldo, vencimientos y pagos.

El estado de cuenta de un predio mezcla el predial y el ICA (las obligaciones del ICA cuelgan del
predio); este servicio separa cada tributo y decide, con la fecha de hoy (el reloj, no la vigencia
fija), qué está vencido. Si hay algo vencido, agrega la nota de intereses de mora (no se calculan).
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

from src.data.models import ESTADOS_VIGENTES, EstadoCuenta, ObligacionTributaria, Pago
from src.services import notas


@dataclass(frozen=True)
class SituacionObligacion:
    obligacion: ObligacionTributaria
    pagado: int
    saldo: int  # lo que falta pagar de una obligación pendiente o vencida; 0 si está al día
    vencida: bool
    descuento_vigente: bool  # el plazo del descuento por pronto pago aún no ha pasado


@dataclass(frozen=True)
class CuentaTributo:
    tributo: str
    obligaciones: tuple[SituacionObligacion, ...]
    pagos: tuple[Pago, ...]
    pendientes: int
    vencidas: int
    saldo: int
    notas: tuple[str, ...]


def esta_vencida(obligacion: ObligacionTributaria, saldo: int, hoy: date) -> bool:
    """Vencida: no está pagada y ya pasó su fecha límite (o la base la registra como vencida)."""
    if obligacion.estado_pago not in ESTADOS_VIGENTES or saldo <= 0:
        return False
    return obligacion.estado_pago == "VENCIDO" or obligacion.fecha_limite_pago < hoy


def descuento_vigente(fecha_limite_descuento: date | str | None, hoy: date) -> bool:
    """El descuento por pronto pago sigue disponible si su fecha límite no ha pasado."""
    if fecha_limite_descuento is None:
        return False
    if isinstance(fecha_limite_descuento, str):
        fecha_limite_descuento = date.fromisoformat(fecha_limite_descuento)
    return hoy <= fecha_limite_descuento


def de_tributo(estado: EstadoCuenta, pagos: list[Pago], tributo: str, hoy: date) -> CuentaTributo:
    """Obligaciones, pagos y saldo de un solo tributo (`IPU` o `ICA`) del estado de cuenta."""
    pagado: dict[str, int] = {}
    for pago in pagos:
        pagado[pago.id_obligacion] = pagado.get(pago.id_obligacion, 0) + pago.valor_pagado
    situaciones = []
    for o in estado.obligaciones:
        if o.tipo_tributo != tributo:
            continue
        abonado = pagado.get(o.id_obligacion, 0)
        saldo = o.valor_liquidado - abonado if o.estado_pago in ESTADOS_VIGENTES else 0
        situaciones.append(
            SituacionObligacion(
                obligacion=o,
                pagado=abonado,
                saldo=saldo,
                vencida=esta_vencida(o, saldo, hoy),
                descuento_vigente=descuento_vigente(o.fecha_limite_descuento, hoy),
            )
        )
    ids = {s.obligacion.id_obligacion for s in situaciones}
    vencidas = sum(s.vencida for s in situaciones)
    return CuentaTributo(
        tributo=tributo,
        obligaciones=tuple(situaciones),
        pagos=tuple(p for p in pagos if p.id_obligacion in ids),
        pendientes=sum(s.obligacion.estado_pago in ESTADOS_VIGENTES for s in situaciones),
        vencidas=vencidas,
        saldo=sum(s.saldo for s in situaciones),
        notas=(notas.NOTA_INTERESES_MORA,) if vencidas else (),
    )


def avaluo_para_estimar(
    anio: int, consultar: Callable[[int], int | None]
) -> tuple[int, int, str | None]:
    """Avalúo del año pedido o, si aún no se conoce, el del año anterior con su nota.

    `consultar(anio)` devuelve el avalúo de esa vigencia o `None`. Devuelve el avalúo, la vigencia
    usada y la nota (o `None`). Si tampoco hay avalúo del año anterior, falla.
    """
    valor = consultar(anio)
    if valor is not None:
        return valor, anio, None
    anterior = consultar(anio - 1)
    if anterior is None:
        raise LookupError(f"No hay avalúo del predio para {anio} ni para {anio - 1}.")
    return anterior, anio - 1, notas.nota_avaluo_anterior(anio, anio - 1)
