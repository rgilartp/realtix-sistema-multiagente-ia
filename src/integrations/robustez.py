"""Tiempo máximo y un único reintento ante fallas transitorias (RNF-08 · sección 3.12).

Toda llamada a un servicio externo (modelo, Chroma, adaptador) pasa por `con_tiempo_y_reintento`.
Si el reintento también falla, se levanta `ServicioNoDisponibleError`: el agente lo reporta como
«fallo de servicio» y la confianza escala. El contribuyente nunca ve el error técnico.
"""

import contextvars
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as TiempoAgotado

TRANSITORIAS: tuple[type[BaseException], ...] = (TimeoutError, ConnectionError, OSError)


class ServicioNoDisponibleError(RuntimeError):
    """El servicio no respondió a tiempo o falló también en el reintento."""

    def __init__(self, servicio: str, causa: BaseException) -> None:
        super().__init__(f"El servicio «{servicio}» no está disponible ({type(causa).__name__}).")
        self.servicio = servicio
        self.causa = causa


def _con_tiempo[T](funcion: Callable[[], T], timeout_s: float) -> T:
    pool = ThreadPoolExecutor(max_workers=1)
    try:
        # El hilo hereda el contexto: trazas de LangSmith y el conteo de tokens siguen la llamada.
        return pool.submit(contextvars.copy_context().run, funcion).result(timeout=timeout_s)
    except TiempoAgotado as error:
        raise TimeoutError(f"Sin respuesta en {timeout_s} s") from error
    finally:
        pool.shutdown(wait=False)  # el hilo que se atrasó no bloquea la respuesta


def con_tiempo_y_reintento[T](
    funcion: Callable[[], T],
    timeout_s: float,
    *,
    servicio: str = "servicio externo",
    transitorias: tuple[type[BaseException], ...] = TRANSITORIAS,
) -> T:
    """Ejecuta `funcion` con tiempo máximo; ante una falla transitoria, reintenta una vez."""
    ultimo: BaseException | None = None
    for _ in range(2):
        try:
            return _con_tiempo(funcion, timeout_s)
        except transitorias as error:
            ultimo = error
    assert ultimo is not None
    raise ServicioNoDisponibleError(servicio, ultimo) from ultimo
