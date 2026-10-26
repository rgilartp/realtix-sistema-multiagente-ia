"""Nivel de confianza (ADR-17): 0,4 × similitud + 0,4 × suficiencia + 0,2 × cobertura.

B4 trae solo la fórmula, pura y sin modelo. B5 agrega la normalización de la similitud y el resto
del servicio. Sin fragmentos recuperados (`similitud=None`), el puntaje se renormaliza sobre los
otros dos factores (sección 3.3).
"""

from dataclasses import dataclass

SUFICIENCIA: dict[str, float] = {"completa": 1.0, "parcial": 0.5, "no_pudo": 0.0}


@dataclass(frozen=True)
class Pesos:
    similitud: float = 0.4
    suficiencia: float = 0.4
    cobertura: float = 0.2


PESOS_POR_DEFECTO = Pesos()


def calcular_nivel(
    similitud: float | None, suficiencia: str, cobertura: float, pesos: Pesos = PESOS_POR_DEFECTO
) -> float:
    """Puntaje entre 0 y 1; la suficiencia desconocida vale 0."""
    valor_suf = SUFICIENCIA.get(suficiencia, 0.0)
    if similitud is None:
        total = pesos.suficiencia + pesos.cobertura
        return (pesos.suficiencia * valor_suf + pesos.cobertura * cobertura) / total
    return pesos.similitud * similitud + pesos.suficiencia * valor_suf + pesos.cobertura * cobertura
