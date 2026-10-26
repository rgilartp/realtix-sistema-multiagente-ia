"""Herramientas del agente del ICA: situación propia, estimación, régimen y fechas.

La situación propia sale del estado de cuenta de los predios de la sesión, filtrada al ICA (las
obligaciones del ICA cuelgan del predio en RealSit). El régimen se deduce de la periodicidad de la
obligación registrada; no hay un método nuevo del adaptador.
"""

from typing import Any

from src.agents.herramientas import (
    ANIO,
    FUENTE_REALSIT,
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
from src.services.calendario_tributario import (
    fechas_ica,
    fuente_del_calendario,
    regimen_ica,
    regimenes_posibles,
)
from src.services.errores import DatoNoPublicadoError
from src.services.ica import EstimacionICA, PeriodoICA, estimar_ica, tabla_aplicable

PERIODICIDAD = {"type": "string", "enum": ["anual", "bimestral"]}


def _situacion(contexto: Contexto, argumentos: dict[str, Any]) -> Resultado:
    cid = exigir_sesion(contexto)
    if argumentos.get("matricula"):
        matriculas = [resolver_matricula(contexto, argumentos)]
    else:
        predios = contexto.llamar(lambda: contexto.adaptador.get_predios_contribuyente(cid))
        matriculas = [p.matricula_catastral for p in predios]
    filas: list[dict[str, Any]] = []
    pagos: list[dict[str, Any]] = []
    saldo = vencidas = 0
    avisos: list[str] = []
    for matricula in matriculas:
        cuenta = cuenta_tributo(contexto, matricula, "ICA")
        vigencias = {}
        for s in cuenta.obligaciones:
            o = s.obligacion
            vigencias[o.id_obligacion] = o.vigencia_fiscal
            filas.append(
                {
                    "vigencia_fiscal": o.vigencia_fiscal,
                    "periodicidad": o.periodicidad,
                    "ingresos_base": pesos(o.base_gravable),
                    "tarifa": por_mil(o.tarifa_por_mil),
                    "valor_liquidado": pesos(o.valor_liquidado),
                    "fecha_limite_pago": fecha(o.fecha_limite_pago),
                    "estado_pago": o.estado_pago,
                    "vencida_a_hoy": s.vencida,
                    "pagado": pesos(s.pagado),
                    "saldo": pesos(s.saldo),
                }
            )
        pagos += [
            {
                "vigencia_fiscal": vigencias[p.id_obligacion],
                "fecha_pago": fecha(p.fecha_pago),
                "valor_pagado": pesos(p.valor_pagado),
                "medio_pago": p.medio_pago,
            }
            for p in cuenta.pagos
        ]
        saldo += cuenta.saldo
        vencidas += cuenta.vencidas
        avisos += [n for n in cuenta.notas if n not in avisos]
    if not filas:
        return Resultado(
            {"sin_obligaciones_ica": "La sesión no tiene obligaciones del ICA registradas."},
            fuentes=(FUENTE_REALSIT,),
        )
    filas.sort(key=lambda f: -f["vigencia_fiscal"])
    datos = {
        "tributo": "impuesto de industria y comercio",
        "fecha_de_hoy": fecha(contexto.hoy),
        "periodicidad_registrada": filas[0]["periodicidad"],
        "obligaciones_vencidas_a_hoy": vencidas,
        "saldo_pendiente_ica": pesos(saldo),
        "obligaciones": filas,
        "pagos": pagos,
    }
    return Resultado(datos, fuentes=(FUENTE_REALSIT,), notas=tuple(avisos))


def _datos_estimacion(e: EstimacionICA, etiqueta: str) -> dict[str, Any]:
    return {
        "periodo": etiqueta,
        "ingresos": pesos(e.ingresos),
        "tarifa": por_mil(e.tarifa_por_mil),
        "impuesto": pesos(e.impuesto),
        "tarifa_si_cumple_condicion": por_mil(e.tarifa_condicionada),
        "impuesto_si_cumple_condicion": pesos(e.impuesto_condicionado),
        "condicion": e.condicion,
        "proyeccion_anual": e.proyeccion_anual,
        "fuente_de_la_tarifa": e.fuente,
    }


def _estimar(contexto: Contexto, argumentos: dict[str, Any]) -> Resultado:
    ciiu = str(argumentos.get("ciiu") or "").strip()
    ingresos = entero(argumentos, "ingresos")
    if not ciiu:
        raise FaltaDatoError("Falta el código CIIU de la actividad.")
    if ingresos is None:
        raise FaltaDatoError("Faltan los ingresos gravables del periodo.")
    anio = entero(argumentos, "anio") or contexto.hoy.year
    periodicidad = argumentos.get("periodicidad") or "anual"
    bimestre = entero(argumentos, "bimestre")
    if periodicidad == "bimestral" and bimestre is None:
        # Sin bimestre: un periodo por cada tabla de tarifas que rige en el año.
        periodos: dict[int, list[int]] = {}
        for b in range(1, 7):
            periodos.setdefault(tabla_aplicable(PeriodoICA(anio, "bimestral", b)), []).append(b)
        grupos = list(periodos.values())
    else:
        grupos = [[bimestre]] if bimestre else [[]]
    estimaciones = []
    for grupo in grupos:
        if periodicidad == "bimestral":
            periodo = PeriodoICA(anio, "bimestral", grupo[0])
            tramo = f"{grupo[0]} a {grupo[-1]}" if len(grupo) > 1 else str(grupo[0])
            etiqueta = f"{'bimestres' if len(grupo) > 1 else 'bimestre'} {tramo} de {anio}"
        else:
            periodo, etiqueta = PeriodoICA(anio), f"año gravable {anio}"
        estimaciones.append((estimar_ica(ciiu, ingresos, periodo), etiqueta))
    primera = estimaciones[0][0]
    datos = {
        "ciiu": ciiu,
        "actividad": primera.actividad,
        "periodicidad": periodicidad,
        "estimaciones": [_datos_estimacion(e, etiqueta) for e, etiqueta in estimaciones],
    }
    fuentes = tuple(dict.fromkeys(e.fuente for e, _ in estimaciones))
    notas = tuple(dict.fromkeys(n for e, _ in estimaciones for n in e.notas))
    return Resultado(datos, fuentes=fuentes, notas=notas)


def _regimen(contexto: Contexto, argumentos: dict[str, Any]) -> Resultado:
    anio = entero(argumentos, "anio") or contexto.hoy.year
    registrado = argumentos.get("regimen")
    candidatos = (
        [registrado] if registrado else regimenes_posibles(anio, argumentos.get("periodicidad"))
    )
    reglas = []
    for candidato in candidatos:
        regla = regimen_ica(anio, candidato)
        fila: dict[str, Any] = {
            "regimen": regla.regimen,
            "periodicidad": regla.periodicidad,
            "regla": regla.regla,
            "umbral_uvt": regla.umbral_uvt,
        }
        try:
            fila["umbral_en_pesos"] = pesos(regla.umbral_en_pesos())
        except DatoNoPublicadoError as error:
            fila["umbral_en_pesos"] = str(error)
        if regla.sin_declaracion_ingresos_uvt:
            fila["no_declaran_con_ingresos_menores_a_uvt"] = regla.sin_declaracion_ingresos_uvt
        reglas.append((fila, regla.fuente))
    datos = {"anio_gravable": anio, "reglas": [f for f, _ in reglas]}
    return Resultado(datos, fuentes=tuple(dict.fromkeys(f for _, f in reglas)))


def _fechas(contexto: Contexto, argumentos: dict[str, Any]) -> Resultado:
    anio = entero(argumentos, "anio") or contexto.hoy.year
    periodicidad = argumentos.get("periodicidad") or "anual"
    fechas = fechas_ica(anio, periodicidad)
    datos = {
        "anio_gravable": anio,
        "periodicidad": periodicidad,
        "fecha_de_hoy": fecha(contexto.hoy),
        "fechas_limite_declaracion": [
            {"fecha": fecha(f), "ya_paso": f < contexto.hoy.isoformat()} for f in fechas
        ],
    }
    return Resultado(datos, fuentes=(fuente_del_calendario(anio),))


HERRAMIENTAS_ICA: tuple[Herramienta, ...] = (
    Herramienta(
        "mi_situacion_ica",
        "Obligaciones del ICA del contribuyente de la sesión: periodicidad, ingresos, tarifa, "
        "valor, fecha límite, estado, si está vencida a la fecha de hoy, pagado, saldo y pagos.",
        {"matricula": {"type": "string", "description": "Opcional: solo ese predio."}},
        (),
        _situacion,
    ),
    Herramienta(
        "estimar_ica",
        "Estimación del ICA de un periodo con el código CIIU y los ingresos gravables del "
        "periodo. Si es bimestral y no se sabe el bimestre, se omite y la herramienta estima "
        "cada tramo del año con su tabla de tarifas.",
        {
            "ciiu": {"type": "string", "description": "Código CIIU de la actividad."},
            "ingresos": {"type": "integer", "description": "Ingresos gravables en pesos."},
            **ANIO,
            "periodicidad": PERIODICIDAD,
            "bimestre": {"type": "integer", "description": "Bimestre, de 1 a 6."},
        },
        ("ciiu", "ingresos", "anio", "periodicidad"),
        _estimar,
    ),
    Herramienta(
        "regimen_ica",
        "Régimen y periodicidad del ICA de un año gravable, con la regla y el umbral. Da la "
        "periodicidad de la obligación registrada si se conoce, o el régimen si el contribuyente "
        "lo dice.",
        {
            **ANIO,
            "periodicidad": PERIODICIDAD,
            "regimen": {
                "type": "string",
                "enum": ["comun_bimestral", "comun_anual", "preferencial"],
            },
        },
        ("anio",),
        _regimen,
    ),
    Herramienta(
        "fechas_ica",
        "Fechas límite de la declaración del ICA de un año gravable, por periodicidad.",
        {**ANIO, "periodicidad": PERIODICIDAD},
        ("anio", "periodicidad"),
        _fechas,
    ),
)
