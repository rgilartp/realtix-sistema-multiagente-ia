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
        parciales = [dict(p) for p in state.get("respuestas_parciales", [])]
        ultima = parciales[-1]
        previo = state.get("nivel_confianza", 0.0) if marcas.get("confianza_calculada") else None

        def resultado(aprobada: bool, nivel: float | None, **extra: Any) -> dict[str, Any]:
            """Anota la parte (nivel y aprobación) para que solo se muestren las aprobadas."""
            ultima["aprobada"] = aprobada
            ultima["nivel"] = nivel
            return {"respuestas_parciales": parciales, "marcas": marcas, **extra}

        def escalar(motivo: str, nivel: float | None = None) -> dict[str, Any]:
            # ADR-13: sin confianza propia de la parte que escala, el nivel es 0.0.
            marcas["confianza_calculada"] = nivel is not None
            return resultado(
                False,
                nivel,
                requiere_escalamiento=True,
                motivo_escalamiento=motivo,
                nivel_confianza=nivel if nivel is not None else 0.0,
            )

        if ultima["fallo_servicio"]:
            marcas["fallo_servicio"] = True
            return escalar("fallo de servicio")
        if ultima["fuera_de_alcance"]:
            return escalar("fuera de alcance")
        if ultima["suficiencia"] == "no_corresponde":
            if state.get("intentos_clasificacion", 0) >= config.max_reclasificaciones:
                return escalar("tope de reclasificaciones")
            marcas["reclasificar"] = True
            return resultado(
                False,
                None,
                categorias_descartadas=[
                    *state.get("categorias_descartadas", []),
                    ultima["categoria"],
                ],
            )
        fija = ultima["suficiencia"] in RESPUESTAS_VALIDAS_SIN_BASE or ultima["rechazo_acceso"]
        if fija:
            nivel = 1.0
        else:
            nivel = calcular_nivel(
                ultima["similitud"], ultima["suficiencia"], ultima["cobertura"], config.pesos
            )
        # En una consulta multiagente basta una parte bajo el umbral para escalar.
        minimo = nivel if previo is None else min(previo, nivel)
        if not fija and ultima["cobertura"] <= 0:
            return escalar("sin cobertura", minimo)
        marcas["confianza_calculada"] = True
        if nivel < config.umbral_confianza:
            return escalar("confianza insuficiente", minimo)
        return resultado(True, nivel, nivel_confianza=minimo)

    return nodo_confianza
