"""Métricas de enrutamiento y de tiempo (RF-OBS-02 y RF-OBS-03) y tokens por nodo (sección 3.8)."""

from decimal import Decimal
from typing import TypedDict

import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage
from langgraph.graph import END, START, StateGraph

from src.agents.state import CATEGORIAS
from src.integrations.costos import UsoPorNodo
from src.services.metricas import SIN_CATEGORIA, calcular_metricas, percentil


@pytest.mark.unit
@pytest.mark.req(
    "RF-OBS-02 · Matriz de confusión de enrutamiento", "RF-OBS-03 · Métricas de precisión y tiempo"
)
def test_matriz_precision_exhaustividad_f1_y_tiempos() -> None:
    etiquetas = {"IPU-01": "ipu", "ICA-01": "ica", "HOR-01": None}
    interacciones = [
        {"escenario_id": "IPU-01", "categoria": "ipu", "duracion_ms": 100, "estado": "respondida"},
        {"escenario_id": "IPU-01", "categoria": "ica", "duracion_ms": 300, "estado": "respondida"},
        {"escenario_id": "ICA-01", "categoria": "ica", "duracion_ms": 200, "estado": "respondida"},
        {"escenario_id": "HOR-01", "categoria": None, "duracion_ms": 5,
         "estado": "fuera_de_horario"},  # sin categoría esperada: no entra en la matriz
        {"escenario_id": None, "categoria": "general", "duracion_ms": 50, "escalada": True},
    ]  # fmt: skip
    m = calcular_metricas(interacciones, etiquetas, CATEGORIAS)
    assert m["turnos"] == 5 and m["turnos_etiquetados"] == 3 and m["exactitud"] == 0.667
    assert m["matriz_de_confusion"]["ipu"] == {**dict.fromkeys([*CATEGORIAS, SIN_CATEGORIA], 0),
                                               "ipu": 1, "ica": 1}  # fmt: skip
    assert m["por_categoria"]["ipu"] == {"soporte": 2, "precision": 1.0, "exhaustividad": 0.5,
                                         "f1": 0.667}  # fmt: skip
    assert m["por_categoria"]["ica"]["precision"] == 0.5
    assert m["por_categoria"]["general"]["precision"] is None
    assert m["tiempos_ms"] == {"mediana": 100.0, "p95": 300.0, "maximo": 300.0}
    assert m["por_estado"]["fuera_de_horario"] == 1 and m["escaladas"] == 1
    assert percentil([], 95) is None and percentil([1.0, 2.0], 50) == 1.0


class _Estado(TypedDict, total=False):
    x: int


@pytest.mark.unit
@pytest.mark.req("RF-OBS-03 · Métricas de precisión y tiempo")
def test_tokens_y_modelo_por_nodo() -> None:
    respuesta = AIMessage(
        "hola",
        usage_metadata={"input_tokens": 120, "output_tokens": 30, "total_tokens": 150},
        response_metadata={"model_name": "claude-haiku-5-5"},
    )
    modelo = GenericFakeChatModel(messages=iter([respuesta]))

    def nodo_ipu(state: _Estado) -> _Estado:
        modelo.invoke("¿qué es el predial?")
        return {"x": 1}

    grafo = StateGraph(_Estado)
    grafo.add_node("nodo_ipu", nodo_ipu)
    grafo.add_edge(START, "nodo_ipu")
    grafo.add_edge("nodo_ipu", END)
    uso = UsoPorNodo()
    grafo.compile().invoke({"x": 0}, {"callbacks": [uso]})
    assert uso.totales() == {"entrada": 120, "salida": 30}
    assert uso.modelo_por_nodo() == {"nodo_ipu": "claude-haiku-5-5"}
    assert uso.costo_usd() == Decimal("0.000027")
