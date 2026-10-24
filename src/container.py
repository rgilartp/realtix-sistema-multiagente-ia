"""Contenedor de dependencias: construye una sola vez los servicios y los inyecta.

Es el único módulo que conoce las implementaciones concretas (adaptador, recuperador, modelos y
almacén). Los nodos y la API reciben sus dependencias desde aquí; los bloques siguientes agregan
cada una como propiedad perezosa.
"""

from functools import cached_property, lru_cache

from src.config import Settings, cargar_configuracion


class Contenedor:
    """Dependencias del sistema multiagente de IA, construidas a pedido."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings

    @cached_property
    def settings(self) -> Settings:
        """Configuración inyectada o, si no la hay, leída del entorno."""
        return self._settings or cargar_configuracion()


@lru_cache(maxsize=1)
def obtener_contenedor() -> Contenedor:
    """Contenedor único del proceso."""
    return Contenedor()
