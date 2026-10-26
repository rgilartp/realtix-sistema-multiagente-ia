"""Agentes simulados de B4: sin modelo ni red, para las pruebas del grafo.

Se usan cuando `Dependencias.modelos` es `None`. No contienen lógica tributaria: consultan al
adaptador y dan formato. Los agentes reales (B7) están en `ipu.py`, `ica.py` y `general.py`.
"""

import re
from typing import Any

from src.agents.dependencias import Dependencias
from src.agents.nodes._comun import (
    MATRICULA,
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
from src.services.errores import ActividadNoReconocidaError

GENERAL = "Información general de la plataforma (respuesta simulada)."

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


def responder_ipu(deps: Dependencias, state: AgentState) -> tuple[dict[str, Any], dict[str, Any]]:
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
        return parcial("ipu", "", suficiencia="no_pudo", cobertura=0.0, fallo_servicio=True), datos
    datos["predio"] = matricula
    texto_cuenta = (
        f"Predio {matricula}: {cuenta.obligaciones_pendientes} obligaciones pendientes "
        f"o vencidas, saldo {formatear_pesos(cuenta.saldo_total_pendiente)}."
    )
    return parcial("ipu", texto_cuenta), datos


CODIGO_CIIU = re.compile(r"\b\d{4}\b")


def responder_ica(deps: Dependencias, state: AgentState) -> dict[str, Any]:
    texto = texto_de_la_parte(state)
    ipu = contiene(texto, PALABRAS_IPU) or MATRICULA.search(texto)
    if ipu and not _tiene_ica(texto):
        return parcial("ica", "", suficiencia="no_corresponde", cobertura=0.0)
    if "retencion" in normalizar(texto):  # RF-ICA-04: fuera del alcance del MVP
        return parcial("ica", "", suficiencia="no_pudo", cobertura=0.0, fuera_de_alcance=True)
    codigo = CODIGO_CIIU.search(texto)
    if codigo:
        try:
            tarifa = deps.adaptador.get_tarifa_ica(codigo.group(0))
        except ActividadNoReconocidaError:
            return parcial(
                "ica",
                "No reconozco esa actividad. ¿Puedes confirmar el código CIIU?",
                suficiencia="aclaracion",
            )
        except Exception:  # el adaptador no respondió (RNF-08)
            return parcial("ica", "", suficiencia="no_pudo", cobertura=0.0, fallo_servicio=True)
        return parcial(
            "ica",
            (
                f"Actividad {tarifa.descripcion}: {tarifa.tarifa_por_mil} por mil "
                "(respuesta simulada)."
            ),
            fuentes=(tarifa.fuente,),
            similitud=0.9,
        )
    return parcial(
        "ica",
        "Explicación del impuesto de industria y comercio (respuesta simulada).",
        fuentes=("Acuerdo 65 de 2002 (simulado)",),
        similitud=0.85,
    )
