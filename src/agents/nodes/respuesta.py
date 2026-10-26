"""`nodo_respuesta` simulado: consolida las respuestas parciales con una plantilla (ADR-03)."""

from collections.abc import Callable
from typing import Any

from langchain_core.messages import AIMessage

from src.agents.dependencias import Dependencias
from src.agents.state import AgentState

ETIQUETAS = {"ipu": "Predial", "ica": "Industria y comercio", "ocr": "Recibo", "general": "General"}


def crear_nodo_respuesta(deps: Dependencias) -> Callable[[AgentState], dict[str, Any]]:
    def nodo_respuesta(state: AgentState) -> dict[str, Any]:
        parciales = [p for p in state.get("respuestas_parciales", []) if p["texto"]]
        if len(parciales) == 1:
            texto = parciales[0]["texto"]
        else:
            texto = "\n\n".join(
                f"{ETIQUETAS.get(p['categoria'], p['categoria'])}: {p['texto']}" for p in parciales
            )
        return {"respuesta_final": texto, "messages": [AIMessage(content=texto)]}

    return nodo_respuesta
