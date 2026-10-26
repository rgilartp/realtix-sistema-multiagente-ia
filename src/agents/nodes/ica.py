"""`nodo_ica` simulado: tarifa por el adaptador, respuesta conceptual y retención que escala."""

import re
from collections.abc import Callable
from typing import Any

from src.agents.dependencias import Dependencias
from src.agents.nodes._comun import MATRICULA, contiene, normalizar, parcial, ultimo_texto
from src.agents.nodes.orquestador import PALABRAS_IPU, _tiene_ica
from src.agents.state import AgentState
from src.services.errores import ActividadNoReconocidaError

CODIGO_CIIU = re.compile(r"\b\d{4}\b")


def crear_nodo_ica(deps: Dependencias) -> Callable[[AgentState], dict[str, Any]]:
    def responder(state: AgentState) -> dict[str, Any]:
        texto = ultimo_texto(state)
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

    def nodo_ica(state: AgentState) -> dict[str, Any]:
        return {"respuestas_parciales": [*state.get("respuestas_parciales", []), responder(state)]}

    return nodo_ica
