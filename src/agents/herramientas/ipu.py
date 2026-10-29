"""Herramientas del agente del predial: predios, estado de cuenta, estimación y plazos.

Solo el impuesto predial: el estado de cuenta de un predio también trae el ICA, y aquí se filtra
(`obligaciones.de_tributo`), para que el saldo del predial no incluya lo del ICA.
"""

from contextlib import suppress
from typing import Any

from src.agents.herramientas import (
    ANIO,
    FUENTE_REALSIT,
    MATRICULA_OPCIONAL,
    Contexto,
    FaltaDatoError,
    Herramienta,
    Resultado,
    cuenta_tributo,
    entero,
    exigir_sesion,
    fecha,
    pesos,
    por_mil,
    resolver_matricula,
)
from src.services import obligaciones
from src.services.calendario_tributario import fechas_predial, fuente_del_calendario
from src.services.datos_anuales import porcentaje_pronto_pago
from src.services.errores import AnioSinDatosError
from src.services.minimizacion import minimizar
from src.services.obligaciones import SituacionObligacion
from src.services.predial import RangoIPU, liquidar_predial, tabla_tarifas_ipu


def _obligacion(s: SituacionObligacion) -> dict[str, Any]:
    o = minimizar(s.obligacion)
    return {
        "vigencia_fiscal": o["vigencia_fiscal"],
        "avaluo_base": pesos(s.obligacion.base_gravable),
        "tarifa": por_mil(s.obligacion.tarifa_por_mil),
        "valor_liquidado": pesos(s.obligacion.valor_liquidado),
        "descuento_pronto_pago": pesos(s.obligacion.descuento_pronto_pago),
        "fecha_limite_descuento": fecha(s.obligacion.fecha_limite_descuento),
        "descuento_aun_vigente": s.descuento_vigente,
        "fecha_limite_pago": fecha(s.obligacion.fecha_limite_pago),
        "estado_pago": o["estado_pago"],
        "vencida_a_hoy": s.vencida,
        "pagado": pesos(s.pagado),
        "saldo": pesos(s.saldo),
        "en_spac": o["en_spac"],
    }


def _mis_predios(contexto: Contexto, argumentos: dict[str, Any]) -> Resultado:
    cid = exigir_sesion(contexto)
    predios = contexto.llamar(lambda: contexto.adaptador.get_predios_contribuyente(cid))
    datos = [
        {
            "matricula_catastral": p.matricula_catastral,
            "destino": p.destino,
            "estrato": p.estrato,
            "avaluo_catastral": pesos(p.avaluo_catastral),
        }
        for p in predios
    ]
    return Resultado({"predios": datos}, fuentes=(FUENTE_REALSIT,))


def _estado_cuenta(contexto: Contexto, argumentos: dict[str, Any]) -> Resultado:
    matricula = resolver_matricula(contexto, argumentos)
    cuenta = cuenta_tributo(contexto, matricula, "IPU")
    vigencias = {
        s.obligacion.id_obligacion: s.obligacion.vigencia_fiscal for s in cuenta.obligaciones
    }
    datos = {
        "matricula_catastral": matricula,
        "tributo": "impuesto predial unificado",
        "fecha_de_hoy": fecha(contexto.hoy),
        "obligaciones_pendientes_o_vencidas": cuenta.pendientes,
        "obligaciones_vencidas_a_hoy": cuenta.vencidas,
        "saldo_pendiente_predial": pesos(cuenta.saldo),
        "obligaciones": [_obligacion(s) for s in cuenta.obligaciones],
        "pagos": [
            {
                "vigencia_fiscal": vigencias[p.id_obligacion],
                "fecha_pago": fecha(p.fecha_pago),
                "valor_pagado": pesos(p.valor_pagado),
                "medio_pago": p.medio_pago,
            }
            for p in cuenta.pagos
        ],
    }
    return Resultado(datos, fuentes=(FUENTE_REALSIT,), notas=cuenta.notas)


def _estimar(contexto: Contexto, argumentos: dict[str, Any]) -> Resultado:
    anio = entero(argumentos, "anio") or contexto.hoy.year
    avaluo = entero(argumentos, "avaluo")
    fuentes: list[str] = []
    avisos: list[str] = []
    situacion: dict[str, Any] | None = None
    vigencia_avaluo = anio
    if avaluo is None:  # predio de la sesión
        matricula = resolver_matricula(contexto, argumentos)
        cid = exigir_sesion(contexto)
        predios = contexto.llamar(lambda: contexto.adaptador.get_predios_contribuyente(cid))
        predio = next((p for p in predios if p.matricula_catastral == matricula), None)
        if predio is None:  # ajeno o inexistente: el adaptador rechaza con el mensaje único
            contexto.llamar(lambda: contexto.adaptador.get_avaluo_catastral(matricula, cid))
            raise FaltaDatoError("El predio no está asociado a la sesión.")
        destino, estrato = predio.destino, predio.estrato

        def consultar(vigencia: int) -> int | None:
            try:
                return contexto.llamar(
                    lambda: contexto.adaptador.get_avaluo_catastral(matricula, cid, vigencia)
                ).avaluo_catastral
            except LookupError:
                return None

        avaluo, vigencia_avaluo, nota = obligaciones.avaluo_para_estimar(anio, consultar)
        if nota:
            avisos.append(nota)
        cuenta = cuenta_tributo(contexto, matricula, "IPU")
        del_anio = [s for s in cuenta.obligaciones if s.obligacion.vigencia_fiscal == anio]
        if del_anio:
            s = del_anio[0]
            situacion = {
                "estado_pago": s.obligacion.estado_pago,
                "vencida_a_hoy": s.vencida,
                "fecha_limite_pago": fecha(s.obligacion.fecha_limite_pago),
                "saldo": pesos(s.saldo),
            }
            if s.vencida:
                avisos.extend(cuenta.notas)
        fuentes.append(FUENTE_REALSIT)
    else:
        destino = str(argumentos.get("destino") or "")
        estrato = entero(argumentos, "estrato")
        if destino not in ("residencial", "comercial", "lote"):
            raise FaltaDatoError("Falta el destino del predio: residencial, comercial o lote.")
        if destino == "residencial" and estrato is None:
            raise FaltaDatoError("Falta el estrato del predio residencial.")
    liq = liquidar_predial(anio, destino, estrato, avaluo)  # type: ignore[arg-type]
    datos: dict[str, Any] = {
        "anio_gravable": anio,
        "fecha_de_hoy": fecha(contexto.hoy),
        "avaluo": pesos(avaluo),
        "vigencia_del_avaluo": vigencia_avaluo,
        "destino": destino,
        "estrato": estrato,
        "obligado_a_pagar": liq.tarifa.obligado,
        "tarifa": por_mil(liq.tarifa.tarifa_por_mil),
        "fuente_de_la_tarifa": liq.tarifa.fuente,
        "regla_de_la_tarifa": liq.tarifa.regla,
        "impuesto": pesos(liq.impuesto),
    }
    if liq.descuento is not None:
        datos |= {
            "porcentaje_descuento_pronto_pago": liq.porcentaje_descuento,
            "descuento": pesos(liq.descuento),
            "total_con_descuento": pesos(liq.total_con_descuento),
            "fecha_limite_descuento": fecha(liq.fecha_descuento),
            "descuento_aun_vigente": obligaciones.descuento_vigente(
                liq.fecha_descuento, contexto.hoy
            ),
            "fecha_limite_sin_descuento": fecha(liq.fecha_sin_descuento),
            "plazo_sin_descuento_ya_paso": not obligaciones.descuento_vigente(
                liq.fecha_sin_descuento, contexto.hoy
            ),
        }
    if liq.sobretasa is not None:
        datos["sobretasa_alumbrado"] = {
            "tarifa": por_mil(liq.sobretasa.tarifa_por_mil),
            "valor": pesos(liq.sobretasa.valor),
            "tope_aplicado": liq.sobretasa.tope_aplicado,
        }
        datos["total_estimado_impuesto_mas_sobretasa"] = pesos(liq.total_estimado)
    if situacion:
        datos["obligacion_registrada_del_anio"] = situacion
    return Resultado(datos, fuentes=(*liq.fuentes, *fuentes), notas=(*liq.notas, *avisos))


def _fechas(contexto: Contexto, argumentos: dict[str, Any]) -> Resultado:
    anio = entero(argumentos, "anio") or contexto.hoy.year
    plazos = fechas_predial(anio)
    hoy = contexto.hoy
    datos: dict[str, Any] = {
        "anio_gravable": anio,
        "fecha_de_hoy": fecha(hoy),
        "limite_pago_con_descuento": fecha(plazos["pronto_pago"]),
        "limite_pago_sin_descuento": fecha(plazos["sin_descuento"]),
        "facturas_expedidas_a_mas_tardar": fecha(plazos["facturas_a_mas_tardar"]),
        "spac_declaracion_inicial": fecha(plazos["spac_declaracion_inicial"]),
        "spac_cuotas": [fecha(f) for f in plazos["spac_cuotas"]],
        "descuento_aun_vigente": obligaciones.descuento_vigente(plazos["pronto_pago"], hoy),
        "plazo_sin_descuento_ya_paso": not obligaciones.descuento_vigente(
            plazos["sin_descuento"], hoy
        ),
    }
    with suppress(AnioSinDatosError):
        datos["porcentaje_descuento_pronto_pago"] = porcentaje_pronto_pago(anio)
    return Resultado(datos, fuentes=(fuente_del_calendario(anio),))


def _limite(valor: int, unidad: str) -> str:
    return (
        pesos(valor) or "" if unidad == "pesos" else f"{valor} SMMLV (aún no se publica en pesos)"
    )


def _filas(rangos: tuple[RangoIPU, ...]) -> list[dict[str, Any]]:
    return [
        {
            **({"estratos": list(r.estratos)} if r.estratos else {}),
            "avaluo_desde": ("más de " if r.desde_exclusivo else "") + _limite(r.desde, r.unidad),
            "avaluo_hasta": _limite(r.hasta, r.unidad) if r.hasta is not None else "en adelante",
            "tarifa": por_mil(r.tarifa_por_mil),
        }
        for r in rangos
    ]


def _tarifas(contexto: Contexto, argumentos: dict[str, Any]) -> Resultado:
    """Tabla de tarifas del año, sin sesión ni avalúo (F7 de la corrida 1)."""
    anio = entero(argumentos, "anio") or contexto.hoy.year
    destino = argumentos.get("destino") or "residencial"
    if destino not in ("residencial", "comercial", "lote"):
        raise FaltaDatoError(f"El destino «{destino}» no está entre residencial, comercial y lote.")
    tabla = tabla_tarifas_ipu(anio, destino)
    datos: dict[str, Any] = {"anio_gravable": anio, "destino": destino}
    fuentes = [tabla.fuente_generales]
    if tabla.preferenciales:
        datos["tarifas_preferenciales_estratos_1_a_3"] = {
            "aplica_a": tabla.aplica_preferenciales,
            "reemplazan_la_tabla_general": True,
            "rangos": _filas(tabla.preferenciales),
            "fuente": tabla.fuente_preferenciales,
        }
        fuentes.append(str(tabla.fuente_preferenciales))
    if tabla.exclusion:
        limite = _limite(tabla.exclusion.desde, tabla.exclusion.unidad)
        hasta = "hasta" if tabla.exclusion.desde_exclusivo else "inferior a"
        datos["exclusion"] = {
            "regla": f"Los predios residenciales de estratos 1 y 2 con avalúo {hasta} {limite} "
            "quedan excluidos del predial.",
            "fuente": tabla.fuente_exclusion,
        }
        fuentes.append(str(tabla.fuente_exclusion))
    datos["tarifas_por_rango_de_avaluo"] = {
        "rangos": _filas(tabla.generales),
        "fuente": tabla.fuente_generales,
    }
    return Resultado(datos, fuentes=tuple(dict.fromkeys(fuentes)), notas=tabla.notas)


HERRAMIENTAS_IPU: tuple[Herramienta, ...] = (
    Herramienta(
        "mis_predios",
        "Predios asociados a la sesión: matrícula, destino, estrato y avalúo catastral.",
        {},
        (),
        _mis_predios,
    ),
    Herramienta(
        "estado_cuenta_predial",
        "Obligaciones del impuesto predial de un predio de la sesión, por vigencia: valor, "
        "descuento, fecha límite, estado, si está vencida a la fecha de hoy, pagado y saldo; "
        "y los pagos registrados (incluidas las cuotas del SPAC). No incluye el ICA.",
        MATRICULA_OPCIONAL,
        (),
        _estado_cuenta,
    ),
    Herramienta(
        "estimar_predial",
        "Liquidación estimada del impuesto predial de un año gravable. Para un predio de la "
        "sesión, da la matrícula (o nada, si la sesión tiene un solo predio): la herramienta ya "
        "trae su destino, estrato y avalúo, y la situación de la obligación del año (si está "
        "vencida). Para un predio cualquiera, da el avalúo, el destino y, si es residencial, el "
        "estrato. No hace falta consultar antes los predios ni el estado de cuenta.",
        {
            **ANIO,
            **MATRICULA_OPCIONAL,
            "avaluo": {"type": "integer", "description": "Avalúo catastral en pesos."},
            "destino": {"type": "string", "enum": ["residencial", "comercial", "lote"]},
            "estrato": {"type": "integer", "description": "Estrato, de 1 a 6."},
        },
        ("anio",),
        _estimar,
    ),
    Herramienta(
        "tarifas_predial",
        "Tabla de tarifas del impuesto predial de un año gravable por destino, sin sesión ni "
        "avalúo: los rangos de avalúo en pesos con su tarifa por mil y, en el residencial, las "
        "tarifas preferenciales de los estratos 1 a 3 con sus límites en pesos (SMMLV del año) y "
        "la exclusión de los estratos 1 y 2. Para una tarifa, un rango o un umbral de un año.",
        {**ANIO, "destino": {"type": "string", "enum": ["residencial", "comercial", "lote"]}},
        ("anio",),
        _tarifas,
    ),
    Herramienta(
        "fechas_predial",
        "Plazos del impuesto predial de un año gravable: pago con descuento, sin descuento, "
        "expedición de facturas y SPAC (declaración inicial y cuotas).",
        ANIO,
        ("anio",),
        _fechas,
    ),
)
