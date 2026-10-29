"""Régimen y fechas de declaración del ICA y fechas del predial, por año gravable.

Lee `datos/`; si falta el año o el valor, falla de forma explícita y no estima (ADR-06).
"""

from dataclasses import dataclass
from datetime import date
from typing import Any, Literal

from src.data.models import RegimenICA
from src.services.datos_anuales import (
    calendario,
    cargar_datos,
    regimen_ica_del_anio,
    umbral_ica_pesos,
)

Periodicidad = Literal["anual", "bimestral"]


@dataclass(frozen=True)
class ReglaICA:
    """Régimen del contribuyente y la regla del año; el umbral en pesos puede no estar publicado."""

    anio: int
    regimen: RegimenICA | None  # None: en 2027 el régimen depende del impuesto del año anterior
    periodicidad: Periodicidad | None
    umbral_uvt: int
    regla: str
    primer_ano_preferencial: bool
    sin_declaracion_ingresos_uvt: int | None
    fuente: str

    def umbral_en_pesos(self) -> int:
        """Umbral de 391 UVT en pesos; falla con `DatoNoPublicadoError` si la UVT no se publica."""
        return umbral_ica_pesos(self.anio)


def _periodicidad(regimen: RegimenICA) -> Periodicidad:
    return "bimestral" if regimen == "comun_bimestral" else "anual"


def regimen_ica(
    anio: int,
    regimen_registrado: RegimenICA | None,
    impuesto_a_cargo_anterior: int | None = None,
) -> ReglaICA:
    """Régimen del ICA del año gravable.

    El preferencial no se deduce del impuesto: viene registrado (`regimen_ica` de la base). En 2026
    el común se parte con el umbral de 391 UVT (en pesos, con la UVT de `datos/`) si se da el
    impuesto a cargo de 2025.
    En 2027 devuelve la regla en UVT del art. 26 del Acuerdo 1084; solo la conversión a pesos falla.
    """
    fila = regimen_ica_del_anio(anio)
    fuente = str(fila["fuente"])
    umbral_uvt = int(fila["umbral_uvt"])
    if anio >= 2027:
        sin = fila.get("sin_declaracion", {}).get("ingresos_netos_menores_a_uvt")
        regla = (
            f"Común si el impuesto a cargo del año anterior supera {umbral_uvt} UVT (declara y "
            f"paga cada dos meses); preferencial hasta {umbral_uvt} UVT (declara una vez al "
            "año). Quien empieza actividades queda el primer año en el preferencial."
        )
        return ReglaICA(
            anio=anio,
            regimen=regimen_registrado,
            periodicidad=_periodicidad(regimen_registrado) if regimen_registrado else None,
            umbral_uvt=umbral_uvt,
            regla=regla,
            primer_ano_preferencial=True,
            sin_declaracion_ingresos_uvt=int(sin) if sin else None,
            fuente=fuente,
        )
    regimen = regimen_registrado
    if regimen != "preferencial" and impuesto_a_cargo_anterior is not None:
        mayor = impuesto_a_cargo_anterior > umbral_ica_pesos(anio)
        regimen = "comun_bimestral" if mayor else "comun_anual"
    if regimen is None:
        raise ValueError("Falta el régimen registrado o el impuesto a cargo del año anterior.")
    regla = str(fila[regimen])
    return ReglaICA(
        anio=anio,
        regimen=regimen,
        periodicidad=_periodicidad(regimen),
        umbral_uvt=umbral_uvt,
        regla=regla,
        primer_ano_preferencial=False,
        sin_declaracion_ingresos_uvt=None,
        fuente=fuente,
    )


def regimenes_posibles(anio: int, periodicidad: Periodicidad | None) -> list[RegimenICA | None]:
    """Regímenes del año que corresponden a una periodicidad, según `regimenes_ica.yaml`.

    En 2026, «bimestral» es el común bimestral y «anual», el común anual o el preferencial (los dos
    declaran una vez al año). Si el año trae solo la regla general (2027), devuelve `[None]`.
    """
    fila = regimen_ica_del_anio(anio)
    regimenes: list[RegimenICA] = ["comun_bimestral", "comun_anual", "preferencial"]
    if not all(r in fila for r in regimenes):
        return [None]
    return [r for r in regimenes if periodicidad is None or _periodicidad(r) == periodicidad]


def fechas_ica(anio: int, periodicidad: Periodicidad) -> list[str]:
    """Fechas límite (ISO) de la declaración del ICA del año; `AnioSinDatosError` si no hay."""
    plazos = calendario(anio)
    concepto = (
        "ica_bimestral_comun_mayor_391_uvt"
        if periodicidad == "bimestral"
        else "ica_anual_comun_hasta_391_uvt_y_preferencial"
    )
    return list(plazos[concepto])


def fechas_predial(anio: int) -> dict[str, Any]:
    """Fechas del predial del año: descuento, sin descuento, facturas y SPAC."""
    plazos = calendario(anio)
    return {
        "pronto_pago": plazos["predial_pronto_pago_10"][0],
        "sin_descuento": plazos["predial_sin_descuento"][0],
        "facturas_a_mas_tardar": plazos["predial_facturas_expedidas_a_mas_tardar"][0],
        "spac_declaracion_inicial": plazos["spac_declaracion_inicial"][0],
        "spac_cuotas": list(plazos["spac_cuotas"]),
    }


def fuente_del_calendario(anio: int) -> str:
    """Norma de la que salen los plazos del año (p. ej. la Resolución SDH-000195 de 2025)."""
    return str(cargar_datos(f"calendario/{anio}.yaml", anio, "calendario")["fuente"])


def dias_hasta(fecha: date | str, hoy: date) -> int:
    """Días que faltan desde hoy hasta la fecha (0 si es hoy; negativo si ya pasó). Lo calcula el
    código para que el modelo no diga «mañana» o «en una semana» por su cuenta (G4 de la corrida
    2)."""
    destino = date.fromisoformat(fecha) if isinstance(fecha, str) else fecha
    return (destino - hoy).days


def respecto_a_hoy(fecha: date | str, hoy: date) -> str:
    """La fecha con relación a hoy, lista para copiar: «hoy», «mañana», «en N días» o «hace N
    días». El modelo la copia tal cual en lugar de hacer la cuenta (G4 de la corrida 2)."""
    dias = dias_hasta(fecha, hoy)
    if dias == 0:
        return "hoy"
    if dias == 1:
        return "mañana"
    if dias > 1:
        return f"en {dias} días"
    return "hace 1 día" if dias == -1 else f"hace {-dias} días"
