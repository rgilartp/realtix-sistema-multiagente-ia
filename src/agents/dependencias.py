"""Dependencias inyectadas en los nodos: adaptador, configuración, clasificador, modelos y más.

Los nodos simulados de B4 y los reales de B7 comparten esta firma; el grafo no cambia. Sin
`modelos`, los agentes usan sus versiones simuladas (las pruebas del grafo, sin red).
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from langchain_core.language_models import BaseChatModel

from src.agents.state import AgentState
from src.data.adapter import RealSitAdapter
from src.integrations.recuperador import Recuperador
from src.services.confianza import EscalaSimilitud, Pesos
from src.services.horario import Reloj


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
    timeout_modelo_s: float = 20.0
    timeout_recuperacion_s: float = 5.0
    timeout_adaptador_s: float = 5.0
    zona_horaria: str = "America/Bogota"

    @classmethod
    def desde_settings(cls, settings: Any) -> "ConfigGrafo":
        return cls(
            umbral_confianza=settings.umbral_confianza,
            max_reclasificaciones=settings.max_reclasificaciones,
            pesos=Pesos(
                settings.peso_similitud, settings.peso_suficiencia, settings.peso_cobertura
            ),
            timeout_modelo_s=settings.timeout_modelo_s,
            timeout_recuperacion_s=settings.timeout_chroma_s,
            timeout_adaptador_s=settings.timeout_adaptador_s,
            zona_horaria=settings.zona_horaria,
        )


@dataclass
class Dependencias:
    adaptador: RealSitAdapter
    config: ConfigGrafo = ConfigGrafo()
    clasificador: Clasificador | None = None  # None: el clasificador simulado por palabras
    modelos: Callable[[str], BaseChatModel] | None = None  # None: agentes simulados
    recuperador: Recuperador | None = None
    reloj: Reloj | None = None  # None: el del sistema; el turno puede traer `ahora` (ADR-16)
