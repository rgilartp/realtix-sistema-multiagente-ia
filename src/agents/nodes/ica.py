"""`nodo_ica`: agente del ICA con Haiku 5.5, herramientas y recuperación (RF-ICA-01 a 04).

La retención del ICA la marca el agente como fuera del MVP y la confianza escala (RF-ICA-04). Sin
modelos configurados, usa el agente simulado de B4.
"""

from collections.abc import Callable
from typing import Any

from langchain_core.runnables import RunnableConfig

from src.agents.agente import ConfigAgente, ejecutar_agente
from src.agents.dependencias import Dependencias
from src.agents.herramientas.ica import HERRAMIENTAS_ICA
from src.agents.nodes._comun import agregar_parcial
from src.agents.nodes.simulados import responder_ica
from src.agents.prompts import prompt_de_agente
from src.agents.state import AgentState

COLECCIONES = ("normativa_ica",)  # colecciones donde recupera el agente


def crear_nodo_ica(deps: Dependencias) -> Callable[..., dict[str, Any]]:
    agente = ConfigAgente("ica", prompt_de_agente("ica"), COLECCIONES, HERRAMIENTAS_ICA)

    def nodo_ica(state: AgentState, config: RunnableConfig) -> dict[str, Any]:
        if deps.modelos is None:
            respuesta, datos = responder_ica(deps, state), dict(state.get("datos_extraidos", {}))
        else:
            respuesta, datos = ejecutar_agente(agente, deps, state, config)
        return {
            "respuestas_parciales": agregar_parcial(state, respuesta),
            "datos_extraidos": datos,
        }

    return nodo_ica
