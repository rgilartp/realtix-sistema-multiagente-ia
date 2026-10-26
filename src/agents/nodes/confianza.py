"""`nodo_confianza` simulado: puntaje (ADR-17) y decisión de continuar, responder o escalar.

Sin modelo (ADR-03). Escala por falla de un servicio, tributario fuera de alcance, falta de
cobertura, confianza bajo el umbral o tope de reclasificaciones. La aclaración y el rechazo por
acceso son respuestas válidas y no escalan; «no corresponde» devuelve la consulta al orquestador.
"""

from collections.abc import Callable
from typing import Any

from src.agents.dependencias import Dependencias
from src.agents.state import AgentState
from src.services.confianza import calcular_nivel

RESPUESTAS_VALIDAS_SIN_BASE = ("aclaracion",)


def crear_nodo_confianza(deps: Dependencias) -> Callable[[AgentState], dict[str, Any]]:
    config = deps.config

    def nodo_confianza(state: AgentState) -> dict[str, Any]:
        marcas = dict(state.get("marcas", {}))
        parciales = state.get("respuestas_parciales", [])
        ultima = parciales[-1]
        previo = state.get("nivel_confianza", 0.0) if marcas.get("confianza_calculada") else None

        def escalar(motivo: str, nivel: float | None = None) -> dict[str, Any]:
            if nivel is not None:
                marcas["confianza_calculada"] = True
            return {
                "requiere_escalamiento": True,
                "motivo_escalamiento": motivo,
                "marcas": marcas,
                "nivel_confianza": nivel if nivel is not None else (previo or 0.0),
            }

        if ultima["fallo_servicio"]:
            marcas["fallo_servicio"] = True
            return escalar("fallo de un servicio")
        if ultima["fuera_de_alcance"]:
            return escalar("fuera de alcance")
        if ultima["suficiencia"] == "no_corresponde":
            if state.get("intentos_clasificacion", 0) >= config.max_reclasificaciones:
                return escalar("tope de reclasificaciones")
            marcas["reclasificar"] = True
            return {
                "marcas": marcas,
                "categorias_descartadas": [
                    *state.get("categorias_descartadas", []),
                    ultima["categoria"],
                ],
            }
        if ultima["suficiencia"] in RESPUESTAS_VALIDAS_SIN_BASE or ultima["rechazo_acceso"]:
            nivel = 1.0
        else:
            nivel = calcular_nivel(
                ultima["similitud"], ultima["suficiencia"], ultima["cobertura"], config.pesos
            )
            if ultima["cobertura"] <= 0:
                return escalar("sin cobertura", nivel)
        # En una consulta multiagente basta una parte bajo el umbral para escalar.
        nivel = nivel if previo is None else min(previo, nivel)
        marcas["confianza_calculada"] = True
        if nivel < config.umbral_confianza:
            return escalar("confianza insuficiente", nivel)
        return {"nivel_confianza": nivel, "marcas": marcas}

    return nodo_confianza
