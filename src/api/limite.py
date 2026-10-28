"""Límite de peticiones por IP en los puntos de acceso que llaman modelos (chat y documento).

Por seguridad y gasto: 10 por minuto y 200 por día por IP (`LIMITE_PETICIONES_POR_MINUTO` y
`LIMITE_PETICIONES_POR_DIA`), en ventanas móviles y en la memoria del proceso; con dos réplicas,
cada una lleva su cuenta. La IP es la última de `X-Forwarded-For`, la que pone Caddy (el backend
solo se alcanza por el proxy); sin esa cabecera, la de la conexión. No cuentan las peticiones del
modo de evaluación con `X-Escenario-Id`: mientras el servidor corre con `--evaluacion` (solo durante
una corrida, A9), cualquiera podría saltarse el límite con esa cabecera, igual que ya puede usar
`X-Reloj-Simulado` o `X-Falla-Inyectada`; es un riesgo aceptado de esa ventana. Al pasarse, 429 con
un mensaje claro y `Retry-After`.
"""

import time
from collections import deque
from collections.abc import Callable
from threading import Lock

from fastapi import HTTPException, Request

from src.api.comun import Evaluacion

MINUTO, DIA = 60.0, 86_400.0
MENSAJE_POR_MINUTO = (
    "Recibí muchas consultas seguidas desde tu conexión. Espera un minuto y vuelve a intentarlo."
)
MENSAJE_POR_DIA = (
    "Llegaste al límite de consultas de hoy desde tu conexión. Vuelve a intentarlo mañana."
)


class LimitadorPorIP:
    """Ventanas móviles de un minuto y de un día por IP."""

    def __init__(
        self, por_minuto: int, por_dia: int, reloj: Callable[[], float] = time.monotonic
    ) -> None:
        self.por_minuto, self.por_dia, self._reloj = por_minuto, por_dia, reloj
        self._marcas: dict[str, deque[float]] = {}
        self._candado = Lock()
        self._proxima_limpieza = 0.0

    def registrar(self, ip: str) -> tuple[str, int] | None:
        """Cuenta la petición si cabe; si no, el mensaje y los segundos para reintentar."""
        with self._candado:
            ahora = self._reloj()
            marcas = self._marcas.setdefault(ip, deque())
            while marcas and ahora - marcas[0] >= DIA:
                marcas.popleft()
            en_el_minuto = [m for m in marcas if ahora - m < MINUTO]
            if len(marcas) >= self.por_dia:
                return MENSAJE_POR_DIA, max(1, int(DIA - (ahora - marcas[0])) + 1)
            if len(en_el_minuto) >= self.por_minuto:
                return MENSAJE_POR_MINUTO, max(1, int(MINUTO - (ahora - en_el_minuto[0])) + 1)
            marcas.append(ahora)
            if ahora >= self._proxima_limpieza:  # a lo más una vez por minuto
                self._proxima_limpieza = ahora + MINUTO
                self._marcas = {k: v for k, v in self._marcas.items() if ahora - v[-1] < DIA}
            return None


def ip_del_cliente(request: Request) -> str:
    reenviada = request.headers.get("x-forwarded-for", "")
    if ultima := reenviada.split(",")[-1].strip():
        return ultima
    return request.client.host if request.client else "desconocida"


def limitar_peticiones(request: Request, evaluacion: Evaluacion) -> None:
    """Dependencia de los puntos de acceso que llaman modelos."""
    if evaluacion.escenario_id is not None:  # modo de evaluación (ADR-16): no cuenta
        return
    if (rechazo := request.app.state.limitador.registrar(ip_del_cliente(request))) is not None:
        mensaje, segundos = rechazo
        raise HTTPException(status_code=429, detail=mensaje, headers={"Retry-After": str(segundos)})
