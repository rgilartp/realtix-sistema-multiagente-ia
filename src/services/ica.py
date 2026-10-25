"""Tarifa del impuesto de industria y comercio (ICA) por periodo.

`buscar_tarifa_ica` es la única implementación de la búsqueda de tarifa (generador, tabla
`tarifa_ica` de la base y, en B5, la estimación). Aplica el parágrafo del art. 21 del Acuerdo 1084
de 2026: los declarantes bimestrales usan `ica_2027.yaml` desde el bimestre 6 de 2026 y los anuales
desde el año gravable 2027.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Literal

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
        return TarifaICA(ciiu, fila["actividad"], Decimal(fila["tarifa_por_mil"]), tabla, fuente)
    if tabla == 2027:
        fila = _buscar(datos.get("progresiva_financiera", []), ciiu)
        if fila is not None:
            tarifa = Decimal(fila[_columna_progresiva(periodo.anio)])
            return TarifaICA(ciiu, fila["actividad"], tarifa, tabla, fuente)
    raise ActividadNoReconocidaError(ciiu)


def actividades_de_la_tabla(anio: int) -> list[TarifaICA]:
    """Todas las actividades de la tabla de 2026 (año gravable), para cargar `tarifa_ica`."""
    datos = cargar_datos(f"tarifas/ica_{anio}.yaml", anio, "tarifas del ICA")
    fuente = str(datos["fuente"])
    return [
        TarifaICA(f["ciiu"], f["actividad"], Decimal(f["tarifa_por_mil"]), anio, fuente)
        for f in datos["por_actividad"]
    ]
