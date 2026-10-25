"""Contenedor de dependencias: construye una sola vez los servicios y los inyecta.

Es el único módulo que conoce las implementaciones concretas (adaptador, recuperador, modelos y
almacén). Los nodos y la API reciben sus dependencias desde aquí; los bloques siguientes agregan
cada una como propiedad perezosa.
"""

from functools import cached_property, lru_cache

from src.config import Settings, cargar_configuracion
from src.data.adapter import MockRealSitAdapter, RealSitAdapter
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


@lru_cache(maxsize=1)
def obtener_contenedor() -> Contenedor:
    """Contenedor único del proceso."""
    return Contenedor()
