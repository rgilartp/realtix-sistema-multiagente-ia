"""`nodo_confianza`: aplica el servicio de confianza (ADR-17) y decide el camino del turno.

Sin modelo (ADR-03). Escala por falla de un servicio, tributario fuera de alcance, falta de
cobertura, confianza bajo el umbral o tope de reclasificaciones. La aclaración y el rechazo por
acceso son respuestas válidas y no escalan; «no corresponde» devuelve la consulta al orquestador.
"""

from collections.abc import Callable
from typing import Any

from src.agents.dependencias import Dependencias
from src.agents.state import AgentState
from src.services.confianza import (
    combinar_niveles,
    evaluar_parte,
    factor_cobertura,
)


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
        tributo = ultima["categoria"] if ultima["categoria"] in ("ipu", "ica") else None
        municipio = "Medellín" if marcas.get("municipio_distinto") else None
        evaluacion = evaluar_parte(
            ultima["similitud"],
            ultima["suficiencia"],
            factor_cobertura(tributo, municipio, ultima["cobertura"]),
            rechazo_acceso=ultima["rechazo_acceso"],
            umbral=config.umbral_confianza,
            pesos=config.pesos,
            escala=config.escala_similitud,
        )
        ultima["origen_nivel"] = evaluacion.origen
        # En una consulta multiagente basta una parte bajo el umbral para escalar.
        minimo = combinar_niveles(previo, evaluacion.nivel)
        if evaluacion.motivo == "sin cobertura":
            return escalar(evaluacion.motivo, minimo)
        marcas["confianza_calculada"] = True
        if evaluacion.motivo:
            return escalar(evaluacion.motivo, minimo)
        return resultado(True, evaluacion.nivel, nivel_confianza=minimo)

    return nodo_confianza
