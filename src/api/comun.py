"""Dependencias comunes de los puntos de acceso: servicios, sesión y modo de evaluación."""

from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request

from src.api.acceso import Sesion, resolver_sesion
from src.api.esquemas import RespuestaChat
from src.api.evaluacion import EvaluacionTurno, leer_evaluacion
from src.api.servicios import ServiciosAPI
from src.api.turno import ConversacionAjenaError, SolicitudTurno, procesar_turno

MENSAJE_CONVERSACION_AJENA = (
    "Esta conversación pertenece a otra sesión. Abre una conversación nueva para continuar."
)


def obtener_servicios(request: Request) -> ServiciosAPI:
    return request.app.state.servicios


Servicios = Annotated[ServiciosAPI, Depends(obtener_servicios)]


def obtener_sesion(
    servicios: Servicios, authorization: Annotated[str | None, Header()] = None
) -> Sesion | None:
    return resolver_sesion(
        authorization,
        servicios.settings.ovt_hmac_secret,
        servicios.adaptador,
        servicios.nombre_de,
        servicios.settings.timeout_adaptador_s,
    )


def obtener_evaluacion(
    servicios: Servicios,
    x_reloj_simulado: Annotated[str | None, Header()] = None,
    x_escenario_id: Annotated[str | None, Header()] = None,
    x_falla_inyectada: Annotated[str | None, Header()] = None,
) -> EvaluacionTurno:
    return leer_evaluacion(servicios.settings, x_reloj_simulado, x_escenario_id, x_falla_inyectada)


SesionOpcional = Annotated[Sesion | None, Depends(obtener_sesion)]
Evaluacion = Annotated[EvaluacionTurno, Depends(obtener_evaluacion)]


def exigir_sesion(sesion: SesionOpcional) -> Sesion:
    if sesion is None:
        raise HTTPException(
            status_code=401,
            detail="Para consultar tu cuenta necesitas iniciar sesión en la OVT simulada.",
        )
    return sesion


SesionObligatoria = Annotated[Sesion, Depends(exigir_sesion)]


def turno(servicios: ServiciosAPI, solicitud: SolicitudTurno) -> RespuestaChat:
    """`procesar_turno` con la conversación ajena convertida en 403."""
    try:
        return procesar_turno(servicios, solicitud)
    except ConversacionAjenaError:
        raise HTTPException(status_code=403, detail=MENSAJE_CONVERSACION_AJENA) from None
