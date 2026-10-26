"""Estado compartido del grafo (Tabla 3 de arquitectura) y su ciclo de vida (sección 3.1).

Los 14 campos de la Tabla 3 más tres auxiliares del turno (ADR-23): `marcas`, `respuesta_final`
y `categorias_descartadas`. Ciclo de vida:

- se conservan entre turnos (checkpointer): `messages`, `id_conversacion`, `datos_extraidos`,
  `resumen_caso` e `intentos_clasificacion`;
- los fija la capa de acceso en cada solicitud: `contribuyente_id` y `predios_autorizados`;
- el resto se reinicia en cada turno con `entrada_de_turno`.
"""

from typing import Annotated, Any, Literal, TypedDict

from langchain_core.messages import AnyMessage, HumanMessage
from langgraph.graph.message import add_messages

Categoria = Literal["ipu", "ica", "general", "ocr", "fuera_de_alcance"]
Suficiencia = Literal["completa", "parcial", "no_pudo", "aclaracion", "no_corresponde"]

CATEGORIAS: tuple[str, ...] = ("ipu", "ica", "general", "ocr", "fuera_de_alcance")
CAMPOS_DE_CONVERSACION = (
    "messages",
    "id_conversacion",
    "datos_extraidos",
    "resumen_caso",
    "intentos_clasificacion",
)
CAMPOS_DE_ACCESO = ("contribuyente_id", "predios_autorizados")
CAMPOS_DEL_TURNO = (
    "categoria",
    "nivel_confianza",
    "requiere_escalamiento",
    "categorias_pendientes",
    "respuestas_parciales",
    "motivo_escalamiento",
    "documento_adjunto",
    "marcas",
    "respuesta_final",
    "categorias_descartadas",
)


class AgentState(TypedDict, total=False):
    # Se conservan entre turnos
    messages: Annotated[list[AnyMessage], add_messages]
    id_conversacion: str
    datos_extraidos: dict[str, Any]
    resumen_caso: str
    intentos_clasificacion: int
    # Los fija la capa de acceso en cada solicitud
    contribuyente_id: str | None
    predios_autorizados: list[str]
    # Del turno
    categoria: str
    nivel_confianza: float
    requiere_escalamiento: bool
    categorias_pendientes: list[dict[str, str]]
    respuestas_parciales: list[dict[str, Any]]
    motivo_escalamiento: str | None
    documento_adjunto: dict[str, Any] | None
    # Auxiliares del turno (ADR-23)
    marcas: dict[str, Any]
    respuesta_final: str
    categorias_descartadas: list[str]


def entrada_de_turno(
    mensaje: str,
    id_conversacion: str,
    contribuyente_id: str | None = None,
    predios_autorizados: list[str] | None = None,
    documento_adjunto: dict[str, Any] | None = None,
) -> AgentState:
    """Entrada de cada turno: fija el acceso y reinicia los campos del turno.

    Al pasarla a `invoke` sobre el mismo `thread_id`, los campos de conversación se conservan
    (el checkpointer) y los del turno quedan en blanco, de modo que una bandera de escalamiento
    de un turno anterior no condicione el siguiente.
    """
    return {
        "messages": [HumanMessage(content=mensaje)],
        "id_conversacion": id_conversacion,
        "contribuyente_id": contribuyente_id,
        "predios_autorizados": list(predios_autorizados or []),
        "categoria": "",
        "nivel_confianza": 0.0,
        "requiere_escalamiento": False,
        "categorias_pendientes": [],
        "respuestas_parciales": [],
        "motivo_escalamiento": None,
        "documento_adjunto": documento_adjunto,
        "marcas": {},
        "respuesta_final": "",
        "categorias_descartadas": [],
    }
