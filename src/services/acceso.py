"""Reglas de acceso (RF-AUT-01 a RF-AUT-04), sin LangGraph.

La restricción a predios propios vive una sola vez, en `verificar_predio_propio` del adaptador; aquí
solo se decide qué hacer según la sesión. `rechazo_previo` es un filtro anterior al modelo (F9 de
la corrida 1) que compara el mensaje con los predios de la sesión; la regla de verdad sigue siendo
la del adaptador. El token de la OVT simulada (HMAC) lo valida la API (B9).
"""

import re
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal

from src.data.adapter import PredioInaccesibleError, verificar_predio_propio
from src.data.models import Predio

Razon = Literal["permitido", "sesion_requerida", "predio_inaccesible"]
# Una matrícula catastral dentro de un mensaje (formato de la base sintética: 50C-0000000).
MATRICULA_EN_TEXTO = re.compile(r"\b50C-\d{7}\b", re.IGNORECASE)


@dataclass(frozen=True)
class DecisionAcceso:
    permitido: bool
    razon: Razon


def decidir_acceso(
    personal: bool,
    contribuyente_id: str | None,
    *,
    pidio_predio: bool = False,
    predio: Predio | None = None,
) -> DecisionAcceso:
    """Decide si se responde, si falta iniciar sesión o si el predio no se puede consultar.

    - Consulta general (`personal=False`): se atiende sin sesión (RF-AUT-03).
    - Consulta personal sin sesión: se pide iniciar sesión (RF-AUT-04).
    - Con sesión y un predio pedido: `predio` (o `None` si no existe) se valida con la regla única
      del adaptador; ajeno e inexistente dan la misma razón (RF-AUT-02).
    """
    if not personal:
        return DecisionAcceso(True, "permitido")
    if not contribuyente_id:
        return DecisionAcceso(False, "sesion_requerida")
    if pidio_predio:
        try:
            verificar_predio_propio(predio, contribuyente_id)
        except PredioInaccesibleError:
            return DecisionAcceso(False, "predio_inaccesible")
    return DecisionAcceso(True, "permitido")


def matriculas_ajenas(texto: str, predios_autorizados: Iterable[str]) -> list[str]:
    """Las matrículas con formato válido que nombra el mensaje y no son de la sesión, sin modelo
    (F9 de la corrida 1): con una sola, el agente rechaza con el mensaje único antes de llamar al
    modelo (RF-AUT-02), sin depender de que el modelo pida la herramienta con ese predio."""
    propias = {p.upper() for p in predios_autorizados}
    nombradas = (m.upper() for m in MATRICULA_EN_TEXTO.findall(texto))
    return list(dict.fromkeys(m for m in nombradas if m not in propias))


def rechazo_previo(texto: str, contribuyente_id: str | None, predios: Iterable[str]) -> bool:
    """Con sesión, el mensaje nombra un predio que no es de la sesión: se rechaza con el mensaje
    único antes de llamar al modelo. Sin sesión sigue el flujo del aviso de sesión."""
    return bool(contribuyente_id) and bool(matriculas_ajenas(texto, predios))
