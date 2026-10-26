"""`nodo_general`: aviso de sesión, pregunta por la IA, lo no tributario y dudas transversales.

El aviso de sesión requerida (RF-AUT-04), la respuesta a la pregunta por la IA (RF-SYS-06, que
ofrece el escalamiento) y lo no tributario (RF-GEN-04) son textos fijos, sin modelo. Las dudas
transversales (glosario, uso de la OVT simulada, datos personales) van a Haiku 5.5 con los
fragmentos de `plataforma_general` y `normativa_datos` (RF-GEN-01 a 03).
"""

from collections.abc import Callable
from typing import Any

from langchain_core.runnables import RunnableConfig

from src.agents.agente import ConfigAgente, ejecutar_agente
from src.agents.dependencias import Dependencias
from src.agents.nodes._comun import agregar_parcial, parcial
from src.agents.nodes.simulados import GENERAL
from src.agents.prompts import prompt_de_agente
from src.agents.state import AgentState

AVISO_SESION = (
    "Para consultar información de tu cuenta necesitas iniciar sesión en la Oficina Virtual "
    "Tributaria (entorno simulado de pruebas). Mientras tanto puedo resolver dudas generales."
)
RESPUESTA_IA = (
    "Soy un sistema de inteligencia artificial, no una persona. Si lo prefieres, puedo "
    "transferirte con un funcionario."
)
ALCANCE = (
    "Puedo ayudarte con el impuesto predial unificado y el impuesto de industria y comercio de "
    "Bogotá, y con el uso de la Oficina Virtual Tributaria (entorno simulado de pruebas)."
)
FUERA_DE_ALCANCE = (
    f"Ese tema no es tributario y queda fuera de lo que puedo atender en este canal. {ALCANCE}"
)
FUERA_DEL_CANAL = f"Esa consulta queda fuera de lo que puedo atender en este canal. {ALCANCE}"


COLECCIONES = ("plataforma_general", "normativa_datos")  # colecciones donde recupera el agente


def crear_nodo_general(deps: Dependencias) -> Callable[..., dict[str, Any]]:
    agente = ConfigAgente("general", prompt_de_agente("general"), COLECCIONES)

    def nodo_general(state: AgentState, config: RunnableConfig) -> dict[str, Any]:
        marcas = state.get("marcas", {})
        datos = dict(state.get("datos_extraidos", {}))
        if marcas.get("sesion_requerida"):
            respuesta = parcial("general", AVISO_SESION)
        elif marcas.get("pregunta_ia"):
            datos["oferta_transferencia"] = True
            respuesta = parcial("general", RESPUESTA_IA)
        elif state.get("categoria") == "fuera_de_alcance":
            no_tributario = marcas.get("no_tributario")
            respuesta = parcial("general", FUERA_DE_ALCANCE if no_tributario else FUERA_DEL_CANAL)
        elif deps.modelos is None:
            respuesta = parcial(
                "general",
                GENERAL,
                fuentes=("Glosario simulado (plataforma_general)",),
                similitud=0.85,
            )
        else:
            respuesta, datos = ejecutar_agente(agente, deps, state, config)
        return {
            "respuestas_parciales": agregar_parcial(state, respuesta),
            "datos_extraidos": datos,
        }

    return nodo_general
