"""Contenedor de dependencias: construye una sola vez los servicios y los inyecta.

Es el único módulo que conoce las implementaciones concretas (adaptador, recuperador, modelos y
almacén). Los nodos y la API reciben sus dependencias desde aquí; los bloques siguientes agregan
cada una como propiedad perezosa.
"""

from functools import cached_property, lru_cache
from threading import Lock
from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_openai import OpenAIEmbeddings

from src.agents.clasificador import ClasificadorLLM
from src.agents.dependencias import ConfigGrafo, Dependencias
from src.config import Settings, cargar_configuracion
from src.data.adapter import MockRealSitAdapter, RealSitAdapter
from src.integrations.embeddings import crear_embeddings
from src.integrations.modelos import crear_modelo
from src.integrations.recuperacion_hibrida import RecuperadorHibrido
from src.integrations.recuperador import Recuperador
from src.services.horario import Horario, Reloj
from src.store.almacen import Almacen, crear_motor


class Contenedor:
    """Dependencias del sistema multiagente de IA, construidas a pedido."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings
        self._chroma: Any = None
        self._candado_chroma = Lock()

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
        """Dependencias de los nodos reales (B7): adaptador, parámetros, clasificador del
        orquestador, modelos de los agentes y recuperador."""
        config = ConfigGrafo.desde_settings(self.settings)
        return Dependencias(
            self.adaptador,
            config,
            clasificador=ClasificadorLLM(self.modelo("orquestador"), config.timeout_modelo_s),
            modelos=self.modelo,
            recuperador=self.recuperador,
            modo_evaluacion=self.settings.modo_evaluacion,
        )

    def cliente_chroma(self) -> Any:
        """Cliente HTTP del Chroma de Compose, uno solo por proceso (se crea al primer uso).

        `/health` lo pide en cada chequeo: un cliente nuevo por llamada dejaba abiertas sus
        conexiones y agotaba los descriptores del proceso en unas dos horas (502 del proxy).
        """
        with self._candado_chroma:  # `/health` y el primer turno pueden pedirlo a la vez
            if self._chroma is None:
                import chromadb

                self._chroma = chromadb.HttpClient(
                    host=self.settings.chroma_host, port=self.settings.chroma_port
                )
            return self._chroma

    @cached_property
    def recuperador(self) -> Recuperador:
        """Recuperación híbrida: Chroma + BM25 + RRF (ADR-04); conecta con Chroma al primer uso."""
        return RecuperadorHibrido(self.cliente_chroma, self.embeddings)

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
