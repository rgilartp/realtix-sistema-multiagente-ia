"""Chat: mensaje, documento y mensajes nuevos de la conversación (sección 3.8, Tabla 8).

`POST /chat/documento` recibe el recibo (RF-OCR-01): JPG, PNG o PDF de hasta
`TAMANO_MAXIMO_ARCHIVO_MB`, validado por sus primeros bytes y no solo por la extensión. Lo guarda
en un temporal, lo procesa en la misma solicitud y lo borra al terminar, pase lo que pase.
"""

import os
import tempfile
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, Path, Query, UploadFile
from fastapi.responses import JSONResponse
from langchain_core.messages import AIMessage, HumanMessage

from src.agents.graph import configuracion_de_hilo
from src.api.acceso import Sesion
from src.api.comun import MENSAJE_CONVERSACION_AJENA, Evaluacion, Servicios, SesionOpcional, turno
from src.api.esquemas import (
    AVISO_IA,
    PATRON_ID,
    MensajeConversacion,
    MensajesConversacion,
    Meta,
    RespuestaChat,
    SolicitudMensaje,
)
from src.api.turno import ConversacionAjenaError, SolicitudTurno, abrir_conversacion

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

# Firma de los primeros bytes de cada formato aceptado.
FIRMAS = {
    b"\xff\xd8\xff": ("image/jpeg", ".jpg"),
    b"\x89PNG\r\n\x1a\n": ("image/png", ".png"),
    b"%PDF-": ("application/pdf", ".pdf"),
}
MENSAJE_FORMATO = (
    "Solo puedo recibir el recibo en JPG, PNG o PDF. Intenta de nuevo con uno de esos formatos."
)
MENSAJE_TAMANO = "El archivo pesa más de {mb} MB. Envía una foto o un PDF más liviano del recibo."


def tipo_de_archivo(contenido: bytes) -> tuple[str, str] | None:
    """(tipo MIME, extensión) según la firma del archivo, o `None` si no es JPG, PNG ni PDF."""
    return next((v for firma, v in FIRMAS.items() if contenido.startswith(firma)), None)


@router.post("/mensaje", response_model=RespuestaChat)
def mensaje(
    solicitud: SolicitudMensaje,
    servicios: Servicios,
    sesion: SesionOpcional,
    evaluacion: Evaluacion,
) -> RespuestaChat:
    return turno(
        servicios,
        SolicitudTurno(solicitud.id_conversacion, solicitud.mensaje, sesion, evaluacion),
    )


@router.post("/documento", response_model=RespuestaChat)
def documento(
    servicios: Servicios,
    sesion: SesionOpcional,
    evaluacion: Evaluacion,
    archivo: Annotated[UploadFile, File()],
    id_conversacion: Annotated[str, Form(min_length=1, max_length=64, pattern=PATRON_ID)],
    mensaje: Annotated[str | None, Form(max_length=2000)] = None,
) -> RespuestaChat | JSONResponse:
    limite = servicios.settings.tamano_maximo_archivo_mb * 1024 * 1024
    contenido = archivo.file.read(limite + 1)

    def rechazo(codigo: int, texto: str) -> JSONResponse:
        """413 o 415 con el formato del chat; también abre la conversación y lleva el aviso de IA
        si es la primera respuesta (sección 3.8)."""
        nueva = False
        if isinstance(sesion, Sesion) or sesion is None:
            try:
                nueva = abrir_conversacion(servicios, id_conversacion, sesion)
            except ConversacionAjenaError:
                raise HTTPException(status_code=403, detail=MENSAJE_CONVERSACION_AJENA) from None
        cuerpo = RespuestaChat(
            id_conversacion=id_conversacion,
            respuesta=texto,
            aviso_ia=AVISO_IA if nueva else None,
            interlocutor="sistema",
            estado="aclaracion",
            meta=Meta(version=servicios.version),
        )
        return JSONResponse(cuerpo.model_dump(), status_code=codigo)

    if len(contenido) > limite:
        return rechazo(413, MENSAJE_TAMANO.format(mb=servicios.settings.tamano_maximo_archivo_mb))
    tipo = tipo_de_archivo(contenido)
    if tipo is None:
        return rechazo(415, MENSAJE_FORMATO)
    descriptor, ruta = tempfile.mkstemp(prefix="recibo-", suffix=tipo[1])
    try:
        with os.fdopen(descriptor, "wb") as destino:
            destino.write(contenido)
        adjunto = {"ruta": ruta, "tipo": tipo[0], "tamano_bytes": len(contenido)}
        return turno(
            servicios,
            SolicitudTurno(
                id_conversacion,
                (mensaje or "").strip() or "Te envío mi recibo",
                sesion,
                evaluacion,
                documento_adjunto=adjunto,
            ),
        )
    finally:  # RF-OCR-01: el archivo no se conserva después de procesarlo
        if os.path.exists(ruta):
            os.remove(ruta)


@router.get("/{id_conversacion}/mensajes", response_model=MensajesConversacion)
def mensajes(
    id_conversacion: Annotated[str, Path(min_length=1, max_length=64, pattern=PATRON_ID)],
    servicios: Servicios,
    sesion: SesionOpcional,
    desde: Annotated[int, Query(ge=0)] = 0,
) -> MensajesConversacion:
    """Mensajes de la conversación desde el índice `desde` (el widget consulta los nuevos cuando la
    conversación está escalada). Una conversación con dueño solo la ve su contribuyente."""
    estado = servicios.almacen.estado_conversacion(id_conversacion)
    if estado is None:
        raise HTTPException(status_code=404, detail="No encontré esa conversación.")
    dueno = servicios.almacen.contribuyente_de_conversacion(id_conversacion)
    propia = isinstance(sesion, Sesion) and sesion.contribuyente_id == dueno
    if dueno is not None and not propia:
        raise HTTPException(status_code=403, detail="Esta conversación pertenece a otra sesión.")
    lista = historial(servicios, id_conversacion)
    return MensajesConversacion(
        id_conversacion=id_conversacion,
        estado=estado,
        mensajes=lista[desde:],
        siguiente=len(lista),
    )


def historial(servicios: Servicios, id_conversacion: str) -> list[MensajeConversacion]:
    """Mensajes del grafo (contribuyente y agente) y, después, los del caso escalado."""
    valores = servicios.grafo.get_state(configuracion_de_hilo(id_conversacion)).values
    filas: list[tuple[str, str]] = []
    for m in valores.get("messages", []):
        if isinstance(m, HumanMessage):
            filas.append(("contribuyente", str(m.content)))
        elif isinstance(m, AIMessage):
            filas.append(("agente", str(m.content)))
    caso = servicios.almacen.caso_de_conversacion(id_conversacion)
    if caso:
        filas += [
            (m["autor"], m["texto"]) for m in servicios.almacen.mensajes_del_caso(caso["id_caso"])
        ]
    return [MensajeConversacion(indice=i, autor=a, texto=t) for i, (a, t) in enumerate(filas)]  # type: ignore[arg-type]
