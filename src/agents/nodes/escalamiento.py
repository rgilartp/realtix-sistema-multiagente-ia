"""`nodo_escalamiento`: resumen del caso, registro y aviso de transferencia, sin modelo (ADR-03).

Único nodo que registra casos (ADR-18). Si la parte que escala no tiene confianza calculada guarda
0.0 con su motivo (ADR-13). Entrega solo las partes aprobadas por la confianza (sección 3.4,
caso 4); las rechazadas van en el resumen para el funcionario. Es el último recurso (RNF-08): nunca
falla; un motivo fuera de la lista se registra como «fallo de servicio» y conserva el original.
"""

import logging
import time
from collections.abc import Callable
from typing import Any

from langchain_core.messages import AIMessage

from src.agents.dependencias import Dependencias
from src.agents.state import MOTIVOS_ESCALAMIENTO, AgentState
from src.data.models import CasoEscalado
from src.services.resumen import construir_resumen

registro = logging.getLogger(__name__)

AVISO_TRANSFERENCIA = (
    "Voy a transferir tu consulta a un funcionario, que te atenderá a la brevedad. "
    "Ya le compartí un resumen para que no tengas que repetirlo."
)
# Explicación previa al aviso según el motivo; los demás motivos solo llevan el aviso.
PREFACIOS = {
    "solicitud explícita": "Con gusto.",
    "fuera de alcance": (
        "Tu consulta trata de un tema tributario que este asistente no cubre: atiende el impuesto "
        "predial unificado y el impuesto de industria y comercio de Bogotá, sin la retención del "
        "ICA ni otros tributos o municipios."
    ),
    "fallo de servicio": "En este momento no pude completar tu consulta por una falla técnica.",
}


def crear_nodo_escalamiento(deps: Dependencias) -> Callable[[AgentState], dict[str, Any]]:
    def nodo_escalamiento(state: AgentState) -> dict[str, Any]:
        inicio = time.perf_counter()
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
        # Si escala antes del agente, la de la clasificación (F2 de la corrida 1).
        categoria = state.get("categoria") or marcas.get("categoria_clasificada") or None
        intentos = state.get("intentos_clasificacion", 0)
        resumen, resumen_json = construir_resumen(
            motivo=motivo,
            categoria=categoria,
            nivel_confianza=nivel,
            intentos=intentos,
            resueltas=resueltas,
            rechazadas=rechazadas,
            motivo_original=original if motivo != original else None,
        )
        resumen_json["duracion_resumen_ms"] = round((time.perf_counter() - inicio) * 1000, 3)
        caso = CasoEscalado(
            id_caso=f"CASO-{state['id_conversacion']}",
            id_conversacion=state["id_conversacion"],
            resumen=resumen,
            nivel_confianza=nivel,
            motivo=motivo,
            categoria=categoria,
            resumen_json=resumen_json,
            intentos=intentos,
        )
        try:
            deps.adaptador.registrar_caso_escalado(caso)
        except Exception:  # RNF-08: el aviso se entrega aunque el registro falle
            marcas["registro_fallido"] = True
        marcas["duracion_escalamiento_ms"] = round((time.perf_counter() - inicio) * 1000, 3)
        prefacio = PREFACIOS.get(motivo)
        aviso = f"{prefacio} {AVISO_TRANSFERENCIA}" if prefacio else AVISO_TRANSFERENCIA
        partes = "\n\n".join(p["texto"] for p in resueltas)
        respuesta = f"{partes}\n\n{aviso}" if partes else aviso
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
