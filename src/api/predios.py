"""Estado de cuenta e historial de pagos de un predio propio, con token (Tabla 8, RF-AUT-02).

Un predio ajeno y uno inexistente dan la misma respuesta y no revelan datos (OC-06). Lo que se
devuelve pasa por `minimizar`: matrícula, vigencias, valores y estados, sin nombre ni documento.
"""

from fastapi import APIRouter, HTTPException

from src.api.comun import Servicios, SesionObligatoria
from src.data.adapter import MENSAJE_PREDIO_INACCESIBLE, PredioInaccesibleError
from src.integrations.robustez import con_tiempo_y_reintento
from src.services.minimizacion import minimizar

router = APIRouter(prefix="/api/v1/predios", tags=["predios"])


def _consultar(servicios: Servicios, consulta):  # noqa: ANN001, ANN202
    try:
        return con_tiempo_y_reintento(
            consulta, servicios.settings.timeout_adaptador_s, servicio="adaptador"
        )
    except PredioInaccesibleError:
        raise HTTPException(status_code=404, detail=MENSAJE_PREDIO_INACCESIBLE) from None


@router.get("/{predio_id}/estado-cuenta")
def estado_cuenta(predio_id: str, servicios: Servicios, sesion: SesionObligatoria) -> dict:
    cuenta = _consultar(
        servicios,
        lambda: servicios.adaptador.get_estado_cuenta(predio_id, sesion.contribuyente_id),
    )
    return minimizar(cuenta)


@router.get("/{predio_id}/pagos")
def pagos(predio_id: str, servicios: Servicios, sesion: SesionObligatoria) -> dict:
    lista = _consultar(
        servicios,
        lambda: servicios.adaptador.get_historial_pagos(predio_id, sesion.contribuyente_id),
    )
    return {"matricula_catastral": predio_id, "pagos": minimizar(lista)}
