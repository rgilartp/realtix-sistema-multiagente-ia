"""Fábrica de modelos por nodo, con las reglas de la API de los modelos 5.5 (sección 3.2).

El modelo de cada nodo sale de la configuración (RF-SYS-04 y RNF-10): cambiar de modelo es cambiar
una variable de entorno. Reglas: sin `temperature`, `top_p` ni `top_k`; sin prefijo de respuesta; la
salida estructurada de Sonnet va por `json_schema` (no por `tool_choice`); los bloques de la
respuesta se leen por tipo y `stop_reason: "refusal"` se trata como falla del servicio.
"""

from typing import Any, Literal

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage

from src.config import Settings
from src.integrations.robustez import ServicioNoDisponibleError

NodoConModelo = Literal["orquestador", "ipu", "ica", "general", "ocr", "juez"]
NODOS: tuple[str, ...] = ("orquestador", "ipu", "ica", "general", "ocr", "juez")
# Pensamiento y esfuerzo por nodo (sección 3.2). Los demás nodos no usan modelo (ADR-03).
PARAMETROS: dict[str, dict[str, Any]] = {
    "orquestador": {"thinking": {"type": "between_tools"}, "reasoning_effort": "low"},
    "ipu": {"thinking": {"type": "disabled"}, "reasoning_effort": "medium"},
    "ica": {"thinking": {"type": "disabled"}, "reasoning_effort": "medium"},
    "general": {"thinking": {"type": "disabled"}, "reasoning_effort": "medium"},
    "ocr": {"thinking": {"type": "disabled"}, "reasoning_effort": "medium"},
    "juez": {"reasoning_effort": "medium"},
}


def nombre_del_modelo(nodo: str, settings: Settings) -> str:
    """Identificador del modelo del nodo, tomado de `MODELO_<NODO>`."""
    if nodo not in NODOS:
        raise ValueError(f"El nodo «{nodo}» no usa modelo (ADR-03).")
    return str(getattr(settings, f"modelo_{nodo}"))


def crear_modelo(nodo: str, settings: Settings, **extra: Any) -> ChatAnthropic:
    """Modelo del nodo con la clave explícita `REALTIX_ANTHROPIC_API_KEY`, tiempo y un reintento."""
    return ChatAnthropic(
        model=nombre_del_modelo(nodo, settings),
        api_key=settings.realtix_anthropic_api_key,
        timeout=settings.timeout_modelo_s,
        max_retries=1,
        **PARAMETROS[nodo],
        **extra,
    )


def texto_de_respuesta(mensaje: AIMessage) -> str:
    """Texto de la respuesta, leyendo los bloques por tipo; la negativa del modelo es una falla."""
    if mensaje.response_metadata.get("stop_reason") == "refusal":
        raise ServicioNoDisponibleError("modelo", RuntimeError("refusal"))
    contenido = mensaje.content
    if isinstance(contenido, str):
        return contenido
    return "".join(
        bloque.get("text", "")
        for bloque in contenido
        if isinstance(bloque, dict) and bloque.get("type") == "text"
    )
