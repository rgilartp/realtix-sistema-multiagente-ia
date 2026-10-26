"""`nodo_general` simulado: aviso de sesión requerida, pregunta por la IA y fuera de alcance."""

from collections.abc import Callable
from typing import Any

from src.agents.dependencias import Dependencias
from src.agents.nodes._comun import parcial, ultimo_texto
from src.agents.state import AgentState

AVISO_SESION = (
    "Para consultar información de tu cuenta necesitas iniciar sesión en la Oficina Virtual "
    "Tributaria (entorno simulado de pruebas). Mientras tanto puedo resolver dudas generales."
)
RESPUESTA_IA = (
    "Soy un sistema de inteligencia artificial, no una persona. Si lo prefieres, puedo "
    "transferirte con un funcionario."
)
FUERA_DE_ALCANCE = "Ese tema no es tributario y queda fuera de lo que puedo atender en este canal."
GENERAL = "Información general de la plataforma (respuesta simulada)."


def crear_nodo_general(deps: Dependencias) -> Callable[[AgentState], dict[str, Any]]:
    def nodo_general(state: AgentState) -> dict[str, Any]:
        marcas = state.get("marcas", {})
        datos = dict(state.get("datos_extraidos", {}))
        if marcas.get("sesion_requerida"):
            respuesta = parcial("general", AVISO_SESION)
        elif marcas.get("pregunta_ia"):
            datos["oferta_transferencia"] = True
            respuesta = parcial("general", RESPUESTA_IA)
        elif state.get("categoria") == "fuera_de_alcance":
            respuesta = parcial("general", FUERA_DE_ALCANCE)
        else:
            _ = ultimo_texto(state)
            respuesta = parcial(
                "general",
                GENERAL,
                fuentes=("Glosario simulado (plataforma_general)",),
                similitud=0.85,
            )
        return {
            "respuestas_parciales": [*state.get("respuestas_parciales", []), respuesta],
            "datos_extraidos": datos,
        }

    return nodo_general
