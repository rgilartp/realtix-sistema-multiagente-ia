"""`nodo_escalamiento` simulado: resumen del caso, registro y aviso de transferencia.

Único nodo que registra casos (ADR-18). Si escala antes de calcular la confianza guarda 0.0 con
su motivo (ADR-13). Entrega las partes ya resueltas de una consulta multiagente (sección 3.4).
"""

from collections.abc import Callable
from typing import Any

from langchain_core.messages import AIMessage

from src.agents.dependencias import Dependencias
from src.agents.state import AgentState
from src.data.models import CasoEscalado

AVISO_TRANSFERENCIA = (
    "Voy a transferir tu consulta a un funcionario, que te atenderá a la brevedad. "
    "Ya le compartí un resumen para que no tengas que repetirlo."
)


def crear_nodo_escalamiento(deps: Dependencias) -> Callable[[AgentState], dict[str, Any]]:
    def nodo_escalamiento(state: AgentState) -> dict[str, Any]:
        marcas = dict(state.get("marcas", {}))
        motivo = state.get("motivo_escalamiento") or "no especificado"
        nivel = state.get("nivel_confianza", 0.0) if marcas.get("confianza_calculada") else 0.0
        resueltas = [
            p
            for p in state.get("respuestas_parciales", [])
            if p["suficiencia"] in ("completa", "parcial", "aclaracion") and p["texto"]
        ]
        categoria = state.get("categoria") or None
        resumen = (
            f"Motivo: {motivo}. Categoría: {categoria or 'sin clasificar'}. "
            f"Nivel de confianza: {nivel:.2f}. "
            f"Reclasificaciones: {state.get('intentos_clasificacion', 0)}. "
            f"Partes ya resueltas: {len(resueltas)}."
        )
        caso = CasoEscalado(
            id_caso=f"CASO-{state['id_conversacion']}",
            id_conversacion=state["id_conversacion"],
            resumen=resumen,
            nivel_confianza=nivel,
            motivo=motivo,
            categoria=categoria,
            resumen_json={
                "motivo": motivo,
                "categoria": categoria,
                "nivel_confianza": nivel,
                "intentos": state.get("intentos_clasificacion", 0),
                "partes_resueltas": [p["texto"] for p in resueltas],
            },
            intentos=state.get("intentos_clasificacion", 0),
        )
        try:
            deps.adaptador.registrar_caso_escalado(caso)
        except Exception:  # RNF-08: el aviso se entrega aunque el registro falle
            marcas["registro_fallido"] = True
        partes = "\n".join(p["texto"] for p in resueltas)
        respuesta = f"{partes}\n\n{AVISO_TRANSFERENCIA}" if partes else AVISO_TRANSFERENCIA
        return {
            "requiere_escalamiento": True,
            "motivo_escalamiento": motivo,
            "nivel_confianza": nivel,
            "resumen_caso": resumen,
            "respuesta_final": respuesta,
            "marcas": marcas,
            "messages": [AIMessage(content=respuesta)],
        }

    return nodo_escalamiento
