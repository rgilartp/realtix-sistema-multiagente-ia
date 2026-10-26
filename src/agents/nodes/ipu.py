"""`nodo_ipu` simulado: estado de cuenta por el adaptador o respuesta conceptual fija.

No contiene lógica tributaria: solo consulta al adaptador y da formato (capas separadas).
"""

import re
from collections.abc import Callable
from typing import Any

from src.agents.dependencias import Dependencias
from src.agents.nodes._comun import (
    MATRICULA,
    agregar_parcial,
    contiene,
    es_personal,
    formatear_pesos,
    normalizar,
    parcial,
    texto_de_la_parte,
)
from src.agents.nodes.orquestador import PALABRAS_IPU, _tiene_ica
from src.agents.state import AgentState
from src.data.adapter import PredioInaccesibleError

REFERENCIA_ANTERIOR = re.compile(r"\b(ese|mismo|anterior)\b")


def _resolver_predio(texto: str, state: AgentState) -> str | None:
    encontrada = MATRICULA.search(texto)
    if encontrada:
        return encontrada.group(0).upper()
    if REFERENCIA_ANTERIOR.search(normalizar(texto)):
        recordado = state.get("datos_extraidos", {}).get("predio")
        if recordado:
            return str(recordado)
    propios = state.get("predios_autorizados", [])
    return propios[0] if len(propios) == 1 else None


def crear_nodo_ipu(deps: Dependencias) -> Callable[[AgentState], dict[str, Any]]:
    def responder(state: AgentState) -> tuple[dict[str, Any], dict[str, Any]]:
        texto = texto_de_la_parte(state)
        datos = dict(state.get("datos_extraidos", {}))
        if _tiene_ica(texto) and not (contiene(texto, PALABRAS_IPU) or MATRICULA.search(texto)):
            return parcial("ipu", "", suficiencia="no_corresponde", cobertura=0.0), datos
        contribuyente = state.get("contribuyente_id")
        if not es_personal(texto):
            respuesta = parcial(
                "ipu",
                "Explicación del impuesto predial unificado (respuesta simulada).",
                fuentes=("Acuerdo 105 de 2003 (simulado)",),
                similitud=0.85,
            )
            return respuesta, datos
        if not contribuyente:
            return parcial("ipu", "Necesitas iniciar sesión para ver tu cuenta."), datos
        matricula = _resolver_predio(texto, state)
        if matricula is None:
            propios = ", ".join(state.get("predios_autorizados", [])) or "ninguno"
            return parcial(
                "ipu",
                f"¿De cuál de tus predios quieres saber? Tus predios: {propios}.",
                suficiencia="aclaracion",
            ), datos
        try:
            cuenta = deps.adaptador.get_estado_cuenta(matricula, contribuyente)
        except PredioInaccesibleError as error:
            return parcial("ipu", str(error), rechazo_acceso=True), datos
        except Exception:  # el adaptador no respondió (RNF-08)
            return parcial(
                "ipu", "", suficiencia="no_pudo", cobertura=0.0, fallo_servicio=True
            ), datos
        datos["predio"] = matricula
        texto_cuenta = (
            f"Predio {matricula}: {cuenta.obligaciones_pendientes} obligaciones pendientes "
            f"o vencidas, saldo {formatear_pesos(cuenta.saldo_total_pendiente)}."
        )
        return parcial("ipu", texto_cuenta), datos

    def nodo_ipu(state: AgentState) -> dict[str, Any]:
        respuesta, datos = responder(state)
        return {
            "respuestas_parciales": agregar_parcial(state, respuesta),
            "datos_extraidos": datos,
        }

    return nodo_ipu
