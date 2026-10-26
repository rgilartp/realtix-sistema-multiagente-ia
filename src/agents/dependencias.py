"""Dependencias inyectadas en los nodos: adaptador, configuración y clasificador.

Los nodos simulados de B4 y los reales de B7 comparten esta firma; el grafo no cambia.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from src.agents.state import AgentState
from src.data.adapter import RealSitAdapter
from src.services.confianza import EscalaSimilitud, Pesos


@dataclass
class Clasificacion:
    """Salida del orquestador: partes por categoría (en orden) y marcas de la consulta."""

    partes: list[dict[str, str]] = field(default_factory=list)  # {"categoria", "texto"}
    marcas: dict[str, Any] = field(default_factory=dict)


Clasificador = Callable[[str, AgentState], Clasificacion]


@dataclass(frozen=True)
class ConfigGrafo:
    umbral_confianza: float = 0.7
    max_reclasificaciones: int = 2
    pesos: Pesos = Pesos()
    escala_similitud: EscalaSimilitud = EscalaSimilitud()  # se fija en B8 (sección 3.3)

    @classmethod
    def desde_settings(cls, settings: Any) -> "ConfigGrafo":
        return cls(
            umbral_confianza=settings.umbral_confianza,
            max_reclasificaciones=settings.max_reclasificaciones,
            pesos=Pesos(
                settings.peso_similitud, settings.peso_suficiencia, settings.peso_cobertura
            ),
        )


@dataclass
class Dependencias:
    adaptador: RealSitAdapter
    config: ConfigGrafo = ConfigGrafo()
    clasificador: Clasificador | None = None  # None: el clasificador simulado por palabras
