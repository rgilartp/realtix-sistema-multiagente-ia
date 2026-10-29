"""Lo que de verdad envía a LangSmith el cliente instalado, sin red (auditoría de seguridad).

Se interceptan las peticiones HTTP del cliente de `langsmith` (entradas, salidas y cualquier
adjunto de la carga multipart) y se buscan la imagen en base64 y un nombre declarado, inventados.
"""

import base64
import io
from typing import Any, TypedDict

import pytest
import requests
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tracers.langchain import LangChainTracer
from langgraph.graph import END, START, StateGraph
from langsmith import Client
from langsmith import utils as ls_utils
from PIL import Image

from src.integrations.robustez import con_tiempo_y_reintento
from src.integrations.trazas import (
    MASCARA_IMAGEN,
    MASCARA_NOMBRE,
    Anonimizador,
    AnonimizadorDeTrazas,
)

REQ = ("RNF-03 · Protección de datos personales", "RNF-05 · Registro auditable")
NOMBRE = "Ana Pérez"  # inventado
SIN_RED = "https://langsmith.invalid"


def _imagen_en_base64() -> str:
    salida = io.BytesIO()
    Image.new("RGB", (300, 300), "white").save(salida, "PNG")
    return base64.b64encode(salida.getvalue()).decode("ascii")


DATOS = _imagen_en_base64()
MENSAJE = HumanMessage(
    content=[
        {"type": "text", "text": f"Hola, me llamo {NOMBRE} y te envío mi recibo."},
        {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": DATOS}},
    ]
)


@pytest.fixture
def enviados(monkeypatch: pytest.MonkeyPatch) -> list[bytes]:
    """Los cuerpos de todas las peticiones HTTP; ninguna sale de la máquina."""
    cuerpos: list[bytes] = []

    def enviar(self: Any, request: requests.PreparedRequest, **_: Any) -> requests.Response:
        cuerpo = request.body or b""
        cuerpos.append(cuerpo.encode() if isinstance(cuerpo, str) else cuerpo)
        respuesta = requests.Response()
        respuesta.status_code, respuesta._content = 200, b"{}"
        respuesta.headers["Content-Type"] = "application/json"
        respuesta.url, respuesta.request = request.url or "", request
        return respuesta

    monkeypatch.setattr(requests.adapters.HTTPAdapter, "send", enviar)
    return cuerpos


def _cliente(anonimizador: Anonimizador) -> Client:
    return Client(
        api_url=SIN_RED, api_key="sin-clave", hide_inputs=anonimizador, hide_outputs=anonimizador
    )


def _modelo() -> GenericFakeChatModel:
    # Los modelos reciben el nombre declarado ya enmascarado (`para_modelos=True`): no lo repiten.
    return GenericFakeChatModel(messages=iter([AIMessage("Recibí tu recibo.")]))


def _contiene_nombre(carga: bytes) -> bool:
    return NOMBRE.encode() in carga  # la carga va en UTF-8 sin escapar (lo prueba la fila anterior)


@pytest.mark.unit
@pytest.mark.req(*REQ)
@pytest.mark.parametrize(("anonimizador", "se_filtra"), [(AnonimizadorDeTrazas(), False),
                                                         (Anonimizador(), True)])  # fmt: skip
def test_la_carga_de_langsmith_no_lleva_la_imagen_ni_el_nombre(
    enviados: list[bytes], anonimizador: Anonimizador, se_filtra: bool
) -> None:
    # Con el anonimizador anterior (la segunda fila), la imagen y el nombre sí llegaban: esa era la
    # causa de que las trazas del incidente de datos reales guardaran la imagen.
    cliente = _cliente(anonimizador)
    trazador = LangChainTracer(project_name="prueba", client=cliente)
    _modelo().invoke([MENSAJE], config={"callbacks": [trazador]})
    trazador.wait_for_futures()
    cliente.flush()
    carga = b"".join(enviados)
    assert b"multipart" in carga or b"inputs" in carga  # la ejecución sí se envió
    assert (DATOS[:200].encode() in carga) is se_filtra
    assert (f"me llamo {NOMBRE}".encode() in carga) is se_filtra
    if not se_filtra:
        assert MASCARA_IMAGEN.encode() in carga and MASCARA_NOMBRE.encode() in carga
        assert not _contiene_nombre(carga)


class Estado(TypedDict):
    texto: str


@pytest.mark.unit
@pytest.mark.req(*REQ)
def test_con_el_trazador_del_sistema_langchain_no_agrega_otro(
    enviados: list[bytes], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Aunque Compose pase LANGSMITH_* al contenedor, el grafo con el trazador anonimizado no suma
    el trazador por defecto de LangChain (sin anonimizador), tampoco en el hilo de
    `con_tiempo_y_reintento`."""
    entorno = {"LANGSMITH_TRACING": "true", "LANGCHAIN_TRACING_V2": "true",
               "LANGSMITH_API_KEY": "sin-clave", "LANGSMITH_ENDPOINT": SIN_RED}  # fmt: skip
    for variable, valor in entorno.items():
        monkeypatch.setenv(variable, valor)
    ls_utils.get_env_var.cache_clear()
    creados: list[LangChainTracer] = []
    iniciar = LangChainTracer.__init__

    def contar(self: LangChainTracer, *args: Any, **kwargs: Any) -> None:
        creados.append(self)
        iniciar(self, *args, **kwargs)

    monkeypatch.setattr(LangChainTracer, "__init__", contar)
    vistos: list[list[Any]] = []  # los manejadores con que corre el modelo, en el hilo

    class ModeloQueMira(GenericFakeChatModel):
        def _generate(self, messages: Any, stop: Any = None, run_manager: Any = None, **kw: Any):
            vistos.append(list(run_manager.handlers) if run_manager else [])
            return super()._generate(messages, stop=stop, run_manager=run_manager, **kw)

    modelo = ModeloQueMira(messages=iter([AIMessage("Recibí tu recibo.")]))

    def nodo(_: Estado) -> Estado:
        respuesta = con_tiempo_y_reintento(lambda: modelo.invoke([MENSAJE]), 10)
        return {"texto": str(respuesta.content)}

    grafo = StateGraph(Estado)
    grafo.add_node("nodo", nodo)
    grafo.add_edge(START, "nodo")
    grafo.add_edge("nodo", END)
    cliente = _cliente(AnonimizadorDeTrazas())
    trazador = LangChainTracer(project_name="prueba", client=cliente)
    try:
        grafo.compile().invoke({"texto": ""}, config={"callbacks": [trazador]})
        trazador.wait_for_futures()
        cliente.flush()
    finally:
        ls_utils.get_env_var.cache_clear()
    # LangChain copia el trazador del sistema para sumar metadatos (`copy_with_metadata_defaults`),
    # pero no crea uno propio: todos usan el cliente anonimizado. Sin el trazador del sistema, sí
    # crearía uno con el cliente por defecto, sin anonimizador (se comprobó a mano).
    assert creados[0] is trazador and all(t.client is cliente for t in creados)
    [manejadores] = vistos
    trazadores = [h for h in manejadores if isinstance(h, LangChainTracer)]
    assert len(trazadores) == 1 and trazadores[0].client is cliente
    carga = b"".join(enviados)
    assert MASCARA_IMAGEN.encode() in carga
    assert DATOS[:200].encode() not in carga and not _contiene_nombre(carga)
