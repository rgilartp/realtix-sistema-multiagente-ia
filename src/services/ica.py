"""Tarifa del impuesto de industria y comercio (ICA) por periodo.

`buscar_tarifa_ica` es la única implementación de la búsqueda de tarifa (generador, tabla
`tarifa_ica` de la base y, en B5, la estimación). Aplica el parágrafo del art. 21 del Acuerdo 1084
de 2026: los declarantes bimestrales usan `ica_2027.yaml` desde el bimestre 6 de 2026 y los anuales
desde el año gravable 2027. `estimar_ica` (B5) calcula el impuesto de un periodo con esa tarifa.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Literal, cast

from src.services import notas
from src.services.datos_anuales import (
    cargar_datos,
    fuente_de_la_uvt,
    regimen_ica_del_anio,
    regla_bomberil_mas_reciente,
    uvt,
)
from src.services.errores import ActividadNoReconocidaError, AnioSinDatosError, DatoNoPublicadoError

Periodicidad = Literal["anual", "bimestral"]


@dataclass(frozen=True)
class PeriodoICA:
    """Periodo gravable: el año y, si es bimestral, el bimestre (1 a 6)."""

    anio: int
    periodicidad: Periodicidad = "anual"
    bimestre: int | None = None

    def __post_init__(self) -> None:
        if self.periodicidad == "bimestral" and self.bimestre not in range(1, 7):
            raise ValueError("Un periodo bimestral lleva el bimestre, de 1 a 6.")
        if self.periodicidad == "anual" and self.bimestre is not None:
            raise ValueError("Un periodo anual no lleva bimestre.")


@dataclass(frozen=True)
class TarifaICA:
    ciiu: str
    actividad: str
    tarifa_por_mil: Decimal
    tabla: int
    fuente: str
    tarifa_condicionada: Decimal | None = None  # p. ej. 58112 en 2026: 4,14 si cumple Acuerdo 98
    condicion: str | None = None


def periodicidad_registrada(
    obligaciones: Iterable[tuple[int, str]], anio: int
) -> tuple[Periodicidad, int] | None:
    """La periodicidad de las obligaciones del ICA registradas, como (periodicidad, vigencia): la
    del año pedido o, si no hay una de ese año, la de la vigencia más reciente; `None` sin
    obligaciones. Regla sin modelo (F4 y F8 de la corrida 1): con sesión, las fechas y la
    estimación usan la periodicidad del contribuyente, no las dos."""
    validas = sorted(((v, p) for v, p in obligaciones if p in ("anual", "bimestral")), reverse=True)
    if not validas:
        return None
    vigencia, periodicidad = next(((v, p) for v, p in validas if v == anio), validas[0])
    return cast(Periodicidad, periodicidad), vigencia


def tabla_aplicable(periodo: PeriodoICA) -> int:
    """Año de la tabla de tarifas (2026 o 2027) que rige para el periodo."""
    if periodo.anio < 2026:
        raise AnioSinDatosError(periodo.anio, "tarifas del ICA")
    if periodo.anio >= 2027:
        return 2027
    if periodo.periodicidad == "bimestral" and periodo.bimestre == 6:
        return 2027
    return 2026


def _columna_progresiva(anio: int) -> str:
    return "hasta_2027" if anio <= 2027 else ("en_2028" if anio == 2028 else "desde_2029")


def _buscar(filas: list[dict[str, Any]], ciiu: str) -> dict[str, Any] | None:
    return next((f for f in filas if f["ciiu"] == ciiu), None)


def buscar_tarifa_ica(ciiu: str, periodo: PeriodoICA) -> TarifaICA:
    """Tarifa por mil de la actividad (CIIU) para el periodo; no adivina actividades ausentes."""
    tabla = tabla_aplicable(periodo)
    datos = cargar_datos(f"tarifas/ica_{tabla}.yaml", tabla, "tarifas del ICA")
    fuente = str(datos["fuente"])
    fila = _buscar(datos["por_actividad"], ciiu)
    if fila is not None:
        condicionada = fila.get("tarifa_condicionada")
        return TarifaICA(
            ciiu,
            fila["actividad"],
            Decimal(fila["tarifa_por_mil"]),
            tabla,
            fuente,
            tarifa_condicionada=Decimal(condicionada["tarifa_por_mil"]) if condicionada else None,
            condicion=str(condicionada["condicion"]) if condicionada else None,
        )
    if tabla == 2027:
        fila = _buscar(datos.get("progresiva_financiera", []), ciiu)
        if fila is not None:
            tarifa = Decimal(fila[_columna_progresiva(periodo.anio)])
            return TarifaICA(ciiu, fila["actividad"], tarifa, tabla, fuente)
    raise ActividadNoReconocidaError(ciiu)


@dataclass(frozen=True)
class TarifaDelPeriodo:
    """Una tarifa de la consulta por año: la del año (`anual`, que en un año con dos tablas cubre
    también los bimestres 1 a 5), la del bimestre 6 si cambia en el año, o la del año siguiente."""

    aplica_a: Literal["anual", "bimestre_6", "anio_siguiente"]
    anio: int
    tarifa: TarifaICA


def tarifas_ica_del_anio(ciiu: str, anio: int) -> tuple[list[TarifaDelPeriodo], list[int]]:
    """Tarifas de una actividad para un año, sin ingresos (F7 de la corrida 1).

    La del año es obligatoria (`ActividadNoReconocidaError` si la tabla no tiene el código). Si la
    tabla cambia en el bimestre 6, también la de ese bimestre; si cambia el año siguiente y su
    tabla ya está publicada, la de ese año. Devuelve además las tablas (años) en las que el código
    no aparece, porque el Acuerdo 1084 de 2026 renumeró actividades: no se adivina la nueva."""
    anual = buscar_tarifa_ica(ciiu, PeriodoICA(anio))
    tarifas = [TarifaDelPeriodo("anual", anio, anual)]
    faltan: list[int] = []
    bimestre_6 = PeriodoICA(anio, "bimestral", 6)
    if tabla_aplicable(bimestre_6) != anual.tabla:
        try:
            tarifas.append(
                TarifaDelPeriodo("bimestre_6", anio, buscar_tarifa_ica(ciiu, bimestre_6))
            )
        except ActividadNoReconocidaError:
            faltan.append(tabla_aplicable(bimestre_6))
    try:
        siguiente = buscar_tarifa_ica(ciiu, PeriodoICA(anio + 1))
        if siguiente.tarifa_por_mil != anual.tarifa_por_mil:
            tarifas.append(TarifaDelPeriodo("anio_siguiente", anio + 1, siguiente))
    except ActividadNoReconocidaError:
        faltan.append(tabla_aplicable(PeriodoICA(anio + 1)))
    except AnioSinDatosError:
        pass
    return tarifas, sorted(set(faltan))


@dataclass(frozen=True)
class FilaTablaICA:
    ciiu: str
    actividad: str
    grupo: str | None
    tarifa_por_mil: Decimal
    vigencia: int
    fuente: str


def actividades_de_la_tabla(anio: int) -> list[FilaTablaICA]:
    """Todas las actividades de la tabla del año, con la fuente de cada tarifa."""
    datos = cargar_datos(f"tarifas/ica_{anio}.yaml", anio, "tarifas del ICA")
    general = str(datos["fuente"])
    return [
        FilaTablaICA(
            ciiu=f["ciiu"],
            actividad=f["actividad"],
            grupo=f.get("grupo_resolucion_265"),
            tarifa_por_mil=Decimal(f["tarifa_por_mil"]),
            vigencia=anio,
            fuente=str(f.get("fuente_tarifa") or general),
        )
        for f in datos["por_actividad"]
    ]


_UN_PESO = Decimal(1)


@dataclass(frozen=True)
class EstimacionICA:
    """Estimación del ICA de un periodo, con valores exactos y sus notas."""

    ciiu: str
    actividad: str
    periodo: PeriodoICA
    ingresos: int
    tarifa_por_mil: Decimal
    impuesto: int
    tarifa_condicionada: Decimal | None  # solo 58112 en 2026
    impuesto_condicionado: int | None
    condicion: str | None
    proyeccion_anual: bool
    fuente: str
    notas: tuple[str, ...]


def _impuesto(ingresos: int, tarifa_por_mil: Decimal) -> int:
    return int((Decimal(ingresos) * tarifa_por_mil / 1000).quantize(_UN_PESO, ROUND_HALF_UP))


def nota_sobretasa_bomberil(ingresos: int, periodo: PeriodoICA) -> str:
    """Si la sobretasa bomberil aplica, por código: los ingresos del periodo (bimestre o año) frente
    al umbral en UVT del año gravable (`regimenes_ica.yaml`, Res. SDH-000195 de 2025, art. 2)."""
    try:
        regla = regimen_ica_del_anio(periodo.anio).get("sobretasa_bomberil")
        valor_uvt = uvt(periodo.anio)
    except (AnioSinDatosError, DatoNoPublicadoError):
        regla = None
    if not regla:
        conocida = regla_bomberil_mas_reciente()
        return notas.nota_bomberil_sin_datos(
            periodo.anio,
            (conocida[0], int(conocida[1]["umbral_uvt"]), str(conocida[1]["fuente"]))
            if conocida
            else None,
        )
    umbral = int(regla["umbral_uvt"])
    datos = (
        umbral,
        umbral * valor_uvt,
        periodo.anio,
        regla["fuente"],
        fuente_de_la_uvt(periodo.anio),
    )
    if ingresos > umbral * valor_uvt:
        return notas.nota_bomberil_aplica(*datos)
    return notas.nota_bomberil_no_aplica(*datos)


def estimar_ica(ciiu: str, ingresos: int, periodo: PeriodoICA) -> EstimacionICA:
    """Estima el ICA de los `ingresos` gravables del periodo (RF-ICA-02).

    En 2026 usa la tabla de `ica_2026.yaml`; desde el bimestre 6 de 2026 (bimestrales) o 2027
    (anuales), la del art. 21 del Acuerdo 1084. Una actividad sin fila en la tabla del periodo falla
    con `ActividadNoReconocidaError`: nunca se asigna un código por parecido. El 58112 de 2026 da
    8 por mil y, si cumple el Acuerdo 98 de 2003, 4,14; el de 2027, 4 por mil sin condición.
    """
    if ingresos < 0:
        raise ValueError("Los ingresos no pueden ser negativos.")
    tarifa = buscar_tarifa_ica(ciiu, periodo)
    proyeccion = periodo.periodicidad == "anual" and periodo.anio == 2026
    avisos = [
        notas.NOTA_ESTIMACION,
        notas.NOTA_APROXIMACION_ICA,
        notas.NOTA_AVISOS_Y_TABLEROS,
        nota_sobretasa_bomberil(ingresos, periodo),
    ]
    if proyeccion:
        avisos.append(notas.NOTA_PROYECCION_ICA_ANUAL)
    condicionada = tarifa.tarifa_condicionada
    return EstimacionICA(
        ciiu=ciiu,
        actividad=tarifa.actividad,
        periodo=periodo,
        ingresos=ingresos,
        tarifa_por_mil=tarifa.tarifa_por_mil,
        impuesto=_impuesto(ingresos, tarifa.tarifa_por_mil),
        tarifa_condicionada=condicionada,
        impuesto_condicionado=_impuesto(ingresos, condicionada) if condicionada else None,
        condicion=tarifa.condicion,
        proyeccion_anual=proyeccion,
        fuente=tarifa.fuente,
        notas=tuple(avisos),
    )
