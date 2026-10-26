"""Grafo de LangGraph: 8 nodos y 8 transiciones (Tablas 1 y 2 de arquitectura, ADR-14).

Las funciones de enrutamiento son puras (solo leen el estado) y se prueban una por una. Los nodos
se construyen con `Dependencias`; `nodos` permite sustituir cualquiera. Con `deps.modelos`, los
agentes son los reales de B7; sin él, los simulados de B4.
"""

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.agents.dependencias import Dependencias
from src.agents.nodes.confianza import crear_nodo_confianza
from src.agents.nodes.escalamiento import crear_nodo_escalamiento
from src.agents.nodes.general import crear_nodo_general
from src.agents.nodes.ica import crear_nodo_ica
from src.agents.nodes.ipu import crear_nodo_ipu
from src.agents.nodes.ocr import crear_nodo_ocr
from src.agents.nodes.orquestador import crear_nodo_orquestador
from src.agents.nodes.respuesta import crear_nodo_respuesta
from src.agents.state import AgentState

FABRICAS: dict[str, Callable[[Dependencias], Callable[[AgentState], dict[str, Any]]]] = {
    "nodo_orquestador": crear_nodo_orquestador,
    "nodo_ipu": crear_nodo_ipu,
    "nodo_ica": crear_nodo_ica,
    "nodo_general": crear_nodo_general,
    "nodo_ocr": crear_nodo_ocr,
    "nodo_confianza": crear_nodo_confianza,
    "nodo_escalamiento": crear_nodo_escalamiento,
    "nodo_respuesta": crear_nodo_respuesta,
}
DESTINOS_ORQUESTADOR = {
    "nodo_ipu": "nodo_ipu",
    "nodo_ica": "nodo_ica",
    "nodo_general": "nodo_general",
    "nodo_ocr": "nodo_ocr",
    "nodo_escalamiento": "nodo_escalamiento",
}
DESTINOS_CONFIANZA = {
    "nodo_orquestador": "nodo_orquestador",
    "nodo_respuesta": "nodo_respuesta",
    "nodo_escalamiento": "nodo_escalamiento",
}
POR_CATEGORIA = {
    "ipu": "nodo_ipu",
    "ica": "nodo_ica",
    "ocr": "nodo_ocr",
    "general": "nodo_general",
    "fuera_de_alcance": "nodo_general",  # lo no tributario se informa, no se escala
}


def ruta_orquestador(state: AgentState) -> str:
    """Escalamiento directo, aviso de sesión o pregunta por la IA (a `nodo_general`) o worker."""
    if state.get("requiere_escalamiento"):
        return "nodo_escalamiento"
    marcas = state.get("marcas", {})
    if marcas.get("sesion_requerida") or marcas.get("pregunta_ia"):
        return "nodo_general"
    categoria = state.get("categoria", "")
    if categoria not in POR_CATEGORIA:
        raise ValueError(f"Categoría desconocida: {categoria!r}")
    return POR_CATEGORIA[categoria]


def ruta_confianza(state: AgentState) -> str:
    """Escalar, volver al orquestador (reclasificar o categoría pendiente) o responder."""
    if state.get("requiere_escalamiento"):
        return "nodo_escalamiento"
    if state.get("marcas", {}).get("reclasificar") or state.get("categorias_pendientes"):
        return "nodo_orquestador"
    return "nodo_respuesta"


def construir_grafo(
    deps: Dependencias,
    checkpointer: BaseCheckpointSaver | None = None,
    nodos: dict[str, Callable[[AgentState], dict[str, Any]]] | None = None,
) -> CompiledStateGraph:
    """Compila el grafo. Sin `checkpointer`, usa memoria (las pruebas)."""
    constructor = StateGraph(AgentState)
    sustitutos = nodos or {}
    for nombre, fabrica in FABRICAS.items():
        constructor.add_node(nombre, sustitutos.get(nombre) or fabrica(deps))
    constructor.add_edge(START, "nodo_orquestador")
    constructor.add_conditional_edges("nodo_orquestador", ruta_orquestador, DESTINOS_ORQUESTADOR)
    for worker in ("nodo_ipu", "nodo_ica", "nodo_general", "nodo_ocr"):
        constructor.add_edge(worker, "nodo_confianza")
    constructor.add_conditional_edges("nodo_confianza", ruta_confianza, DESTINOS_CONFIANZA)
    constructor.add_edge("nodo_escalamiento", END)
    constructor.add_edge("nodo_respuesta", END)
    return constructor.compile(checkpointer=checkpointer or MemorySaver())


@contextmanager
def checkpointer_postgres(database_url: str) -> Iterator[BaseCheckpointSaver]:
    """Checkpointer en PostgreSQL (producción); crea sus tablas la primera vez."""
    from langgraph.checkpoint.postgres import PostgresSaver

    with PostgresSaver.from_conn_string(database_url) as saver:
        saver.setup()
        yield saver


def configuracion_de_hilo(id_conversacion: str, ahora: str | None = None) -> dict[str, Any]:
    """`thread_id` = id de la conversación, como pide la Tabla 3.

    `ahora` es el momento del turno como fecha ISO (el reloj simulado del modo de evaluación,
    ADR-16). Va como texto y no como objeto, para que el checkpointer de PostgreSQL no tenga que
    serializarlo; sin él, los agentes usan el reloj del sistema.
    """
    configurable: dict[str, Any] = {"thread_id": id_conversacion}
    if ahora is not None:
        configurable["ahora"] = ahora
    return {"configurable": configurable}
