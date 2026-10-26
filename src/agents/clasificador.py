"""Clasificador del orquestador con Sonnet 5.5 y salida estructurada (RF-ORQ-01 y RF-ORQ-05).

Tiene la firma `Clasificador` de B4, así que `nodo_orquestador` no cambia. El modelo devuelve las
partes y las marcas en `json_schema` (Sonnet 5.5 no acepta `tool_choice` forzado); el código decide
lo que no le toca al modelo: la sesión requerida sale de «consulta personal» y de si hay sesión, y
un adjunto va siempre a `ocr`. Al modelo no llegan nombres, documentos ni identificadores: solo el
texto anonimizado y si hay sesión, sí o no (RNF-03).
"""

from collections.abc import Callable
from typing import Any, Literal

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, ConfigDict

from src.agents.dependencias import Clasificacion
from src.agents.prompts import cargar_prompt
from src.agents.state import AgentState
from src.integrations.modelos import texto_de_respuesta
from src.integrations.robustez import con_tiempo_y_reintento
from src.integrations.trazas import Anonimizador

TURNOS_PREVIOS = 4


class Parte(BaseModel):
    model_config = ConfigDict(extra="forbid")
    categoria: Literal["ipu", "ica", "general", "ocr", "fuera_de_alcance"]
    texto: str


class SalidaOrquestador(BaseModel):
    """Esquema de la salida; no pide razonamiento (la API puede rechazarlo, sección 3.2)."""

    model_config = ConfigDict(extra="forbid")
    partes: list[Parte]
    consulta_personal: bool
    solicitud_explicita: bool
    pregunta_ia: bool
    tributario_fuera_mvp: bool
    municipio_distinto: bool
    no_tributario: bool


def historial_anonimizado(
    state: AgentState, anonimizar: Callable[[str], str], turnos: int = TURNOS_PREVIOS
) -> str:
    """Los últimos mensajes anteriores al actual, anonimizados, para entender las referencias."""
    previos = list(state.get("messages", []))[:-1][-turnos:]
    lineas = []
    for mensaje in previos:
        quien = "Contribuyente" if isinstance(mensaje, HumanMessage) else "Asistente"
        lineas.append(f"{quien}: {anonimizar(str(mensaje.content))}")
    return "\n".join(lineas) or "(sin turnos anteriores)"


def _si_no(valor: object) -> str:
    return "sí" if valor else "no"


def mensajes_del_orquestador(
    texto: str, state: AgentState, anonimizar: Callable[[str], str]
) -> list[BaseMessage]:
    """Prompt del orquestador con el contexto mínimo del turno."""
    descartadas = ", ".join(state.get("categorias_descartadas", [])) or "ninguna"
    contexto = (
        f"Sesión iniciada: {_si_no(state.get('contribuyente_id'))}\n"
        f"Adjunto en este turno: {_si_no(state.get('documento_adjunto'))}\n"
        "En el turno anterior se ofreció transferir a un funcionario: "
        f"{_si_no(state.get('datos_extraidos', {}).get('oferta_transferencia'))}\n"
        f"Categorías descartadas para esta parte: {descartadas}\n\n"
        f"Conversación previa:\n{historial_anonimizado(state, anonimizar)}\n\n"
        f"Mensaje a clasificar:\n{anonimizar(texto)}"
    )
    return [SystemMessage(cargar_prompt("orquestador").texto), HumanMessage(contexto)]


def interpretar(salida: SalidaOrquestador, state: AgentState) -> Clasificacion:
    """Pasa la salida del modelo a partes y marcas, con las reglas que decide el código."""
    marcas: dict[str, Any] = {
        nombre: True
        for nombre in (
            "solicitud_explicita",
            "pregunta_ia",
            "tributario_fuera_mvp",
            "municipio_distinto",
            "no_tributario",
        )
        if getattr(salida, nombre)
    }
    partes = [p.model_dump() for p in salida.partes if p.texto.strip()]
    adjunto = state.get("documento_adjunto") is not None
    if adjunto and not any(p["categoria"] == "ocr" for p in partes):
        partes.insert(0, {"categoria": "ocr", "texto": partes[0]["texto"] if partes else ""})
    texto_completo = " ".join(p["texto"] for p in partes)
    if (salida.consulta_personal or adjunto) and not state.get("contribuyente_id"):
        marcas["sesion_requerida"] = True
        partes = [{"categoria": "general", "texto": texto_completo}]
    if marcas.get("pregunta_ia"):
        partes = [{"categoria": "general", "texto": texto_completo}]
    descartadas = state.get("categorias_descartadas", [])
    partes = [p for p in partes if p["categoria"] not in descartadas]
    return Clasificacion(partes or [{"categoria": "general", "texto": texto_completo}], marcas)


class ClasificadorLLM:
    """Clasificador con el modelo del orquestador; si falla, el nodo escala (RNF-08)."""

    def __init__(self, modelo: BaseChatModel, timeout_s: float) -> None:
        self._modelo = modelo.with_structured_output(
            SalidaOrquestador, method="json_schema", include_raw=True
        )
        self._timeout_s = timeout_s
        self._anonimizar = Anonimizador()

    def __call__(self, texto: str, state: AgentState) -> Clasificacion:
        mensajes = mensajes_del_orquestador(texto, state, self._anonimizar.texto)
        resultado = con_tiempo_y_reintento(
            lambda: self._modelo.invoke(mensajes), self._timeout_s, servicio="orquestador"
        )
        crudo: AIMessage = resultado["raw"]
        texto_de_respuesta(crudo)  # una negativa del modelo es una falla del servicio
        if resultado.get("parsing_error") or resultado.get("parsed") is None:
            raise ValueError("La salida del orquestador no cumple el esquema.")
        return interpretar(resultado["parsed"], state)
