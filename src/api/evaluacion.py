"""Modo de evaluación (ADR-16) y fallas inyectables (sección 3.12), solo por configuración.

- `X-Reloj-Simulado` y `X-Escenario-Id` solo se leen con `MODO_EVALUACION=true`; si no, se ignoran.
- `X-Falla-Inyectada` solo se lee con `FALLAS_INYECTABLES=true`. Valores en ASCII:
  `orquestador`, `modelo`, `recuperacion` o `adaptador`, seguidos de `:tiempo` o `:error`
  (por ejemplo, `orquestador:tiempo` en ROB-01 y `adaptador:tiempo` en ROB-02).
Los dos están apagados por defecto. Un valor inválido se ignora y queda en el registro.
"""

import logging
import re
from dataclasses import dataclass
from datetime import datetime

from src.config import Settings
from src.integrations.robustez import FallaInyectada

registro = logging.getLogger(__name__)

# Valor de la cabecera -> nombre del servicio en `con_tiempo_y_reintento`.
SERVICIOS_INYECTABLES = {
    "orquestador": "orquestador",
    "modelo": "modelo",
    "recuperacion": "recuperación",
    "adaptador": "adaptador",
}
ESCENARIO = re.compile(r"^[A-Z]{2,5}-\d{2}$")


@dataclass(frozen=True)
class EvaluacionTurno:
    ahora: datetime | None = None  # reloj simulado
    escenario_id: str | None = None
    falla: FallaInyectada | None = None


def leer_evaluacion(
    settings: Settings,
    reloj_simulado: str | None,
    escenario_id: str | None,
    falla: str | None,
) -> EvaluacionTurno:
    """Lo que el turno toma de las cabeceras de prueba, según la configuración."""
    ahora = escenario = inyectada = None
    if settings.modo_evaluacion:
        if reloj_simulado:
            try:
                ahora = datetime.fromisoformat(reloj_simulado)
            except ValueError:
                registro.warning("X-Reloj-Simulado inválido; se usa el reloj del sistema")
            else:
                if ahora.tzinfo is None:
                    registro.warning("X-Reloj-Simulado sin zona horaria; se usa el del sistema")
                    ahora = None
        if escenario_id and ESCENARIO.match(escenario_id):
            escenario = escenario_id
    if settings.fallas_inyectables and falla:
        servicio, _, tipo = falla.strip().lower().partition(":")
        if servicio in SERVICIOS_INYECTABLES and tipo in ("tiempo", "error"):
            inyectada = FallaInyectada(SERVICIOS_INYECTABLES[servicio], tipo)  # type: ignore[arg-type]
        else:
            registro.warning("X-Falla-Inyectada desconocida; se ignora", extra={"valor": falla})
    return EvaluacionTurno(ahora, escenario, inyectada)
