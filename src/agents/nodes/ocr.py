"""`nodo_ocr` simulado: no lee imágenes; devuelve los campos del adjunto para confirmación."""

from collections.abc import Callable
from typing import Any

from src.agents.dependencias import Dependencias
from src.agents.nodes._comun import parcial
from src.agents.state import AgentState


def crear_nodo_ocr(deps: Dependencias) -> Callable[[AgentState], dict[str, Any]]:
    def nodo_ocr(state: AgentState) -> dict[str, Any]:
        adjunto = state.get("documento_adjunto")
        datos = dict(state.get("datos_extraidos", {}))
        if not adjunto:
            respuesta = parcial(
                "ocr", "Adjunta el recibo que quieres revisar.", suficiencia="aclaracion"
            )
        else:
            campos = dict(adjunto.get("campos_simulados", {}))
            datos["ocr"] = {"campos": campos, "confirmado": False}  # RF-OCR-03
            respuesta = parcial("ocr", "Esto fue lo que leí del recibo. ¿Es correcto? (simulado)")
        return {
            "respuestas_parciales": [*state.get("respuestas_parciales", []), respuesta],
            "datos_extraidos": datos,
        }

    return nodo_ocr
