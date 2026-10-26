"""Nivel de confianza (ADR-17): 0,4 × similitud + 0,4 × suficiencia + 0,2 × cobertura.

Servicio puro y sin modelo (ADR-03). Sin fragmentos recuperados (`similitud=None`), el puntaje se
renormaliza sobre los otros dos factores (sección 3.3). La escala que normaliza el coseno del canal
vectorial es un parámetro (`EscalaSimilitud`); se fija en B8 con la recuperación real.
"""

from dataclasses import dataclass
from typing import Literal

SUFICIENCIA: dict[str, float] = {"completa": 1.0, "parcial": 0.5, "no_pudo": 0.0}
TRIBUTOS_CUBIERTOS = ("ipu", "ica")  # RF-SYS-03: predial e industria y comercio de Bogotá
MUNICIPIO_CUBIERTO = "Bogotá"
Origen = Literal["formula", "aclaracion", "rechazo_acceso"]


@dataclass(frozen=True)
class Pesos:
    similitud: float = 0.4
    suficiencia: float = 0.4
    cobertura: float = 0.2


@dataclass(frozen=True)
class EscalaSimilitud:
    """Coseno que vale 0 y coseno que vale 1; por defecto, la identidad hasta que B8 la fije."""

    minimo: float = 0.0
    maximo: float = 1.0


@dataclass(frozen=True)
class Evaluacion:
    """Resultado de evaluar una parte: de dónde sale el nivel y si pasa el umbral."""

    nivel: float
    origen: Origen  # «formula» es el único nivel calculado; los otros dos valen 1,0 fijo
    aprobada: bool
    motivo: str | None  # «sin cobertura» o «confianza insuficiente» si no se aprueba


PESOS_POR_DEFECTO = Pesos()
ESCALA_POR_DEFECTO = EscalaSimilitud()


def normalizar_similitud(coseno: float, escala: EscalaSimilitud = ESCALA_POR_DEFECTO) -> float:
    """Lleva el coseno a [0, 1] con la escala dada."""
    if escala.maximo <= escala.minimo:
        raise ValueError("La escala de similitud necesita máximo mayor que mínimo.")
    return min(1.0, max(0.0, (coseno - escala.minimo) / (escala.maximo - escala.minimo)))


def calcular_nivel(
    similitud: float | None, suficiencia: str, cobertura: float, pesos: Pesos = PESOS_POR_DEFECTO
) -> float:
    """Puntaje entre 0 y 1; la suficiencia desconocida vale 0. La similitud ya va normalizada."""
    valor_suf = SUFICIENCIA.get(suficiencia, 0.0)
    if similitud is None:
        total = pesos.suficiencia + pesos.cobertura
        return (pesos.suficiencia * valor_suf + pesos.cobertura * cobertura) / total
    return pesos.similitud * similitud + pesos.suficiencia * valor_suf + pesos.cobertura * cobertura


def factor_cobertura(
    tributo: str | None, municipio: str | None, cobertura_declarada: float
) -> float:
    """Cobertura de 0 a 1: el menor entre el alcance del sistema y lo que declara el agente.

    El alcance (RF-SYS-03) es 1 para predial e ICA de Bogotá y para lo que no es un tributo
    (general, OCR); 0 para otro tributo o para otro municipio. Lo que declara el agente (ADR-03)
    solo puede bajarla.
    """
    en_alcance = tributo is None or tributo in TRIBUTOS_CUBIERTOS
    if en_alcance and tributo is not None and municipio not in (None, MUNICIPIO_CUBIERTO):
        en_alcance = False
    alcance = 1.0 if en_alcance else 0.0
    return min(alcance, max(0.0, min(1.0, cobertura_declarada)))


def evaluar_parte(
    similitud: float | None,
    suficiencia: str,
    cobertura: float,
    *,
    rechazo_acceso: bool = False,
    umbral: float,
    pesos: Pesos = PESOS_POR_DEFECTO,
    escala: EscalaSimilitud = ESCALA_POR_DEFECTO,
) -> Evaluacion:
    """Evalúa una parte: la aclaración y el rechazo por acceso son respuestas válidas (1,0 fijo).

    `similitud` es el coseno sin normalizar (o `None` si no hubo fragmentos). Sin cobertura la parte
    nunca se aprueba, aunque el puntaje supere el umbral (ADR-17).
    """
    if suficiencia == "aclaracion":
        return Evaluacion(1.0, "aclaracion", True, None)
    if rechazo_acceso:
        return Evaluacion(1.0, "rechazo_acceso", True, None)
    normalizada = None if similitud is None else normalizar_similitud(similitud, escala)
    nivel = calcular_nivel(normalizada, suficiencia, cobertura, pesos)
    if cobertura <= 0:
        return Evaluacion(nivel, "formula", False, "sin cobertura")
    if round(nivel, 9) < umbral:  # sin ruido de coma flotante en el umbral exacto
        return Evaluacion(nivel, "formula", False, "confianza insuficiente")
    return Evaluacion(nivel, "formula", True, None)


def combinar_niveles(previo: float | None, nivel: float) -> float:
    """En una consulta multiagente cuenta el menor nivel de las partes (sección 3.3)."""
    return nivel if previo is None else min(previo, nivel)
