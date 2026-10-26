"""`nodo_ipu`: agente del predial con Haiku 5.5, herramientas y recuperación (RF-IPU-01 a 05).

Sin lógica tributaria: las cifras salen de los servicios y del adaptador por las herramientas, y las
reglas, de los fragmentos de normas. Sin modelos configurados, usa el agente simulado de B4.
"""

from collections.abc import Callable
from typing import Any

from langchain_core.runnables import RunnableConfig

from src.agents.agente import ConfigAgente, ejecutar_agente
from src.agents.dependencias import Dependencias
from src.agents.herramientas.ipu import HERRAMIENTAS_IPU
from src.agents.nodes._comun import agregar_parcial
from src.agents.nodes.simulados import responder_ipu
from src.agents.prompts import prompt_de_agente
from src.agents.state import AgentState


def crear_nodo_ipu(deps: Dependencias) -> Callable[..., dict[str, Any]]:
    agente = ConfigAgente("ipu", prompt_de_agente("ipu"), ("normativa_ipu",), HERRAMIENTAS_IPU)

    def nodo_ipu(state: AgentState, config: RunnableConfig) -> dict[str, Any]:
        if deps.modelos is None:
            respuesta, datos = responder_ipu(deps, state)
        else:
            respuesta, datos = ejecutar_agente(agente, deps, state, config)
        return {
            "respuestas_parciales": agregar_parcial(state, respuesta),
            "datos_extraidos": datos,
        }

    return nodo_ipu
