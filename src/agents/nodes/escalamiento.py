"""`nodo_escalamiento` simulado: resumen del caso, registro y aviso de transferencia.

Único nodo que registra casos (ADR-18). Si la parte que escala no tiene confianza calculada guarda
0.0 con su motivo (ADR-13). Entrega solo las partes aprobadas por la confianza (sección 3.4,
caso 4); las rechazadas van en el resumen para el funcionario. Es el último recurso (RNF-08): nunca
falla; un motivo fuera de la lista se registra como «fallo de servicio» y conserva el original.
"""

import logging
from collections.abc import Callable
from typing import Any

from langchain_core.messages import AIMessage

from src.agents.dependencias import Dependencias
from src.agents.state import MOTIVOS_ESCALAMIENTO, AgentState
from src.data.models import CasoEscalado

registro = logging.getLogger(__name__)

AVISO_TRANSFERENCIA = (
    "Voy a transferir tu consulta a un funcionario, que te atenderá a la brevedad. "
    "Ya le compartí un resumen para que no tengas que repetirlo."
)


def crear_nodo_escalamiento(deps: Dependencias) -> Callable[[AgentState], dict[str, Any]]:
    def nodo_escalamiento(state: AgentState) -> dict[str, Any]:
        marcas = dict(state.get("marcas", {}))
        original = state.get("motivo_escalamiento")
        motivo = original if original in MOTIVOS_ESCALAMIENTO else "fallo de servicio"
        if motivo != original:
            registro.warning(
                "Motivo de escalamiento fuera de la lista; se registra como fallo de servicio",
                extra={
                    "id_conversacion": state.get("id_conversacion"),
                    "motivo_original": original,
                },
            )
        nivel = state.get("nivel_confianza", 0.0) if marcas.get("confianza_calculada") else 0.0
        parciales = state.get("respuestas_parciales", [])
        resueltas = [p for p in parciales if p.get("aprobada") and p["texto"]]
        rechazadas = [p for p in parciales if not p.get("aprobada") and p["texto"]]
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
                "partes_rechazadas": [
                    {"categoria": p["categoria"], "texto": p["texto"], "nivel": p.get("nivel")}
                    for p in rechazadas
                ],
                **({"motivo_original": original} if motivo != original else {}),
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
