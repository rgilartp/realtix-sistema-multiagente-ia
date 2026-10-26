"""Lector común de `datos/`: UVT, SMMLV, calendario y archivos de tarifas por año gravable."""

from functools import cache
from pathlib import Path
from typing import Any

import yaml

from src.services.errores import AnioSinDatosError, DatoNoPublicadoError

RAIZ_DATOS = Path(__file__).resolve().parent.parent.parent / "datos"


@cache
def _leer(ruta: Path) -> Any:
    return yaml.safe_load(ruta.read_text(encoding="utf-8"))


def cargar_datos(relativa: str, anio: int, que: str) -> dict[str, Any]:
    """Lee un YAML de `datos/`; si no existe, el año no tiene datos."""
    ruta = RAIZ_DATOS / relativa
    if not ruta.is_file():
        raise AnioSinDatosError(anio, que)
    return _leer(ruta)


def _valor_anual(clave: str, anio: int, nombre: str) -> int:
    datos = _leer(RAIZ_DATOS / "uvt_smmlv.yaml")
    for fila in datos[clave]:
        if fila["anio"] == anio:
            if not isinstance(fila["valor"], int):
                raise DatoNoPublicadoError(nombre, anio)
            return fila["valor"]
    raise AnioSinDatosError(anio, nombre)


def smmlv(anio: int) -> int:
    """SMMLV del año, en pesos. Falla si el año no existe o aún no se publica."""
    return _valor_anual("smmlv", anio, "SMMLV")


def uvt(anio: int) -> int:
    """UVT del año, en pesos. Falla si el año no existe o aún no se publica."""
    return _valor_anual("uvt", anio, "UVT")


def calendario(anio: int) -> dict[str, list[str]]:
    """Plazos del año gravable: concepto -> fechas ISO."""
    datos = cargar_datos(f"calendario/{anio}.yaml", anio, "calendario")
    return {p["concepto"]: p["fechas"] for p in datos["plazos"]}


def porcentaje_pronto_pago(anio: int) -> int:
    """Porcentaje de descuento por pronto pago del predial (Res. SDH-000195 de 2025, art. 6)."""
    datos = cargar_datos(f"calendario/{anio}.yaml", anio, "calendario")
    for plazo in datos["plazos"]:
        if plazo["concepto"] == "predial_pronto_pago_10":
            return int(plazo["porcentaje_descuento"])
    raise AnioSinDatosError(anio, "descuento por pronto pago")


def umbral_ica_pesos(anio: int) -> int:
    """Umbral de 391 UVT en pesos para el régimen del ICA del año gravable."""
    datos = _leer(RAIZ_DATOS / "regimenes_ica.yaml")
    for fila in datos["anios"]:
        if fila["anio_gravable"] == anio:
            if "umbral_pesos" not in fila:
                raise DatoNoPublicadoError("umbral del ICA en pesos", anio)
            return int(fila["umbral_pesos"])
    raise AnioSinDatosError(anio, "régimen del ICA")
