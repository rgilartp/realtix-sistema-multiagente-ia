"""Aplicación FastAPI del sistema multiagente de IA (sección 8.9).

Se arranca con la fábrica: `uv run uvicorn --factory src.api.app:crear_app`. Sin servicios
inyectados, el `lifespan` abre el checkpointer de PostgreSQL y arma el grafo real con el
contenedor; las pruebas inyectan los suyos (SQLite, `MemorySaver` y modelos falsos).

- CORS solo para `CORS_ORIGENES`; `Content-Security-Policy` con `frame-ancestors` limitado a esos
  orígenes (el de la OVT simulada), `nosniff` y sin `Referer` (sección 3.11). La cabecera del widget
  (HTML) la pone el proxy, que sirve la web (B11 y B13).
- Los errores salen en español y sin detalles técnicos (`{"detalle": …}`); el chat nunca muestra un
  error técnico (RNF-08).
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from langgraph.graph.state import CompiledStateGraph
from starlette.exceptions import HTTPException

from src.agents.graph import checkpointer_postgres, construir_grafo
from src.api import admin, chat, escalamiento, ovt_simulada, predios
from src.api.servicios import ServiciosAPI, version_del_proyecto
from src.config import Settings
from src.container import Contenedor, obtener_contenedor
from src.integrations.robustez import con_tiempo_y_reintento

registro = logging.getLogger(__name__)

CABECERAS_DE_PRUEBA = ("X-Escenario-Id", "X-Reloj-Simulado", "X-Falla-Inyectada")
MENSAJE_FORMATO = "La solicitud no tiene el formato esperado: revisa los campos que enviaste."
MENSAJE_INTERNO = (
    "No pudimos atender la solicitud en este momento. Intenta de nuevo en unos minutos."
)


def servicios_desde_contenedor(contenedor: Contenedor, grafo: CompiledStateGraph) -> ServiciosAPI:
    """Servicios reales, con las comprobaciones de `/health`."""
    settings = contenedor.settings
    adaptador = contenedor.adaptador
    return ServiciosAPI(
        settings=settings,
        almacen=contenedor.almacen,
        adaptador=adaptador,
        grafo=grafo,
        salud={
            "postgres": contenedor.almacen.comprobar,
            "chroma": lambda: con_tiempo_y_reintento(
                lambda: contenedor.cliente_chroma().heartbeat(),
                settings.timeout_chroma_s,
                servicio="chroma",
            ),
            "realsit": lambda: adaptador.get_predios_contribuyente("CC-0000000000"),
        },
    )


@asynccontextmanager
async def _ciclo_de_vida(app: FastAPI) -> AsyncIterator[None]:
    if getattr(app.state, "servicios", None) is not None:  # inyectados (pruebas)
        yield
        return
    contenedor = obtener_contenedor()
    with checkpointer_postgres(contenedor.settings.database_url.get_secret_value()) as saver:
        app.state.servicios = servicios_desde_contenedor(
            contenedor, construir_grafo(contenedor.deps, saver)
        )
        yield


def _origenes(settings: Settings) -> list[str]:
    return list(settings.cors_origenes)


def crear_app(servicios: ServiciosAPI | None = None) -> FastAPI:
    """La aplicación, con servicios inyectados o armados al arrancar."""
    settings = servicios.settings if servicios else obtener_contenedor().settings
    app = FastAPI(
        title="API del sistema multiagente de IA (Realtix)",
        version=servicios.version if servicios else version_del_proyecto(),
        lifespan=_ciclo_de_vida,
    )
    if servicios is not None:
        app.state.servicios = servicios
    origenes = _origenes(settings)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origenes,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type", *CABECERAS_DE_PRUEBA],
    )
    politica = f"default-src 'none'; frame-ancestors {' '.join(origenes) or "'none'"}"

    @app.middleware("http")
    async def cabeceras_de_seguridad(request: Request, siguiente):  # noqa: ANN001, ANN202
        respuesta = await siguiente(request)
        respuesta.headers["Content-Security-Policy"] = politica
        respuesta.headers["X-Content-Type-Options"] = "nosniff"
        respuesta.headers["Referrer-Policy"] = "no-referrer"
        return respuesta

    @app.exception_handler(HTTPException)
    async def error_http(_: Request, error: HTTPException) -> JSONResponse:
        return JSONResponse({"detalle": str(error.detail)}, status_code=error.status_code)

    @app.exception_handler(RequestValidationError)
    async def error_de_formato(_: Request, __: RequestValidationError) -> JSONResponse:
        return JSONResponse({"detalle": MENSAJE_FORMATO}, status_code=422)

    @app.exception_handler(Exception)
    async def error_interno(_: Request, error: Exception) -> JSONResponse:
        registro.error("Error no controlado en la API", extra={"error": type(error).__name__})
        return JSONResponse({"detalle": MENSAJE_INTERNO}, status_code=500)

    for modulo in (chat, predios, escalamiento, admin, ovt_simulada):
        app.include_router(modulo.router)
    return app
