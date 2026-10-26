"""Tarifa del impuesto de industria y comercio (ICA) por periodo.

`buscar_tarifa_ica` es la única implementación de la búsqueda de tarifa (generador, tabla
`tarifa_ica` de la base y, en B5, la estimación). Aplica el parágrafo del art. 21 del Acuerdo 1084
de 2026: los declarantes bimestrales usan `ica_2027.yaml` desde el bimestre 6 de 2026 y los anuales
desde el año gravable 2027. `estimar_ica` (B5) calcula el impuesto de un periodo con esa tarifa.
"""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Literal

from src.services import notas
from src.services.datos_anuales import cargar_datos
from src.services.errores import ActividadNoReconocidaError, AnioSinDatosError

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
    avisos = [notas.NOTA_ESTIMACION, notas.NOTA_APROXIMACION_ICA, notas.NOTA_COMPLEMENTARIOS_ICA]
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
