"""Métricas de las corridas (sección 6.5 y ADR-24) con datos de juguete y valores conocidos."""

import random

import pytest
from sklearn.metrics import cohen_kappa_score

from src.evaluacion.metricas_eval import (
    VEREDICTOS,
    bootstrap,
    consistencia,
    kappa,
    kappa_con_intervalo,
    latencias,
    pass_at_k,
    pass_hat_k,
    por_escenario,
    tasa_con_intervalos,
    wilson,
)

RNF16 = "RNF-16 · Tasa de respuestas correctas"
OBS05 = "RF-OBS-05 · Ejecución repetible de pruebas"


@pytest.mark.unit
@pytest.mark.req(RNF16)
@pytest.mark.parametrize(
    ("tasa", "n", "esperado"),
    [(0.5, 10, (0.2366, 0.7634)), (0.0, 10, (0.0, 0.2775)), (1.0, 60, (0.9398, 1.0))],
)
def test_wilson_con_valores_publicados(tasa, n, esperado) -> None:
    bajo, alto = wilson(tasa, n)
    assert bajo == pytest.approx(esperado[0], abs=1e-4)
    assert alto == pytest.approx(esperado[1], abs=1e-4)


@pytest.mark.unit
@pytest.mark.req(RNF16)
def test_wilson_usa_los_escenarios_y_no_los_ensayos() -> None:
    """A2: 60 escenarios con 3 ensayos cada uno dan un intervalo más ancho que 180 ensayos."""
    resultados = {f"E{i:02d}": [i % 7 != 0] * 3 for i in range(60)}
    t = tasa_con_intervalos(resultados)
    assert t["escenarios"] == 60 and t["ensayos"] == 180
    assert t["wilson95"] == pytest.approx(list(wilson(t["tasa"], 60)))
    ancho_60 = t["wilson95"][1] - t["wilson95"][0]
    bajo, alto = wilson(t["tasa"], 180)
    assert ancho_60 > alto - bajo


@pytest.mark.unit
@pytest.mark.req(RNF16, OBS05)
def test_bootstrap_repetible_y_alrededor_del_promedio() -> None:
    tasas = [1.0] * 50 + [0.0] * 10
    primero = bootstrap(tasas, lambda m: sum(m) / len(m))
    assert primero == bootstrap(tasas, lambda m: sum(m) / len(m))  # semilla fija
    assert primero[0] < 50 / 60 < primero[1]
    with pytest.raises(ValueError):
        bootstrap([], sum)


@pytest.mark.unit
@pytest.mark.req(RNF16)
def test_pass_at_k_y_pass_hat_k() -> None:
    assert pass_at_k(3, 1, 1) == pytest.approx(1 / 3)
    assert pass_at_k(3, 1, 3) == 1.0
    assert pass_at_k(3, 0, 3) == 0.0
    assert pass_hat_k(3, 3, 3) == 1.0
    assert pass_hat_k(3, 2, 3) == 0.0
    assert pass_hat_k(3, 2, 1) == pytest.approx(2 / 3)
    c = consistencia({"A": [True, True, True], "B": [True, False, False]})
    assert c == {"k": 3, "pass@1": pytest.approx(4 / 6), "pass@3": 1.0, "pass^3": 0.5}


@pytest.mark.unit
@pytest.mark.req(RNF16)
def test_kappa_binario_con_un_caso_resuelto_a_mano() -> None:
    # Acuerdo observado 0,75; esperado 0,5 * 0,25 + 0,5 * 0,75 = 0,5; kappa = 0,5.
    assert kappa(["si", "si", "no", "no"], ["si", "no", "no", "no"]) == pytest.approx(0.5)
    assert kappa(["a", "a"], ["a", "a"]) == 1.0


@pytest.mark.unit
@pytest.mark.req(RNF16)
def test_kappa_coincide_con_scikit_learn_binario_y_ponderado() -> None:
    azar = random.Random(7)
    a = [azar.choice(VEREDICTOS) for _ in range(40)]
    b = [x if azar.random() < 0.7 else azar.choice(VEREDICTOS) for x in a]
    assert kappa(a, b) == pytest.approx(cohen_kappa_score(a, b))
    esperado = cohen_kappa_score(
        [VEREDICTOS.index(x) for x in a], [VEREDICTOS.index(x) for x in b], weights="linear"
    )
    assert kappa(a, b, VEREDICTOS) == pytest.approx(esperado)
    con_ic = kappa_con_intervalo(a, b, VEREDICTOS)
    assert con_ic["n"] == 40 and con_ic["ic95"][0] <= con_ic["kappa"] <= con_ic["ic95"][1]


@pytest.mark.unit
@pytest.mark.req(RNF16)
def test_por_escenario_ordena_los_ensayos() -> None:
    ensayos = [
        {"escenario": "B", "ensayo": 2, "ok": False},
        {"escenario": "B", "ensayo": 1, "ok": True},
        {"escenario": "A", "ensayo": 1, "ok": True},
    ]
    assert por_escenario(ensayos, "ok") == {"A": [True], "B": [True, False]}


@pytest.mark.unit
@pytest.mark.req("RNF-01 · Tiempo de respuesta")
def test_latencias_separa_servidor_y_cliente() -> None:
    ensayos = [
        {
            "tipo_latencia": "simple",
            "turnos": [{"latencia_servidor_ms": 5000, "latencia_cliente_ms": 5200}],
        },
        {
            "tipo_latencia": "simple",
            "turnos": [{"latencia_servidor_ms": 9000, "latencia_cliente_ms": 9400}],
        },
        {
            "tipo_latencia": "rag",
            "turnos": [{"latencia_servidor_ms": 12000, "latencia_cliente_ms": 12100}],
        },
    ]
    lat = latencias(ensayos)
    assert lat["simple"]["servidor_p50_ms"] == 5000 and lat["simple"]["cliente_p95_ms"] == 9400
    assert lat["simple"]["cumplen_meta"] == 1 and lat["rag"]["cumplen_meta"] == 1
