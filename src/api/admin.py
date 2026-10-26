"""`/admin/metricas` y `/health` (Tabla 8; RF-OBS-02 y RF-OBS-03)."""

from typing import Annotated, Any

from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse

from src.agents.state import CATEGORIAS
from src.api.acceso import exigir_rol
from src.api.comun import Servicios
from src.services.metricas import calcular_metricas

router = APIRouter(tags=["administración"])


@router.get("/api/v1/admin/metricas")
def metricas(
    servicios: Servicios, authorization: Annotated[str | None, Header()] = None
) -> dict[str, Any]:
    exigir_rol(authorization, servicios.settings.token_admin)
    return calcular_metricas(
        servicios.almacen.todas_las_interacciones(), servicios.etiquetas, CATEGORIAS
    )


@router.get("/health")
def salud(servicios: Servicios) -> JSONResponse:
    """Estado del servicio y de sus dependencias, sin detalles de configuración ni secretos."""
    dependencias: dict[str, str] = {}
    for nombre, comprobar in servicios.salud.items():
        try:
            comprobar()
            dependencias[nombre] = "ok"
        except Exception:
            dependencias[nombre] = "falla"
    sano = all(v == "ok" for v in dependencias.values())
    cuerpo = {
        "estado": "ok" if sano else "degradado",
        "version": servicios.version,
        "dependencias": dependencias,
    }
    return JSONResponse(cuerpo, status_code=200 if sano else 503)
