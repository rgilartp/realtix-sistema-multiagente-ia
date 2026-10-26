"""Lo que usan los puntos de acceso: configuración, almacén, adaptador, grafo, reloj y salud.

`crear_app` los recibe ya armados (las pruebas: SQLite, `MemorySaver` y modelos falsos) o los arma
el `lifespan` desde el contenedor (PostgreSQL, Chroma y los modelos reales).
"""

import tomllib
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from typing import Any

import yaml
from langgraph.graph.state import CompiledStateGraph

from src.config import Settings
from src.data.adapter import RealSitAdapter
from src.services.horario import Reloj, RelojSistema
from src.store.almacen import Almacen

RAIZ = Path(__file__).resolve().parent.parent.parent
USUARIOS_FIJOS = RAIZ / "src" / "data" / "generar" / "usuarios_fijos.yaml"


def version_del_proyecto() -> str:
    """La versión de `pyproject.toml` (el proyecto no se instala como paquete)."""
    try:
        return tomllib.loads((RAIZ / "pyproject.toml").read_text(encoding="utf-8"))["project"][
            "version"
        ]
    except (OSError, KeyError, tomllib.TOMLDecodeError):
        return "dev"


def usuarios_de_prueba(ruta: Path = USUARIOS_FIJOS) -> list[dict[str, str]]:
    """Usuarios de la OVT simulada (sección 4.2): id, contribuyente, nombre sintético y tipo."""
    datos = yaml.safe_load(ruta.read_text(encoding="utf-8"))
    return [
        {
            "usuario": u["id"],
            "contribuyente_id": u["contribuyente"]["id"],
            "nombre": u["contribuyente"]["nombre"],
            "tipo_persona": u["contribuyente"]["tipo_persona"],
        }
        for u in datos["usuarios"]
    ]


@dataclass
class ServiciosAPI:
    settings: Settings
    almacen: Almacen
    adaptador: RealSitAdapter
    grafo: CompiledStateGraph
    reloj: Reloj = field(default_factory=RelojSistema)
    # Comprobaciones de `/health`: nombre -> función que falla si la dependencia no responde.
    salud: dict[str, Callable[[], Any]] = field(default_factory=dict)
    version: str = field(default_factory=version_del_proyecto)

    @cached_property
    def usuarios(self) -> list[dict[str, str]]:
        return usuarios_de_prueba()

    @cached_property
    def nombre_de(self) -> dict[str, str]:
        """Contribuyente -> nombre de la sesión, para el anonimizador (pendiente de B7)."""
        return {u["contribuyente_id"]: u["nombre"] for u in self.usuarios}

    @cached_property
    def etiquetas(self) -> dict[str, str | None]:
        """Escenario -> categoría esperada, para la matriz de confusión (RF-OBS-02)."""
        from src.evaluacion.escenarios import DIR_ESCENARIOS, cargar_escenarios

        if not DIR_ESCENARIOS.is_dir():  # la imagen de producción no trae las pruebas
            return {}
        return {e["id"]: e.get("categoria_esperada") for e in cargar_escenarios()}
