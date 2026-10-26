"""Reglas de acceso (RF-AUT-01 a RF-AUT-04), sin LangGraph.

La restricción a predios propios vive una sola vez, en `verificar_predio_propio` del adaptador; aquí
solo se decide qué hacer según la sesión. El token de la OVT simulada (HMAC) lo valida la API (B9).
"""

from dataclasses import dataclass
from typing import Literal

from src.data.adapter import PredioInaccesibleError, verificar_predio_propio
from src.data.models import Predio

Razon = Literal["permitido", "sesion_requerida", "predio_inaccesible"]


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
