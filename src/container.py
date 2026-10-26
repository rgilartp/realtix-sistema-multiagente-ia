"""Contenedor de dependencias: construye una sola vez los servicios y los inyecta.

Es el único módulo que conoce las implementaciones concretas (adaptador, recuperador, modelos y
almacén). Los nodos y la API reciben sus dependencias desde aquí; los bloques siguientes agregan
cada una como propiedad perezosa.
"""

from functools import cached_property, lru_cache

from langchain_anthropic import ChatAnthropic
from langchain_openai import OpenAIEmbeddings

from src.agents.dependencias import ConfigGrafo, Dependencias
from src.config import Settings, cargar_configuracion
from src.data.adapter import MockRealSitAdapter, RealSitAdapter
from src.integrations.embeddings import crear_embeddings
from src.integrations.modelos import crear_modelo
from src.integrations.recuperador import Recuperador, RecuperadorEnMemoria
from src.services.horario import Horario, Reloj
from src.store.almacen import Almacen, crear_motor


class Contenedor:
    """Dependencias del sistema multiagente de IA, construidas a pedido."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings

    @cached_property
    def settings(self) -> Settings:
        """Configuración inyectada o, si no la hay, leída del entorno."""
        return self._settings or cargar_configuracion()

    @cached_property
    def almacen(self) -> Almacen:
        """Almacén propio en PostgreSQL (SQLite en las pruebas unitarias); crea las tablas."""
        almacen = Almacen(crear_motor(self.settings.database_url.get_secret_value()))
        almacen.crear_esquema()
        return almacen

    @cached_property
    def adaptador(self) -> RealSitAdapter:
        """Adaptador de RealSit (sintético, solo lectura); los casos van al almacén propio."""
        return MockRealSitAdapter(
            self.settings.realsit_db_path,
            registro_casos=self.almacen,
            vigencia=self.settings.vigencia_actual,
        )

    @cached_property
    def deps(self) -> Dependencias:
        """Dependencias de los nodos: adaptador y parámetros de la confianza y el enrutamiento."""
        return Dependencias(self.adaptador, ConfigGrafo.desde_settings(self.settings))

    @cached_property
    def recuperador(self) -> Recuperador:
        """Recuperador provisional en memoria; B8 pone el híbrido (Chroma + BM25)."""
        return RecuperadorEnMemoria()

    def horario(self, reloj: Reloj | None = None) -> Horario:
        """Horario de atención; el modo de evaluación inyecta un reloj simulado (ADR-16)."""
        return Horario.desde_settings(self.settings, reloj)

    def modelo(self, nodo: str) -> ChatAnthropic:
        """Modelo del nodo según su variable de entorno (RF-SYS-04)."""
        return crear_modelo(nodo, self.settings)

    @cached_property
    def embeddings(self) -> OpenAIEmbeddings:
        """Cliente de embeddings (`text-embedding-3-large`)."""
        return crear_embeddings(self.settings)


@lru_cache(maxsize=1)
def obtener_contenedor() -> Contenedor:
    """Contenedor único del proceso."""
    return Contenedor()
