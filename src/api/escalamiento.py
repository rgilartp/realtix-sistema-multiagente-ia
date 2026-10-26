"""Botón «Hablar con un funcionario» (ADR-18) y bandeja de solo lectura (sección 3.6).

El botón entra al grafo con la marca de solicitud explícita: el orquestador escala sin llamar al
modelo y solo `nodo_escalamiento` registra el caso. La bandeja exige el token de funcionario.
"""

from typing import Annotated, Any

from fastapi import APIRouter, Header, HTTPException

from src.api.acceso import exigir_rol
from src.api.chat import historial
from src.api.comun import Evaluacion, Servicios, SesionOpcional, turno
from src.api.esquemas import RespuestaChat, SolicitudEscalamiento
from src.api.turno import SolicitudTurno

router = APIRouter(prefix="/api/v1/escalamiento", tags=["escalamiento"])
TEXTO_DEL_BOTON = "Quiero hablar con un funcionario"
CAMPOS_DE_LA_LISTA = ("id_caso", "id_conversacion", "motivo", "categoria", "nivel_confianza",
                      "estado", "fecha_escalamiento")  # fmt: skip


@router.post("", response_model=RespuestaChat)
def escalar(
    solicitud: SolicitudEscalamiento,
    servicios: Servicios,
    sesion: SesionOpcional,
    evaluacion: Evaluacion,
) -> RespuestaChat:
    return turno(
        servicios,
        SolicitudTurno(
            solicitud.id_conversacion,
            TEXTO_DEL_BOTON,
            sesion,
            evaluacion,
            solicitud_explicita=True,
        ),
    )


@router.get("/casos")
def casos(
    servicios: Servicios, authorization: Annotated[str | None, Header()] = None
) -> list[dict[str, Any]]:
    exigir_rol(authorization, servicios.settings.token_funcionario)
    return [{k: c[k] for k in CAMPOS_DE_LA_LISTA} for c in servicios.almacen.listar_casos()]


@router.get("/casos/{id_caso}")
def caso(
    id_caso: str, servicios: Servicios, authorization: Annotated[str | None, Header()] = None
) -> dict[str, Any]:
    exigir_rol(authorization, servicios.settings.token_funcionario)
    fila = servicios.almacen.obtener_caso(id_caso)
    if fila is None:
        raise HTTPException(status_code=404, detail="No encontré ese caso.")
    return {
        **{k: fila[k] for k in CAMPOS_DE_LA_LISTA},
        "resumen": fila["resumen_texto"],
        "resumen_estructurado": fila["resumen_json"],
        "intentos": fila["intentos"],
        "mensajes": [m.model_dump() for m in historial(servicios, fila["id_conversacion"])],
    }
